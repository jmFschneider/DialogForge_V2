"""Le moteur : protocole d'appel durable en neuf étapes, transitions, reprise.

Prévol sans mutation, verrou, relecture sous verrou, `CALLING` publié **avant**
`Popen`, artefact de phase **avant** transition. À la reprise, **le dossier
d'appel fait foi, pas le seul statut** : un `resultat.json` valide prouve que les
flux sont complets, et le retraitement est local — jamais un appel repayé
(CONCEPTION_FINALE.md §5).

**Le programme, jamais l'agent, choisit la transition.** Une chaîne qui ressemble
à une commande, un patch ou une instruction d'outil reste du texte (§2).

**L'intervention humaine est appliquée ici, sous le verrou** — jamais par la CLI,
qui ne fait que la transmettre (§7, D-4). Une **porte d'état** décide ensuite si
le cycle peut continuer : sans elle, un second `run` en `WAITING_HUMAN` repartait
en appel payant, porte humaine contournée (C-01).

Les cinq éléments de contexte d'un cycle — dossier, configuration, adaptateurs,
versions sondées, délai — sont portés par `_Engine` plutôt que retraversés par
douze signatures. C'est le seul module du programme qui en ait autant.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import contracts, corpus, decisions, lock, objections, prompts, storage, transport
from .adapters.base import AgentAdapter, CallSpec, ObservedCli
from .contracts import ContractError, Finding
from .demande import complete as complete_demande
from .demande import record as record_provenance
from .models import (
    SCHEMA_VERSION,
    CallState,
    CallStatus,
    Configuration,
    Decision,
    IntegrityError,
    MissionKind,
    Phase,
    ReviewerAccess,
    Role,
    Severity,
    State,
    Status,
    positive_seconds,
)
from .transport import Outcome


class WorkflowError(RuntimeError):
    """Prévol refusé, intervention refusée, ou état modifié sous le verrou."""


@dataclass(frozen=True)
class Answer:
    """`resume --answer` : le fichier portant la réponse humaine, qui **complète**
    la demande — jamais ne la remplace."""

    path: Path


@dataclass(frozen=True)
class Correct:
    """`decide --correct` : une **correction ciblée** demandée par l'humain sur un
    résultat livré. Le fichier complète la demande, comme une réponse ; un tour
    supplémentaire s'ouvre ensuite, au-delà du plafond — explicite et tracé."""

    path: Path


@dataclass(frozen=True)
class Reprocess:
    """`resume --reprocess` : relire **localement** la réponse brute conservée d'un
    appel en erreur, sans rien relancer. Le fichier dit pourquoi, comme pour une
    relance : une opération humaine reste attribuable."""

    call_id: str
    reason_path: Path


@dataclass(frozen=True)
class RetryCall:
    """`resume --retry-call` : l'appel à relancer et le fichier de motif."""

    call_id: str
    reason_path: Path


Intervention = Answer | Correct | Reprocess | RetryCall


@dataclass(frozen=True)
class _Retry:
    """Relance validée sous verrou, portée jusqu'à `intention.json`."""

    call_id: str
    reason: str


_ROLE_OF_PHASE = {
    Phase.PROPOSAL_A: Role.A,
    Phase.REVIEW_B: Role.B,
    Phase.REVISION_A: Role.A,
}

# Une QUESTION née en PROPOSAL_A ou REVISION_A y retourne ; un BLOQUE (né en
# REVIEW_B) reprend en REVISION_A, avec le document courant et les constats
# déjà ouverts (§2).
_RESUME_PHASE = {Phase.REVIEW_B: Phase.REVISION_A}

# La porte d'état nomme la commande qui sort du statut refusé : un refus qui
# n'indique pas la suite renvoie l'humain au code source.
_WAY_OUT = {
    Status.WAITING_HUMAN: "resume --answer <fichier>",
    Status.INTERRUPTED: "resume --retry-call <uuid> --reason-file <fichier>",
    Status.ERROR: "resume --retry-call <uuid> --reason-file <fichier>",
    Status.AWAITING_APPROVAL: (
        "aucune, le cycle est allé à son terme ; décision humaine :"
        " decide --accept | --accept-with-reserves <texte> | --correct <fichier> | --stop"
    ),
    Status.STOPPED: "aucune, la collaboration a été arrêtée par décision humaine",
}

# Sortie de ERROR : **table fermée**, jamais héritée du statut (N-01). Toute
# autre famille d'erreur devra y être ajoutée explicitement.
_RELAUNCHABLE = frozenset({"CONTRACT_ERROR", "DECODE_FAILED"})

_NOT_APPROVED = (
    "> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est"
    " achevé, rien de plus.\n"
    "> Revue B : {access} · constats restés ouverts : {open} (dont {blocking}"
    " BLOCKING) · corpus {corpus}.\n"
    "> Version examinée par B (`{examined}`), livrée sans réécriture : {ending}."
    " Voir `bilan.md`.\n\n"
)


def run(
    collab: Path,
    *,
    adapters: Mapping[str, AgentAdapter],
    timeout_seconds: float,
    command_label: str = "run",
    intervention: Intervention | None = None,
    pause: Callable[[], bool] | None = None,
) -> State:
    """L'unique moteur synchrone. Il enchaîne les appels tant que l'état reste
    `READY` ; toute autre valeur rend la main à l'humain.

    **Pause à la frontière d'appel** : `pause()` n'est consultée qu'**entre** deux
    appels, une fois le précédent appliqué. Elle rend l'état `READY` tel quel — rien
    n'est perdu, `run` reprend au même endroit. Ce n'est pas l'arrêt immédiat, qui
    interrompt l'appel en cours (`INTERRUPTED_BY_USER`, possiblement payé).

    L'intervention humaine est appliquée **sous le verrou**, entre la relecture
    et la porte d'état, puis consommée — comme la relance l'était déjà, elle ne
    vaut que pour la première itération.

    La boucle est bornée par la machine à états elle-même — `max_revisions`
    plafonne les allers-retours et la promotion (`CLOSED`) est terminale. **Aucun compteur de
    garde n'est ajouté** : ce serait un quota interne.
    """
    # Surface appelée directement — par les tests, et par quiconque importe le
    # moteur : le délai y est validé avant toute publication de `CALLING`.
    timeout_seconds = positive_seconds(timeout_seconds)
    while True:
        engine, state = _preflight(collab, adapters, timeout_seconds, intervention)
        with lock.acquire(collab / "verrou.json", command_label):      # étape 2
            engine.recheck(state)                                      # étape 3
            # Avant l'intervention, donc **avant toute mutation** : un corpus qui
            # a bougé invalide la collaboration entière (§3), et le refus doit
            # tomber pendant que le code de sortie 1 dit encore la vérité.
            engine.check_corpus()
            state, retry = engine.intervene(state, intervention)
            engine.gate(state)
            if state.current_call is not None:
                state = engine.resume_call(state)
            else:
                state = engine.new_call(state, retry)
        intervention = None
        if state.status is not Status.READY:
            return state
        if pause is not None and pause():
            return state


def _preflight(
    collab: Path,
    adapters: Mapping[str, AgentAdapter],
    timeout_seconds: float,
    intervention: Intervention | None = None,
) -> tuple[_Engine, State]:
    """Étape 1, **sans aucune mutation** : demande, schémas, état, empreintes,
    adaptateurs, versions observées, modèles, profil de revue. Un adaptateur
    incapable du profil demandé est refusé **avant l'appel** (§1, §8). Le corpus,
    lui, se vérifie sous verrou, immédiatement avant l'appel (§3)."""
    config = Configuration.from_dict(_read_json(collab / "configuration.json"))
    state = State.from_dict(_read_json(collab / "etat.json"))
    answer = _read_answer(intervention)
    text, composed = _check_demande(collab, state, answer, "au prévol")
    observed: dict[str, ObservedCli] = {}
    for role, agent in ((Role.A, config.agent_a), (Role.B, config.agent_b)):
        adapter = adapters.get(agent.adapter_id)
        if adapter is None:
            raise WorkflowError(f"adaptateur inconnu : {agent.adapter_id!r}")
        seen = adapter.probe()
        if not seen.present:
            raise WorkflowError(f"{agent.adapter_id} : CLI absente")
        if agent.model != adapter.default_model(role) and (
            not adapter.capabilities.supports_model_override
        ):
            raise WorkflowError(f"{agent.adapter_id} : modèle non remplaçable")
        observed[agent.adapter_id] = seen
    if config.reviewer_access is ReviewerAccess.CONTEXT_ONLY and (
        not adapters[config.agent_b.adapter_id].capabilities.supports_context_only
    ):
        raise WorkflowError(f"{config.agent_b.adapter_id} : profil CONTEXT_ONLY non supporté")
    source = (
        str(intervention.path.resolve()) if isinstance(intervention, Answer | Correct) else None
    )
    return _Engine(
        collab, config, adapters, observed, text, timeout_seconds, answer, source, composed
    ), state


def _read_answer(intervention: Intervention | None) -> contracts.Normalized | None:
    """La réponse est lue **une fois**, au prévol : le moteur construit ses
    prompts avec elle, et la relecture sous verrou en tolère l'empreinte."""
    if not isinstance(intervention, Answer | Correct):
        return None
    text, _ = storage.read_text(intervention.path)
    return contracts.normalize(text)


def _check_demande(
    collab: Path, state: State, answer: contracts.Normalized | None, where: str
) -> tuple[str, contracts.Normalized | None]:
    """`demande.md` porte l'empreinte de l'état — ou, quand une réponse est
    fournie, celle de la demande **complétée** par cette réponse. Ce second cas
    est l'intervention interrompue entre l'écriture de la demande et la
    publication de l'état : la reprise doit pouvoir l'achever, et non la refuser
    ici avant d'avoir pu réparer.

    La demande complétée se recalcule depuis la version que l'état désigne : le
    `demande.md` courant, ou — s'il est déjà complété — son archive. `complete`
    étant déterministe, c'est le même texte, donc la même empreinte, à chaque rejeu.

    Rend le texte **en vigueur** pour les prompts, et la demande complétée.
    """
    path = collab / "demande.md"
    text, _ = storage.read_text(path)
    current = contracts.normalize(text)
    accepted = {state.demande_sha256}
    composed: contracts.Normalized | None = None
    if answer is not None:
        base = current.text if current.sha256 == state.demande_sha256 else _archived_text(
            path, state.demande_sha256
        )
        if base is not None:
            composed = contracts.normalize(complete_demande(base, answer.text))
            accepted.add(composed.sha256)
    if current.sha256 not in accepted:
        raise WorkflowError(f"demande.md ne correspond plus à l'empreinte de l'état ({where})")
    return (text if composed is None else composed.text), composed


@dataclass(frozen=True)
class _Engine:
    collab: Path
    config: Configuration
    adapters: Mapping[str, AgentAdapter]
    observed: dict[str, ObservedCli]
    demande: str
    timeout_seconds: float
    answer: contracts.Normalized | None = None
    answer_source: str | None = None
    composed: contracts.Normalized | None = None

    # -- Prévol et relecture sous verrou --

    def check_corpus(self) -> None:
        """Le corpus est figé : il n'existe pas de rafraîchissement. Le changer
        en cours de cycle détruirait la référence commune de A et B (§3).

        Contrôle **complet et unique**, sous verrou, immédiatement avant la
        construction de l'appel : le manifeste contre la configuration, puis
        chaque entrée — présence, taille, empreinte —, puis l'absence de fichier
        surnuméraire. Comparer la seule empreinte du **texte** du manifeste ne
        disait rien du contenu qu'il décrit.

        La promesse exacte est « contenu vérifié contre le manifeste **avant
        chaque appel** », et non une immutabilité physique : un éditeur qui
        ignore `verrou.json` pendant que l'agent lit reste hors de portée du
        programme.
        """
        if self.config.corpus_manifest_sha256 is None:
            if self.config.mission_kind is MissionKind.RECHERCHE:
                raise WorkflowError("mission de recherche sans corpus")
            return
        root = self.collab / "corpus"
        text, _ = storage.read_text(root / "manifeste.json")
        if contracts.normalize(text).sha256 != self.config.corpus_manifest_sha256:
            raise WorkflowError("le manifeste de corpus ne correspond plus à la configuration")
        try:
            manifest = corpus.read_manifest(root / "manifeste.json")
        except corpus.CorpusError as exc:
            raise WorkflowError(f"corpus : {exc}") from exc
        files_dir = root / "fichiers"
        for entry in manifest.entries:
            _check_corpus_file(files_dir / entry.logical_path, entry)
        _refuse_extra_files(files_dir, {e.logical_path for e in manifest.entries})

    def recheck(self, state: State) -> None:
        """Étape 3 : toute différence depuis le prévol est un refus. Ferme la
        fenêtre de concurrence sans passer les sondages coûteux sous verrou."""
        if _read_json(self.collab / "etat.json") != state.to_dict():
            raise WorkflowError("l'état a changé entre le prévol et le verrou")
        _check_demande(self.collab, state, self.answer, "entre le prévol et le verrou")

    # -- Intervention humaine, puis porte d'état : sous verrou, dans cet ordre --

    def intervene(
        self, state: State, intervention: Intervention | None
    ) -> tuple[State, _Retry | None]:
        """`cli.py` ne mute plus rien : l'intervention arrive ici et s'applique
        **sous le verrou**, avant la porte d'état (D-4)."""
        if isinstance(intervention, Answer):
            return self.apply_answer(state), None
        if isinstance(intervention, Correct):
            return self.apply_correction(state), None
        if isinstance(intervention, Reprocess):
            return self.apply_reprocess(state, intervention), None
        if isinstance(intervention, RetryCall):
            return self.apply_retry(state, intervention)
        return state, None

    def apply_answer(self, state: State) -> State:
        """La réponse **complète** la demande : archive de l'ancienne **par copie**,
        écriture de la nouvelle version complète, provenance, publication de
        l'état — dans cet ordre, si bien que `demande.md` n'est jamais absent,
        fût-ce une seconde, et reste l'unique autorité.

        Rien de ce qui figurait dans la demande ne disparaît : `complete` garde
        le texte existant en préfixe. Un remplacement intégral n'est **pas** une
        réponse ; s'il devient nécessaire, ce sera une commande explicite et
        distincte.

        Un arrêt après l'archive laisse la demande d'origine : le rejeu
        réarchive un texte déjà archivé, donc ne réarchive pas. Un arrêt après
        l'écriture laisse l'unique cas particulier reconnu — l'état dit encore
        `WAITING_HUMAN` avec l'ancienne empreinte alors que `demande.md` porte
        déjà celle de la demande complétée : il reste à consigner (une seule
        fois) et à publier l'état.
        """
        assert self.answer is not None and self.composed is not None  # prévol
        if state.status is not Status.WAITING_HUMAN:
            raise WorkflowError(
                f"statut {state.status.value} : la collaboration n'attend pas de réponse humaine"
            )
        self.write_complement()
        self.record_answer(state, "reponse")
        return self.publish(replace(
            state, status=Status.READY, phase=_RESUME_PHASE.get(state.phase, state.phase),
            demande_sha256=self.composed.sha256,
        ))

    def write_complement(self) -> None:
        """Archive par copie l'ancienne demande, puis écrit la demande complétée —
        et **ne fait rien** si `demande.md` la porte déjà (rejeu)."""
        assert self.composed is not None
        path = self.collab / "demande.md"
        current, _ = storage.read_text(path)
        if contracts.normalize(current).sha256 != self.composed.sha256:
            _archive(path, current)
            storage.write_atomic_text(path, self.composed.text)

    def apply_correction(self, state: State) -> State:
        """Correction ciblée demandée par l'humain sur un résultat **livré**.

        Même ordre que `apply_answer` — archive, demande complétée, provenance —,
        puis la **décision** consignée, puis l'état : un tour de révision de plus,
        au-delà du plafond, ouvert par une décision qui le dit et le date. Chaque
        écriture est rejouable : un arrêt brutal, puis la même commande, achève.
        """
        assert self.answer is not None and self.composed is not None  # prévol
        if state.status is not Status.AWAITING_APPROVAL:
            raise WorkflowError(
                f"statut {state.status.value} : une correction ciblée se demande sur un résultat"
                " livré (AWAITING_APPROVAL)"
            )
        self.write_complement()
        self.record_answer(state, "correction")
        decisions.record(
            self.collab, decisions.TARGETED_CORRECTION, state,
            instruction_sha256=self.answer.sha256, extra_round=state.revision + 1,
        )
        return self.publish(replace(
            state, status=Status.READY, phase=Phase.REVISION_A, revision=state.revision + 1,
            demande_sha256=self.composed.sha256,
        ))

    def record_answer(self, state: State, source: str) -> None:
        """Consigne d'où vient le complément, quelle version il prolonge et à
        quelle revue elle répondait — **après** `demande.md`, **avant** l'état,
        donc rejouable (`demande.record` ne réécrit pas une empreinte déjà
        consignée).

        L'archive est retrouvée par son empreinte, pas par son rang : au rejeu,
        c'est la seule façon de désigner celle de la version **prolongée**, et
        non une plus ancienne.
        """
        assert self.answer is not None and self.composed is not None
        record_provenance(self.collab, {
            "source": source, "path": self.answer_source, "sha256": self.composed.sha256,
            "complement_sha256": self.answer.sha256, "replaces": state.demande_sha256,
            "archive": _archive_of(self.collab / "demande.md", state.demande_sha256),
            "phase": state.phase.value, "revision": state.revision,
            "latest_review": state.latest_review,
        })

    def apply_retry(self, state: State, request: RetryCall) -> tuple[State, _Retry]:
        """Valide la relance et rend l'état remis en phase **en mémoire**.

        Rien n'est publié avant `intention.json` : un arrêt ici laisse
        l'incident d'origine intact, et la même commande reste rejouable à
        l'identique. Le lien vers l'appel relancé n'est ainsi jamais perdable.
        """
        call = state.current_call
        if call is None or call.call_id != request.call_id:
            raise WorkflowError(f"aucun appel courant {request.call_id!r} à relancer")
        if not self.relaunchable(state, call):
            raise WorkflowError(f"statut {state.status.value} : aucun appel relançable")
        reason, _ = storage.read_text(request.reason_path)
        if not reason.strip():
            raise WorkflowError("le motif de relance ne peut pas être vide")
        return (
            replace(state, status=Status.READY, current_call=None),
            _Retry(call.call_id, reason.strip()),
        )

    def apply_reprocess(self, state: State, request: Reprocess) -> State:
        """Retraitement **local** d'une réponse reçue mais mal interprétée : la
        réponse brute est déjà sur disque et payée, en relire l'interprétation ne
        coûte rien — alors que `--retry-call` repaierait un appel pour la même
        réponse. Même table fermée que la relance (N-01) : seuls `CONTRACT_ERROR`
        et `DECODE_FAILED`, des erreurs **d'interprétation**.

        Rien n'est réécrit : les données brutes restent intactes, l'opération est
        **tracée** (`retraitements.jsonl`, dans le dossier de l'appel), puis l'état
        repasse en `RUNNING` avec son appel courant — le chemin de reprise
        ordinaire, qui confronte le dossier aux empreintes avant de relire. Un
        arrêt brutal ensuite se reprend par un simple `run`.
        """
        call = state.current_call
        if state.status is not Status.ERROR or call is None or call.call_id != request.call_id:
            raise WorkflowError(f"aucun appel en erreur {request.call_id!r} à retraiter")
        if not self.relaunchable(state, call):
            raise WorkflowError(
                "cet incident n'est pas une erreur d'interprétation : un retraitement local"
                " ne changerait rien (voir `status`)"
            )
        reason, _ = storage.read_text(request.reason_path)
        if not reason.strip():
            raise WorkflowError("le motif du retraitement ne peut pas être vide")
        incident = _read_json(self.collab / str(state.last_incident))
        trace = self.collab / call.call_dir / "retraitements.jsonl"
        previous = storage.read_text(trace)[0] if trace.exists() else ""
        entry = {
            "at": _now(), "reason": reason.strip(), "incident": incident.get("kind"),
            "detail": incident.get("detail"),
        }
        storage.write_atomic_text(
            trace, previous + json.dumps(entry, ensure_ascii=False) + "\n"
        )
        return self.publish(replace(state, status=Status.RUNNING))

    def relaunchable(self, state: State, call: CallState) -> bool:
        """`INTERRUPTED` se relance ; `ERROR` ne sort que par la **table fermée**
        des incidents relançables, et seulement pour son propre appel (N-01)."""
        if state.status is Status.INTERRUPTED:
            return True
        if state.status is not Status.ERROR or state.last_incident is None:
            return False
        if not state.last_incident.startswith(f"{call.call_dir}/"):
            return False
        incident = _read_json(self.collab / state.last_incident)
        return isinstance(incident, dict) and incident.get("kind") in _RELAUNCHABLE

    def gate(self, state: State) -> None:
        """Porte d'état, **après l'intervention** : seuls `READY` sans appel
        courant et `RUNNING` avec appel courant entrent dans le cycle. Le statut
        est lu, jamais déduit de la seule présence de `current_call` (C-01)."""
        if state.status is Status.READY and state.current_call is None:
            return
        if state.status is Status.RUNNING and state.current_call is not None:
            return
        raise WorkflowError(
            f"statut {state.status.value} : le cycle ne repart pas d'ici ; sortie :"
            f" {_WAY_OUT.get(state.status, 'corriger etat.json à la main')}"
        )

    # -- Étapes 4 à 7 : un appel --

    def new_call(self, state: State, retry: _Retry | None) -> State:
        role = _ROLE_OF_PHASE.get(state.phase)
        if role is None:
            raise WorkflowError(f"phase {state.phase.value} : aucun appel n'y est prévu")
        agent = self.config.agent_a if role is Role.A else self.config.agent_b
        sequence, call_id = self.next_sequence(), uuid.uuid4().hex
        rel_dir = f"appels/{sequence:04d}-{role.value}-{call_id}"
        prompt = self.build_prompt(state)
        digest = contracts.normalize(prompt).sha256
        spec = CallSpec(
            prompt=prompt, model=agent.model, timeout_seconds=self.timeout_seconds,
            work_root=self.collab,
            reviewer_access=self.config.reviewer_access if role is Role.B else None,
        )
        # `command()` est résolu avant **le premier octet écrit** : un exécutable
        # disparu entre le prévol et l'appel est alors un refus qui ne laisse
        # rien derrière lui, et non un faux « possiblement payé » sur un appel
        # jamais parti. Résoudre après le `mkdir` laissait un dossier d'appel et
        # un `prompt.txt` orphelins.
        argv = self.adapters[agent.adapter_id].command(spec)
        (self.collab / rel_dir).mkdir(parents=True)
        storage.write_atomic_text(self.collab / rel_dir / "prompt.txt", prompt)
        _write_json(self.collab / rel_dir / "intention.json", {
            "schema_version": SCHEMA_VERSION, "call_id": call_id, "sequence": sequence,
            "role": role.value, "phase": state.phase.value,
            "adapter_id": agent.adapter_id, "model": agent.model,
            "observed_version": self.observed[agent.adapter_id].version,
            "reviewer_access": self.config.reviewer_access.value, "prompt_sha256": digest,
            # Trace de l'**argv demandé**, `argv[0]` retiré : jamais une preuve
            # des capacités effectives — la configuration utilisateur, les
            # hooks et l'évolution de la CLI restent hors de portée. Sans
            # `argv[0]`, la règle « aucun chemin absolu persisté » n'a pas à
            # être rouverte, et aucun futur adaptateur ne peut y déposer un
            # secret (D-6b).
            "invocation_args": list(argv[1:]),
            "retries": None if retry is None else retry.call_id,
            "retry_reason": None if retry is None else retry.reason, "created_at": _now(),
        })
        call = CallState(
            call_id=call_id, sequence=sequence, role=role, phase=state.phase,
            status=CallStatus.CALLING, call_dir=rel_dir, prompt_sha256=digest,
            response_sha256=None, started_at=_now(), completed_at=None,
        )
        # Étape 4 : CALLING publié AVANT Popen. Un crash ici est déjà interprétable.
        state = self.publish(replace(state, status=Status.RUNNING, current_call=call))
        # Le prompt passe par stdin, jamais par la ligne de commande : mesuré le
        # 2026-09-03, argv plafonne à 32 767 caractères sous Windows, et une CLI
        # qui voit `DEVNULL` sur son entrée la lit comme un flux vide et dégrade
        # sa réponse (`conception/CARACTERISATION_CLI.md`, point 1).
        try:
            result = transport.run(
                argv, cwd=self.collab, call_dir=self.collab / rel_dir,
                timeout_seconds=self.timeout_seconds, stdin_text=prompt,
            )
        except transport.TransportError as exc:
            # `Popen` a échoué : l'appel **n'est pas parti**. Le déclarer
            # « possiblement payé » ferait payer au lancement suivant une
            # prudence que rien ne justifie.
            return self.incident(
                state, rel_dir, "LAUNCH_FAILED", Status.INTERRUPTED, str(exc)
            )
        if result.outcome is not Outcome.COMPLETED:
            return self.incident(state, rel_dir, result.outcome.value, Status.INTERRUPTED)
        if result.return_code != 0:
            # D-2 : capacité commune aux deux outils — quota épuisé et modèle
            # invalide rendent tous deux 1. Sans ce test, un message de quota
            # sorti sur stdout serait pris pour une réponse et finirait en
            # CONTRACT_ERROR (CONCEPTION_FINALE.md §5).
            return self.incident(
                state, rel_dir, "CLI_FAILED", Status.INTERRUPTED,
                f"code de retour {result.return_code}",
            )
        return self.store_response(state)

    def store_response(self, state: State) -> State:
        """Étape 7 : extraction de la réponse, publication de `RESPONSE_STORED`."""
        call = _current(state)
        agent = self.config.agent_a if call.role is Role.A else self.config.agent_b
        call_dir = self.collab / call.call_dir
        try:
            raw = self.adapters[agent.adapter_id].extract(
                (call_dir / "stdout.txt").read_bytes(), (call_dir / "stderr.txt").read_bytes()
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            # Les flux sont complets mais illisibles : les préserver et nommer
            # l'incident, plutôt qu'une traceback qui laisserait au lancement
            # suivant un faux « possiblement payé ». Aucun appel n'est
            # nécessaire pour retenter l'extraction (N-01).
            return self.incident(
                state, call.call_dir, "DECODE_FAILED", Status.ERROR, str(exc)
            )
        storage.write_atomic_text(call_dir / "reponse_brute.txt", raw)
        normalized = contracts.normalize(raw)
        state = self.publish(replace(state, current_call=replace(
            call, status=CallStatus.RESPONSE_STORED,
            response_sha256=normalized.sha256, completed_at=_now(),
        )))
        return self.apply(state, normalized.text)

    def resume_call(self, state: State) -> State:
        """Table de reprise §5 — le dossier d'appel fait foi, pas le seul statut.

        Le dossier est **confronté aux empreintes de l'état avant toute
        branche**, `RESPONSE_STORED` comprise : sans cela, le moteur reprenait
        sur des fichiers que rien ne rattachait à l'appel qu'il croyait
        reprendre. Une preuve **contredite** n'est pas une preuve **absente**,
        et elle ne se rattrape pas par un appel (C-05).
        """
        call = _current(state)
        call_dir = self.collab / call.call_dir
        try:
            return self.resume_verified(state, call, call_dir)
        except IntegrityError as exc:
            return self.incident(
                state, call.call_dir, "INTEGRITY_MISMATCH", Status.INTERRUPTED, str(exc)
            )

    def resume_verified(self, state: State, call: CallState, call_dir: Path) -> State:
        self.check_digest(
            call_dir / "prompt.txt", call.prompt_sha256, "l'empreinte de l'appel"
        )
        # Avant **toute** branche, `RESPONSE_STORED` comprise : la valeur de
        # retour ne sert pas ici, seule compte l'`IntegrityError` qu'un flux
        # contredisant `resultat.json` déclenche. Sans cet appel, cette branche
        # contournait la garantie d'intégrité que §5 annonce comme commune.
        transport.read_result(call_dir)
        if call.status is CallStatus.RESPONSE_STORED:
            raw = self.check_digest(
                call_dir / "reponse_brute.txt", call.response_sha256, "la reponse enregistree"
            )
            return self.apply(state, raw)
        result = transport.read_result(call_dir)
        if result is None:
            return self.incident(
                state, call.call_dir, "CALL_POSSIBLY_PAID", Status.INTERRUPTED,
                "appel possiblement parti, possiblement paye - aucun rejeu automatique",
            )
        if result.return_code != 0:
            return self.incident(
                state, call.call_dir, "CLI_FAILED", Status.INTERRUPTED,
                f"code de retour {result.return_code}",
            )
        # `resultat.json` valide : les flux sont complets. Retraitement local,
        # sans appel — sans quoi on repaierait une réponse qu'on a déjà.
        return self.store_response(state)

    def check_digest(self, path: Path, expected: str | None, what: str) -> str:
        """Relit un artefact d'appel et le confronte à l'empreinte de l'état.

        L'empreinte porte sur le texte **normalisé**, comme au moment de
        l'écriture : c'est la copie normalisée qui est empreinte, jamais la
        preuve brute (§6). Rend ce texte normalisé, prêt à l'emploi.
        """
        try:
            text, _ = storage.read_text(path)
        except OSError as exc:
            raise IntegrityError(f"{path.name} absent du dossier d'appel") from exc
        normalized = contracts.normalize(text)
        if normalized.sha256 != expected:
            raise IntegrityError(f"{path.name} ne correspond plus a {what}")
        return normalized.text

    # -- Étape 8 : artefact de phase, puis transition --

    def apply(self, state: State, text: str) -> State:
        call = _current(state)
        try:
            if call.role is Role.A:
                return self.apply_a(state, call, text)
            return self.apply_b(state, call, text)
        except ContractError as exc:
            # La réponse brute est déjà préservée : jamais de défaut permissif (§6).
            return self.incident(state, call.call_dir, "CONTRACT_ERROR", Status.ERROR, str(exc))

    def apply_a(self, state: State, call: CallState, text: str) -> State:
        response = contracts.parse_agent_response(text)
        if response.kind == "QUESTION":
            self.write_exchange(call.sequence, "question-A.md", response.body)
            return self.publish(
                replace(state, status=Status.WAITING_HUMAN, current_call=None)
            )
        body = response.body
        if state.phase is Phase.REVISION_A:
            # Une réponse par objection ouverte, **avant** toute écriture : un
            # bloc absent ou incomplet est un échec de contrat, la réponse brute
            # restant dans `appels/`. Le document, lui, reste du texte libre.
            body, block = contracts.split_responses(body)
            responses = contracts.parse_objection_responses(block, state.open_finding_ids)
            self.write_exchange(
                call.sequence, "reponses-A.json", _json_text(contracts.responses_to_dict(responses))
            )
        name = (
            "proposition-A.md" if state.phase is Phase.PROPOSAL_A
            else f"revision-{state.revision}-A.md"
        )
        return self.publish(replace(
            state, status=Status.READY, phase=Phase.REVIEW_B, current_call=None,
            current_document=self.write_exchange(call.sequence, name, body),
        ))

    def apply_b(self, state: State, call: CallState, text: str) -> State:
        review = contracts.parse_review(
            text, state.open_finding_ids,
            {f.id: f.statement for f in self.open_findings(state)},
        )
        # La **forme canonique**, pas le texte de B : c'est ce fichier que le
        # programme relit comme registre des constats, et un bloc clôturé ou une
        # `severity` omise le rendaient illisible par `json.loads`. La preuve
        # exacte reste `reponse_brute.txt` (D-8).
        canonical = _json_text(review.to_dict())
        state = replace(
            state, current_call=None,
            latest_review=self.write_exchange(call.sequence, "critique-B.json", canonical),
            open_finding_ids=contracts.open_finding_ids(review),
        )
        if review.decision is Decision.BLOQUE:
            return self.publish(replace(state, status=Status.WAITING_HUMAN))
        if review.decision is Decision.ACCEPTER:
            if contracts.has_open_blocking(review):
                # La décision de B est conservée telle quelle : le programme ne
                # juge pas sur les sévérités, pas même pour refuser (§6).
                return self.incident(
                    state, call.call_dir, "ACCEPTER_WITH_OPEN_BLOCKING",
                    Status.WAITING_HUMAN, "revue conservee ; incoherence rendue a l'humain",
                )
            return self.promote(state, capped=False)
        if state.revision >= self.config.max_revisions:
            return self.promote(state, capped=True)
        return self.publish(replace(
            state, status=Status.READY, phase=Phase.REVISION_A, revision=state.revision + 1
        ))

    # -- Prompts et artefacts --

    def build_prompt(self, state: State) -> str:
        date = self.corpus_date()
        if state.phase is Phase.PROPOSAL_A:
            return prompts.build_proposal(self.demande, self.config.mission_kind, date)
        document = self.read_relative(state.current_document)
        if state.current_document == decisions.DELIVERED:
            # Après une correction ciblée, A repart du livrable : son **corps**, sans
            # la ligne d'en-tête que le programme y a écrite (elle n'est pas le texte).
            document = _promoted_body(document)
        if state.phase is Phase.REVIEW_B:
            replies = self.replies_to(state)
            prior = "\n".join(
                _prior_line(f, replies.get(f.id)) for f in self.open_findings(state)
            ) or "Aucun."
            # Relecture **ciblée** dès qu'une correction a eu lieu (1.3).
            return prompts.build_review(
                self.demande, document, prior, self.config.reviewer_access, date,
                targeted=state.revision >= 1,
            )
        review = self.read_relative(state.latest_review)
        return prompts.build_revision(
            self.demande, document, review, self.config.mission_kind, date
        )

    def replies_to(self, state: State) -> dict[str, contracts.ObjectionResponse]:
        """Les réponses de A à la revue précédente, par identifiant — vides pour
        la première revue. Le fichier partage le numéro d'appel du document :
        `0003-revision-1-A.md` a pour réponses `0003-reponses-A.json`."""
        assert state.current_document is not None
        document = Path(state.current_document)
        path = self.collab / document.parent / f"{document.name[:4]}-reponses-A.json"
        if not path.exists():
            return {}
        text, _ = storage.read_text(path)
        return {r.id: r for r in contracts.responses_from_dict(json.loads(text))}

    def open_findings(self, state: State) -> list[Finding]:
        """Le registre unique fait foi : les constats ouverts se relisent dans la
        dernière revue, jamais dans une seconde vérité (§6)."""
        if state.latest_review is None:
            return []
        open_ids = set(state.open_finding_ids)
        review = contracts.parse_review(self.read_relative(state.latest_review))
        return [f for f in review.findings if f.id in open_ids]

    def promote(self, state: State, *, capped: bool) -> State:
        """Le cycle s'achève par la **promotion de la version que B vient
        d'examiner** — jamais par une réécriture que personne n'aurait relue.

        `current_document` est ce document : la revue qui vient d'être publiée
        porte sur lui, et A n'a plus d'appel après B. Le livrable en reprend le
        corps octet pour octet ; le bilan, écrit par le programme, dit ce qui
        reste en désaccord. La ligne d'en-tête est vraie à tout moment : le cycle
        s'achève en `AWAITING_APPROVAL`, jamais en « succès » (§2).

        Deux écritures puis l'état : un arrêt entre elles laisse un livrable sans
        état, et le rejeu de la reprise relit la même revue — mêmes octets.
        """
        assert state.current_document is not None and state.latest_review is not None
        examined = state.current_document
        findings = self.open_findings(state)
        date = self.corpus_date()
        header = _NOT_APPROVED.format(
            access=self.config.reviewer_access.value, open=len(findings),
            blocking=sum(1 for f in findings if f.severity is Severity.BLOCKING),
            corpus="absent" if date is None else f"figé le {date}",
            ending=(
                f"plafond de {self.config.max_revisions} révision(s) atteint" if capped
                else "acceptée par B"
            ),
            examined=examined,
        )
        (self.collab / "livrables").mkdir(exist_ok=True)
        delivered = "livrables/version_finale.md"
        storage.write_atomic_text(
            self.collab / delivered, header + self.read_relative(examined)
        )
        storage.write_atomic_text(
            self.collab / "livrables" / "bilan.md",
            objections.bilan(
                self.collab, delivered=delivered, examined=examined,
                review=state.latest_review, revisions=state.revision,
                max_revisions=self.config.max_revisions, capped=capped,
                corrections=decisions.corrections(self.collab),
            ),
        )
        return self.publish(replace(
            state, status=Status.AWAITING_APPROVAL, phase=Phase.CLOSED,
            current_document=delivered, current_call=None,
        ))

    def write_exchange(self, sequence: int, name: str, body: str) -> str:
        (self.collab / "echanges").mkdir(exist_ok=True)
        path = f"echanges/{sequence:04d}-{name}"
        storage.write_atomic_text(self.collab / path, body)
        return path

    def incident(
        self, state: State, rel_dir: str, kind: str, status: Status, detail: str = ""
    ) -> State:
        """Aucun rejeu automatique : la suite passe par `resume --retry-call`,
        qui exige un motif humain attribuable (§5)."""
        _write_json(self.collab / rel_dir / "incident.json", {
            "schema_version": SCHEMA_VERSION, "kind": kind, "detail": detail, "at": _now(),
        })
        return self.publish(
            replace(state, status=status, last_incident=f"{rel_dir}/incident.json")
        )

    # -- Chemins et publication --

    def corpus_date(self) -> str | None:
        if self.config.corpus_manifest_sha256 is None:
            return None
        manifest = _read_json(self.collab / "corpus" / "manifeste.json")
        return str(manifest["captured_at"])[:10]

    def next_sequence(self) -> int:
        calls = self.collab / "appels"
        if not calls.is_dir():
            return 1
        used = [
            int(p.name[:4]) for p in calls.iterdir() if p.is_dir() and p.name[:4].isdigit()
        ]
        return max(used, default=0) + 1

    def read_relative(self, relative: str | None) -> str:
        if relative is None:
            raise WorkflowError("l'état ne désigne aucun artefact pour cette phase")
        text, _ = storage.read_text(self.collab / relative)
        return text

    def publish(self, state: State) -> State:
        state = replace(state, updated_at=_now())
        _write_json(self.collab / "etat.json", state.to_dict())
        return state


def _check_corpus_file(path: Path, entry: corpus.ManifestEntry) -> None:
    """Le lien symbolique est refusé **par symétrie avec la copie**, qui refuse
    déjà les fichiers non réguliers : ce qui n'a pas pu entrer dans le corpus ne
    doit pas pouvoir y apparaître après coup."""
    if path.is_symlink():
        raise WorkflowError(f"corpus : {entry.logical_path} est devenu un lien symbolique")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise WorkflowError(f"corpus : {entry.logical_path} absent ou illisible") from exc
    if len(data) != entry.size or hashlib.sha256(data).hexdigest() != entry.sha256:
        raise WorkflowError(f"corpus : {entry.logical_path} ne correspond plus au manifeste")


def _refuse_extra_files(files_dir: Path, expected: set[str]) -> None:
    """Un fichier surnuméraire est un corpus qui a bougé : A et B ne liraient
    plus la même chose, et le manifeste ne le dirait pas."""
    if not files_dir.is_dir():
        return
    for path in files_dir.rglob("*"):
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(files_dir).as_posix()
        if relative not in expected:
            raise WorkflowError(f"corpus : fichier surnuméraire — {relative}")


def _archive(path: Path, text: str) -> None:
    """L'ancienne demande est archivée en `demande.md.NNN`, jamais écrasée : une
    réponse partielle ne doit pas créer une seconde autorité (§2).

    Par **copie** et non par renommage — un arrêt entre les deux laisserait
    sinon la collaboration sans `demande.md`. Si la dernière archive porte déjà
    ce texte, c'est un rejeu : il n'y a rien à sauver une seconde fois.
    """
    numbers = sorted(
        int(suffix) for p in path.parent.glob(f"{path.name}.*")
        if (suffix := p.name.rsplit(".", 1)[-1]).isdigit()
    )
    if numbers:
        previous, _ = storage.read_text(path.with_name(f"{path.name}.{numbers[-1]:03d}"))
        if previous == text:
            return
    storage.write_atomic_text(
        path.with_name(f"{path.name}.{(numbers[-1] if numbers else 0) + 1:03d}"), text
    )


def _promoted_body(delivered: str) -> str:
    """Le livrable sans son en-tête : le programme l'écrit en lignes `> ...`,
    suivies d'une ligne vide — jamais de ligne vide à l'intérieur."""
    return delivered.split("\n\n", 1)[1]


_STOPPABLE = (
    Status.READY, Status.RUNNING, Status.WAITING_HUMAN, Status.INTERRUPTED, Status.ERROR,
    Status.AWAITING_APPROVAL,
)


def decide(
    collab: Path, kind: str, *, reserves: str | None = None, reason: str | None = None
) -> State:
    """Une décision humaine **sans appel** : acceptation, acceptation avec réserves,
    arrêt. (La correction ciblée passe par le moteur : `Correct`.)

    Sous le verrou, comme toute mutation. Consignée **avant** l'état : un arrêt
    brutal laisse une décision sans effet sur l'état, que la même commande achève
    sans la consigner deux fois. Accepter ne change pas le statut : « terminé »
    reste `AWAITING_APPROVAL`, l'acceptation est dans `decisions.json`.
    """
    with lock.acquire(collab / "verrou.json", "decide"):
        state = State.from_dict(_read_json(collab / "etat.json"))
        if kind in (decisions.ACCEPTED, decisions.ACCEPTED_WITH_RESERVES):
            if state.status is not Status.AWAITING_APPROVAL:
                raise WorkflowError(
                    f"statut {state.status.value} : il n'y a rien à accepter tant que le cycle"
                    " n'est pas allé à son terme (AWAITING_APPROVAL)"
                )
            current = decisions.latest(collab)
            if decisions.is_acceptance(current) and current is not None and (
                decisions.applies_to_current(collab, current, state)
            ):
                raise WorkflowError("ce résultat est déjà accepté : la décision ne se répète pas")
            if kind == decisions.ACCEPTED_WITH_RESERVES and not (reserves or "").strip():
                raise WorkflowError("l'acceptation avec réserves exige le texte des réserves")
            decisions.record(collab, kind, state, reserves=(reserves or "").strip() or None)
            return state
        if kind == decisions.STOPPED:
            if state.status not in _STOPPABLE:
                raise WorkflowError(f"statut {state.status.value} : rien à arrêter")
            decisions.record(collab, kind, state, reason=(reason or "").strip() or None)
            stopped = replace(state, status=Status.STOPPED, updated_at=_now())
            _write_json(collab / "etat.json", stopped.to_dict())
            return stopped
    raise WorkflowError(f"décision inconnue : {kind!r}")


def _archive_of(path: Path, sha256: str) -> str | None:
    """Le nom de la dernière archive de `path` dont le texte porte cette empreinte."""
    for candidate in sorted(path.parent.glob(f"{path.name}.*"), reverse=True):
        if candidate.name.rsplit(".", 1)[-1].isdigit() and (
            contracts.normalize(storage.read_text(candidate)[0]).sha256 == sha256
        ):
            return candidate.name
    return None


def _archived_text(path: Path, sha256: str) -> str | None:
    name = _archive_of(path, sha256)
    return None if name is None else storage.read_text(path.parent / name)[0]


def _current(state: State) -> CallState:
    if state.current_call is None:
        raise WorkflowError("aucun appel courant")
    return state.current_call


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    storage.write_atomic_text(path, _json_text(payload))


def _prior_line(finding: Finding, reply: contracts.ObjectionResponse | None) -> str:
    """Le constat antérieur tel que B le relit : l'énoncé initial, puis ce que A
    y a répondu — c'est ce que B doit juger, pas sa propre mémoire."""
    line = f"- {finding.id} [{finding.severity.value}] {finding.statement}"
    if reply is None:
        return line
    return f"{line}\n  Réponse de A : {reply.kind.value} — {reply.justification or '(sans détail)'}"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
