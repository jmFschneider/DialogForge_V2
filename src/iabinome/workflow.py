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

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import contracts, lock, prompts, storage, transport
from .adapters.base import AgentAdapter, CallSpec, ObservedCli
from .contracts import ContractError, Finding
from .models import (
    SCHEMA_VERSION,
    CallState,
    CallStatus,
    Configuration,
    Decision,
    MissionKind,
    Phase,
    ReviewerAccess,
    Role,
    Severity,
    State,
    Status,
)
from .transport import Outcome


class WorkflowError(RuntimeError):
    """Prévol refusé, intervention refusée, ou état modifié sous le verrou."""


@dataclass(frozen=True)
class Answer:
    """`resume --answer` : le fichier portant la réponse humaine."""

    path: Path


@dataclass(frozen=True)
class RetryCall:
    """`resume --retry-call` : l'appel à relancer et le fichier de motif."""

    call_id: str
    reason_path: Path


Intervention = Answer | RetryCall


@dataclass(frozen=True)
class _Retry:
    """Relance validée sous verrou, portée jusqu'à `intention.json`."""

    call_id: str
    reason: str


_ROLE_OF_PHASE = {
    Phase.PROPOSAL_A: Role.A,
    Phase.REVIEW_B: Role.B,
    Phase.REVISION_A: Role.A,
    Phase.FINAL_A: Role.A,
}

# Une QUESTION née en PROPOSAL_A ou REVISION_A y retourne ; une née en FINAL_A
# ou un BLOQUE (né en REVIEW_B) reprennent en REVISION_A, avec le document
# courant et les constats déjà ouverts (§2).
_RESUME_PHASE = {Phase.REVIEW_B: Phase.REVISION_A, Phase.FINAL_A: Phase.REVISION_A}

# La porte d'état nomme la commande qui sort du statut refusé : un refus qui
# n'indique pas la suite renvoie l'humain au code source.
_WAY_OUT = {
    Status.WAITING_HUMAN: "resume --answer <fichier>",
    Status.INTERRUPTED: "resume --retry-call <uuid> --reason-file <fichier>",
    Status.ERROR: "resume --retry-call <uuid> --reason-file <fichier>",
    Status.AWAITING_APPROVAL: "aucune, le cycle est allé à son terme",
}

# Sortie de ERROR : **table fermée**, jamais héritée du statut (N-01). Toute
# autre famille d'erreur devra y être ajoutée explicitement.
_RELAUNCHABLE = frozenset({"CONTRACT_ERROR", "DECODE_FAILED"})

_NOT_APPROVED = (
    "> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est"
    " achevé, rien de plus.\n"
    "> Revue B : {access} · constats restés ouverts : {open} (dont {blocking}"
    " BLOCKING) · corpus {corpus}.\n\n"
)


def run(
    collab: Path,
    *,
    adapters: Mapping[str, AgentAdapter],
    timeout_seconds: float,
    command_label: str = "run",
    intervention: Intervention | None = None,
) -> State:
    """L'unique moteur synchrone. Il enchaîne les appels tant que l'état reste
    `READY` ; toute autre valeur rend la main à l'humain.

    L'intervention humaine est appliquée **sous le verrou**, entre la relecture
    et la porte d'état, puis consommée — comme la relance l'était déjà, elle ne
    vaut que pour la première itération.

    La boucle est bornée par la machine à états elle-même — `max_revisions`
    plafonne les allers-retours et `FINAL_A` est terminal. **Aucun compteur de
    garde n'est ajouté** : ce serait un quota interne.
    """
    while True:
        engine, state = _preflight(collab, adapters, timeout_seconds, intervention)
        with lock.acquire(collab / "verrou.json", command_label):      # étape 2
            engine.recheck(state)                                      # étape 3
            state, retry = engine.intervene(state, intervention)
            engine.gate(state)
            if state.current_call is not None:
                state = engine.resume_call(state)
            else:
                state = engine.new_call(state, retry)
        intervention = None
        if state.status is not Status.READY:
            return state


def _preflight(
    collab: Path,
    adapters: Mapping[str, AgentAdapter],
    timeout_seconds: float,
    intervention: Intervention | None = None,
) -> tuple[_Engine, State]:
    """Étape 1, **sans aucune mutation** : demande, schémas, état, empreintes,
    corpus, adaptateurs, versions observées, modèles, profil de revue. Un
    adaptateur incapable du profil demandé est refusé **avant l'appel** (§1, §8)."""
    config = Configuration.from_dict(_read_json(collab / "configuration.json"))
    state = State.from_dict(_read_json(collab / "etat.json"))
    answer = _read_answer(intervention)
    demande = _check_demande(collab, state, answer, "au prévol")
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
    engine = _Engine(collab, config, adapters, observed, demande, timeout_seconds, answer)
    engine.check_corpus()
    return engine, state


def _read_answer(intervention: Intervention | None) -> contracts.Normalized | None:
    """La réponse est lue **une fois**, au prévol : le moteur construit ses
    prompts avec elle, et la relecture sous verrou en tolère l'empreinte."""
    if not isinstance(intervention, Answer):
        return None
    text, _ = storage.read_text(intervention.path)
    return contracts.normalize(text)


def _check_demande(
    collab: Path, state: State, answer: contracts.Normalized | None, where: str
) -> str:
    """`demande.md` porte l'empreinte de l'état — ou, quand une réponse est
    fournie, déjà la sienne. Ce second cas est l'intervention interrompue entre
    l'écriture de la demande et la publication de l'état : la reprise doit
    pouvoir l'achever, et non la refuser ici avant d'avoir pu réparer."""
    text, _ = storage.read_text(collab / "demande.md")
    accepted = {state.demande_sha256}
    if answer is not None:
        accepted.add(answer.sha256)
    if contracts.normalize(text).sha256 not in accepted:
        raise WorkflowError(f"demande.md ne correspond plus à l'empreinte de l'état ({where})")
    return text if answer is None else answer.text


@dataclass(frozen=True)
class _Engine:
    collab: Path
    config: Configuration
    adapters: Mapping[str, AgentAdapter]
    observed: dict[str, ObservedCli]
    demande: str
    timeout_seconds: float
    answer: contracts.Normalized | None = None

    # -- Prévol et relecture sous verrou --

    def check_corpus(self) -> None:
        """Le corpus est figé : il n'existe pas de rafraîchissement. Le changer
        en cours de cycle détruirait la référence commune de A et B (§3)."""
        if self.config.corpus_manifest_sha256 is None:
            if self.config.mission_kind is MissionKind.RECHERCHE:
                raise WorkflowError("mission de recherche sans corpus")
            return
        text, _ = storage.read_text(self.collab / "corpus" / "manifeste.json")
        if contracts.normalize(text).sha256 != self.config.corpus_manifest_sha256:
            raise WorkflowError("le manifeste de corpus ne correspond plus à la configuration")

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
        if isinstance(intervention, RetryCall):
            return self.apply_retry(state, intervention)
        return state, None

    def apply_answer(self, state: State) -> State:
        """Archive **par copie**, écrit `demande.md`, publie l'état — dans cet
        ordre, si bien que `demande.md` n'est jamais absent, fût-ce une seconde.

        Un arrêt après l'archive laisse la demande d'origine : le rejeu
        réarchive un texte déjà archivé, donc ne réarchive pas. Un arrêt après
        l'écriture laisse l'unique cas particulier reconnu — l'état dit encore
        `WAITING_HUMAN` avec l'ancienne empreinte alors que `demande.md` porte
        déjà celle de la réponse : il ne reste qu'à publier l'état.
        """
        assert self.answer is not None  # lu au prévol, avec la demande
        if state.status is not Status.WAITING_HUMAN:
            raise WorkflowError(
                f"statut {state.status.value} : la collaboration n'attend pas de réponse humaine"
            )
        path = self.collab / "demande.md"
        current, _ = storage.read_text(path)
        if contracts.normalize(current).sha256 != self.answer.sha256:
            _archive(path, current)
            storage.write_atomic_text(path, self.answer.text)
        return self.publish(replace(
            state, status=Status.READY, phase=_RESUME_PHASE.get(state.phase, state.phase),
            demande_sha256=self.answer.sha256,
        ))

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
        (self.collab / rel_dir).mkdir(parents=True)
        prompt = self.build_prompt(state)
        storage.write_atomic_text(self.collab / rel_dir / "prompt.txt", prompt)
        digest = contracts.normalize(prompt).sha256
        _write_json(self.collab / rel_dir / "intention.json", {
            "schema_version": SCHEMA_VERSION, "call_id": call_id, "sequence": sequence,
            "role": role.value, "phase": state.phase.value,
            "adapter_id": agent.adapter_id, "model": agent.model,
            "observed_version": self.observed[agent.adapter_id].version,
            "reviewer_access": self.config.reviewer_access.value, "prompt_sha256": digest,
            "retries": None if retry is None else retry.call_id,
            "retry_reason": None if retry is None else retry.reason, "created_at": _now(),
        })
        call = CallState(
            call_id=call_id, sequence=sequence, role=role, phase=state.phase,
            status=CallStatus.CALLING, call_dir=rel_dir, prompt_sha256=digest,
            response_sha256=None, started_at=_now(), completed_at=None,
        )
        spec = CallSpec(
            prompt=prompt, model=agent.model, timeout_seconds=self.timeout_seconds,
            work_root=self.collab,
            reviewer_access=self.config.reviewer_access if role is Role.B else None,
        )
        # `command()` est résolu AVANT la publication de CALLING : un exécutable
        # disparu entre le prévol et l'appel devient un refus sans mutation, au
        # lieu d'un faux « possiblement payé » sur un appel jamais parti.
        argv = self.adapters[agent.adapter_id].command(spec)
        # Étape 4 : CALLING publié AVANT Popen. Un crash ici est déjà interprétable.
        state = self.publish(replace(state, status=Status.RUNNING, current_call=call))
        # Le prompt passe par stdin, jamais par la ligne de commande : mesuré le
        # 2026-09-03, argv plafonne à 32 767 caractères sous Windows, et une CLI
        # qui voit `DEVNULL` sur son entrée la lit comme un flux vide et dégrade
        # sa réponse (`conception/CARACTERISATION_CLI.md`, point 1).
        result = transport.run(
            argv, cwd=self.collab, call_dir=self.collab / rel_dir,
            timeout_seconds=self.timeout_seconds, stdin_text=prompt,
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
        raw = self.adapters[agent.adapter_id].extract(
            (call_dir / "stdout.txt").read_bytes(), (call_dir / "stderr.txt").read_bytes()
        )
        storage.write_atomic_text(call_dir / "reponse_brute.txt", raw)
        normalized = contracts.normalize(raw)
        state = self.publish(replace(state, current_call=replace(
            call, status=CallStatus.RESPONSE_STORED,
            response_sha256=normalized.sha256, completed_at=_now(),
        )))
        return self.apply(state, normalized.text)

    def resume_call(self, state: State) -> State:
        """Table de reprise §5 — le dossier d'appel fait foi, pas le seul statut."""
        call = _current(state)
        call_dir = self.collab / call.call_dir
        if call.status is CallStatus.RESPONSE_STORED:
            raw, _ = storage.read_text(call_dir / "reponse_brute.txt")
            return self.apply(state, contracts.normalize(raw).text)
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
        if state.phase is Phase.FINAL_A:
            path = self.write_final(state, response.body)
            return self.publish(replace(
                state, status=Status.AWAITING_APPROVAL, phase=Phase.CLOSED,
                current_document=path, current_call=None,
            ))
        name = (
            "proposition-A.md" if state.phase is Phase.PROPOSAL_A
            else f"revision-{state.revision}-A.md"
        )
        return self.publish(replace(
            state, status=Status.READY, phase=Phase.REVIEW_B, current_call=None,
            current_document=self.write_exchange(call.sequence, name, response.body),
        ))

    def apply_b(self, state: State, call: CallState, text: str) -> State:
        review = contracts.parse_review(text, state.open_finding_ids)
        state = replace(
            state, current_call=None,
            latest_review=self.write_exchange(call.sequence, "critique-B.json", text),
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
            return self.publish(replace(state, status=Status.READY, phase=Phase.FINAL_A))
        if state.revision >= self.config.max_revisions:
            return self.publish(replace(state, status=Status.READY, phase=Phase.FINAL_A))
        return self.publish(replace(
            state, status=Status.READY, phase=Phase.REVISION_A, revision=state.revision + 1
        ))

    # -- Prompts et artefacts --

    def build_prompt(self, state: State) -> str:
        date = self.corpus_date()
        if state.phase is Phase.PROPOSAL_A:
            return prompts.build_proposal(self.demande, self.config.mission_kind, date)
        document = self.read_relative(state.current_document)
        if state.phase is Phase.REVIEW_B:
            findings = self.open_findings(state)
            prior = "\n".join(
                f"- {f.id} [{f.severity.value}] {f.statement}" for f in findings
            ) or "Aucun."
            return prompts.build_review(
                self.demande, document, prior, self.config.reviewer_access, date
            )
        review = self.read_relative(state.latest_review)
        build = (
            prompts.build_revision if state.phase is Phase.REVISION_A else prompts.build_final
        )
        return build(self.demande, document, review, self.config.mission_kind, date)

    def open_findings(self, state: State) -> list[Finding]:
        """Le registre unique fait foi : les constats ouverts se relisent dans la
        dernière revue, jamais dans une seconde vérité (§6)."""
        if state.latest_review is None:
            return []
        open_ids = set(state.open_finding_ids)
        review = contracts.parse_review(self.read_relative(state.latest_review))
        return [f for f in review.findings if f.id in open_ids]

    def write_final(self, state: State, body: str) -> str:
        """La ligne d'en-tête est écrite par le programme et vraie à tout moment :
        le cycle s'achève en `AWAITING_APPROVAL`, jamais en « succès » (§2)."""
        findings = self.open_findings(state)
        date = self.corpus_date()
        header = _NOT_APPROVED.format(
            access=self.config.reviewer_access.value, open=len(findings),
            blocking=sum(1 for f in findings if f.severity is Severity.BLOCKING),
            corpus="absent" if date is None else f"figé le {date}",
        )
        (self.collab / "livrables").mkdir(exist_ok=True)
        storage.write_atomic_text(
            self.collab / "livrables" / "version_finale.md", header + body
        )
        return "livrables/version_finale.md"

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


def _current(state: State) -> CallState:
    if state.current_call is None:
        raise WorkflowError("aucun appel courant")
    return state.current_call


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
