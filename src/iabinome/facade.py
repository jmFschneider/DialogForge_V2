"""Façade applicative commune à la CLI et à la GUI (`conception/GUI_V1.md` §10.1,
§10.3). Une façade sans appelant serait une API spéculative (`task_plan.md`,
Decisions Made) : chaque fonction ici vient avec l'écran qui l'appelle.

`inspect_collaboration` ne mute rien : charger, valider, présenter. **Le
dossier fait foi, jamais une mémoire de fenêtre** (§3.3) — chaque appel relit
`configuration.json` et `etat.json`, sans cache du statut ni de la phase.

`create_collaboration` (lot 4) est la **création partagée** (§6.1, §6.5) : la
CLI et la GUI y rassemblent la même requête structurée, jamais un
`argparse.Namespace` ni un formulaire Tkinter — une seule autorité pour ce
qu'une collaboration a le droit de contenir.
"""

from __future__ import annotations

import json
import shutil
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import contracts, corpus, decisions, incidents, settings, storage
from . import demande as demande_module
from .adapters.base import AgentAdapter
from .decisions import AllowedAction
from .framing import FramingArtifacts
from .models import (
    SCHEMA_VERSION,
    AgentPurpose,
    AgentSpec,
    CallStatus,
    Configuration,
    MissionKind,
    Phase,
    ReviewerAccess,
    SchemaError,
    State,
    Status,
)

_STATUS_LABELS = {
    Status.RUNNING: "En cours",
    Status.WAITING_HUMAN: "Intervention requise",
    Status.INTERRUPTED: "Appel inabouti",
    Status.ERROR: "Réponse reçue, inexploitable",
    Status.STOPPED: "Arrêt définitif",
}

_PHASE_LABELS = {
    Phase.PROPOSAL_A: "A produit la proposition",
    Phase.REVIEW_B: "B critique",
    Phase.REVISION_A: "A révise",
    Phase.CLOSED: "Clôturé",
}

_ACTIVITY_BY_STATUS = {
    Status.WAITING_HUMAN: "En attente de votre réponse",
    Status.INTERRUPTED: "Appel interrompu ; aucune relance automatique",
    Status.ERROR: "Réponse reçue mais inexploitable telle quelle",
    Status.AWAITING_APPROVAL: "Cycle terminé",
    Status.STOPPED: "Arrêt définitif",
}

_STOPPED_LOOKING = (Status.WAITING_HUMAN, Status.INTERRUPTED, Status.ERROR)


class InspectionError(RuntimeError):
    """Dossier illisible ou invalide (§5.1) : nommé avec son diagnostic, jamais
    réparé — la GUI ne devine pas ce qu'un dossier aurait dû contenir."""


@dataclass(frozen=True)
class DecisionSummary:
    """Le dernier point de `decisions.json`, ou son absence (§10.3)."""

    kind: str | None
    at: str | None
    applies_to_current_version: bool
    version_digest: str | None
    discrepancies: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionObservation:
    """Ce qu'*une* fenêtre sait de l'exécution en cours — jamais déduit du seul
    dossier (§7.2, §8.2). Le contrôleur GUI est seul à savoir s'il possède un
    fil moteur ; le lot 3 n'en lance aucun, donc toujours `False`/`None` ici."""

    owned_by_this_gui: bool
    runner_alive: bool | None


@dataclass(frozen=True)
class RuntimeResolution:
    timeout_seconds: float
    origin: str


@dataclass(frozen=True)
class Step:
    """Une étape de la progression : `✓` faite, `●` courante, `!` courante mais
    arrêtée (question, incident), `○` à venir, `—` sans objet."""

    symbol: str
    label: str


@dataclass(frozen=True)
class Progress:
    """La progression A/B d'un coup d'œil : un tour par ligne, A à gauche, B à
    droite, puis la décision humaine. Les rôles restent lisibles quel que soit
    l'outil, parce que chaque colonne nomme le sien."""

    agent_a: str
    agent_b: str
    rounds: tuple[tuple[Step, Step], ...]
    human: Step
    now: str


@dataclass(frozen=True)
class Presentation:
    status_label: str
    phase_label: str
    activity_label: str
    allowed_actions: tuple[AllowedAction, ...]
    readable_documents: tuple[str, ...]
    progress: Progress
    next_action_text: str
    trace_dir: str | None = None


@dataclass(frozen=True)
class CollaborationSnapshot:
    path: Path
    name: str
    configuration: Configuration
    state: State
    current_decision: DecisionSummary
    incident: str | None
    runtime_resolution: RuntimeResolution
    execution_observation: ExecutionObservation
    presentation: Presentation


def inspect_collaboration(
    path: Path, *, owned_by_this_gui: bool = False, runner_alive: bool | None = None,
) -> CollaborationSnapshot:
    """Relit intégralement le dossier et rend un instantané en lecture seule.

    `owned_by_this_gui`/`runner_alive` viennent de l'appelant : seul le
    contrôleur sait si *cette* fenêtre possède l'exécution qu'il observe. Sans
    exécution possédée, l'activité d'un `RUNNING` reste honnête plutôt
    qu'animée (§7.2) — c'est le cas par défaut, celui du lot 3.
    """
    try:
        config = Configuration.from_dict(_read_json(path / "configuration.json"))
        state = State.from_dict(_read_json(path / "etat.json"))
    except (OSError, ValueError, SchemaError) as exc:
        raise InspectionError(f"{path} : {exc}") from exc
    decision = _decision_summary(path, state)
    execution = ExecutionObservation(owned_by_this_gui, runner_alive)
    runtime = settings.resolve_timeout(None, None, base=path.parent)
    presentation = Presentation(
        status_label=_status_label(state, decision),
        phase_label=_phase_label(state, config),
        activity_label=_activity_label(state, execution),
        allowed_actions=decisions.allowed_actions(path, state),
        readable_documents=_readable_documents(path, state),
        progress=_progress(state, config, decision),
        next_action_text=decisions.next_action(path, state),
        trace_dir=_trace_dir(state),
    )
    return CollaborationSnapshot(
        path=path, name=path.name, configuration=config, state=state,
        current_decision=decision, incident=_incident_text(path, state),
        runtime_resolution=RuntimeResolution(runtime.seconds, runtime.origin),
        execution_observation=execution, presentation=presentation,
    )


def _decision_summary(path: Path, state: State) -> DecisionSummary:
    latest = decisions.latest(path)
    if latest is None:
        return DecisionSummary(None, None, False, None)
    digest = latest["version"].get("livrable_sha256")
    found = decisions.discrepancies(path, latest, state)
    return DecisionSummary(
        kind=str(latest["decision"]), at=str(latest["at"]),
        applies_to_current_version=not found,
        version_digest=None if digest is None else str(digest)[:12], discrepancies=found,
    )


def _incident_text(path: Path, state: State) -> str | None:
    lines = incidents.explain(path, state)
    return "\n".join(lines) if lines else None


def _status_label(state: State, decision: DecisionSummary) -> str:
    """`AWAITING_APPROVAL` dérive un sous-état de la décision courante — jamais
    ajouté à `etat.json` (§8.7, §10.3) : le statut moteur ne bouge pas."""
    if state.status is Status.READY:
        first = state.current_document is None and state.latest_review is None
        return "Prête" if first else "Prête ; en pause"
    if state.status is not Status.AWAITING_APPROVAL:
        return _STATUS_LABELS[state.status]
    if not decision.applies_to_current_version:
        return "Cycle terminé — décision requise"
    if decision.kind == decisions.ACCEPTED_WITH_RESERVES:
        return "Acceptée avec réserves"
    if decision.kind == decisions.ACCEPTED:
        return "Version acceptée"
    return "Cycle terminé — décision requise"


def _phase_label(state: State, config: Configuration) -> str:
    """§7.1 : `REVISION_A` porte le tour courant, `REVIEW_B` la relecture qui le
    suit dès qu'une révision a déjà eu lieu."""
    if state.phase is Phase.REVISION_A:
        return f"Révision {state.revision} sur {config.max_revisions}"
    if state.phase is Phase.REVIEW_B and state.revision > 0:
        return f"Relecture B de la révision {state.revision}"
    return _PHASE_LABELS[state.phase]


def _activity_label(state: State, execution: ExecutionObservation) -> str:
    """§7.2, table d'activité honnête : jamais d'activité affichée sans preuve
    qu'*une* exécution possédée par cette fenêtre en est la source."""
    if state.status is Status.READY:
        return "Prête ; aucun appel en cours"
    if state.status is Status.RUNNING:
        if not execution.owned_by_this_gui:
            return "État enregistré : appel en cours ou processus arrêté ; activité non prouvée"
        call = state.current_call
        if call is not None and call.status is CallStatus.CALLING:
            return "Appel fournisseur en cours"
        return "Réponse reçue, traitement local en cours"
    return _ACTIVITY_BY_STATUS[state.status]


def _progress(state: State, config: Configuration, decision: DecisionSummary) -> Progress:
    """§7.1, étendu au retour d'usage du 2026-09-28 : un tour par ligne (proposition
    puis critique, puis révision et relecture n), l'étape courante, ce qui est fait,
    et ce qui attend l'humain. Une fois clos, seuls les tours joués restent ; avant,
    les révisions possibles jusqu'au plafond sont annoncées comme conditionnelles."""
    closed = state.phase is Phase.CLOSED
    stopped = state.status is Status.STOPPED
    count = state.revision + 1 if closed else max(config.max_revisions, state.revision) + 1
    cursor = None if closed else 2 * state.revision + (state.phase is Phase.REVIEW_B)

    def mark(index: int) -> str:
        if cursor is None or index < cursor:
            return "✓"
        if stopped:
            return "—"
        if index == cursor:
            return "!" if state.status in _STOPPED_LOOKING else "●"
        return "○"

    rounds = []
    for r in range(count):
        a_label = "Proposition" if r == 0 else f"Révision {r}"
        if not closed and r > state.revision:
            a_label += " (si B la demande)"
        b_label = "Critique" if r == 0 else f"Relecture {r}"
        rounds.append((Step(mark(2 * r), a_label), Step(mark(2 * r + 1), b_label)))

    accepted = {
        decisions.ACCEPTED: "acceptée", decisions.ACCEPTED_WITH_RESERVES: "acceptée avec réserves",
    }.get(decision.kind or "") if decision.applies_to_current_version else None
    if stopped:
        human, now = Step("—", "Arrêtée"), "Arrêtée par décision humaine."
    elif state.status is Status.AWAITING_APPROVAL and accepted:
        human, now = Step("✓", f"Décision : {accepted}"), f"Terminé : version {accepted}."
    elif state.status is Status.AWAITING_APPROVAL:
        human = Step("●", "Décision : à prendre")
        now = "À vous : lire le bilan et décider sur la version relue par B."
    else:
        human, now = Step("○", "Décision"), _now_text(state, config, rounds, cursor)
    return Progress(
        agent_a=f"A · {config.agent_a.adapter_id} ({config.agent_a.model})",
        agent_b=f"B · {config.agent_b.adapter_id} ({config.agent_b.model})",
        rounds=tuple(rounds), human=human, now=now,
    )


def _now_text(
    state: State, config: Configuration, rounds: list[tuple[Step, Step]], cursor: int | None,
) -> str:
    if cursor is None:
        return "Cycle clos."
    role = "AB"[cursor % 2]
    spec = config.agent_a if role == "A" else config.agent_b
    step = rounds[cursor // 2][cursor % 2].label
    who = f"{role} · {spec.adapter_id}"
    if state.status is Status.WAITING_HUMAN:
        return f"À vous : {role} pose une question ({step})."
    if state.status in (Status.INTERRUPTED, Status.ERROR):
        return f"À vous : l'appel de {who} n'a pas abouti ({step})."
    if state.status is Status.READY:
        if state.current_document is None and state.latest_review is None:
            return f"Prête : au démarrage, {step} par {who}."
        return f"En pause : prochaine étape, {step} par {who}."
    return f"Étape courante : {step} par {who}."


def _trace_dir(state: State) -> str | None:
    """Le dossier de l'appel qui n'a pas abouti — pour aller droit à sa trace."""
    if state.status in (Status.INTERRUPTED, Status.ERROR) and state.current_call is not None:
        return state.current_call.call_dir
    return None


def _readable_documents(path: Path, state: State) -> tuple[str, ...]:
    """Ce que l'écran de suivi propose à la lecture — seulement ce qui existe,
    dans l'ordre où un humain les lirait (§7, §8.6). Après un appel inabouti,
    ses sorties brutes non vides s'y ajoutent : la cause y est, telle quelle."""
    candidates = [
        "demande.md", state.current_document, state.latest_review,
        decisions.DELIVERED, "livrables/bilan.md",
    ]
    trace = _trace_dir(state)
    if trace is not None:
        candidates += [f"{trace}/stderr.txt", f"{trace}/stdout.txt"]
    seen: list[str] = []
    for candidate in candidates:
        if not candidate or candidate in seen or not (path / candidate).is_file():
            continue
        if candidate.startswith("appels/") and not (path / candidate).stat().st_size:
            continue
        seen.append(candidate)
    return tuple(seen)


# -- Création (lot 4, §6) --


@dataclass(frozen=True)
class DemandeSource:
    """Le texte de la demande tel qu'un écran l'a obtenu, et sa provenance
    (§6.2) : « fichier » pour un import laissé inchangé, « cadrage » pour une
    saisie directe ou un import modifié dans la GUI — les deux seuls chemins
    que `provenance_demande.json` connaît déjà, la GUI n'en ajoute aucun."""

    text: str
    origin: str
    imported_path: str | None = None


@dataclass(frozen=True)
class CreationRequest:
    """Ce qu'un écran — CLI ou GUI — a rassemblé avant de créer (§6.1). Ni
    `argparse.Namespace`, ni formulaire Tkinter : une seule forme, que
    `create_collaboration` seule sait interpréter."""

    collab: Path
    demande: DemandeSource
    kind: MissionKind
    reviewer_access: ReviewerAccess
    agent_a: str
    agent_b: str
    max_revisions: int
    model_a: str | None = None
    model_b: str | None = None
    effort_a: str | None = None
    effort_b: str | None = None
    web_access: bool = False
    source_root: Path | None = None
    source_list: Path | None = None
    source_label: str | None = None
    # Cadrage avec agent F (`conception/CADRAGE_AGENT.md` §10) : le brouillon de F, sa
    # provenance, et le corpus déjà préparé — jamais relu depuis le projet d'origine.
    framing: FramingArtifacts | None = None


@dataclass(frozen=True)
class CreationResult:
    path: Path
    missing_sections: tuple[str, ...]


class CreationError(RuntimeError):
    """Refus avant toute écriture (§6.5) : rien n'est créé, l'écran qui a
    appelé reste tel quel — formulaire intact, ligne de commande inchangée."""


def create_collaboration(
    request: CreationRequest, *, adapters: Mapping[str, AgentAdapter],
) -> CreationResult:
    """La création **partagée** (§6.1, §6.6) : mêmes vérifications, même
    écriture, que la CLI et la GUI appellent l'une comme l'autre — la
    « validation autoritaire » du §6.5. Tout est vérifié avant la première
    écriture ; un refus ne laisse aucun dossier partiel derrière lui (AC-12).
    """
    check_creation(request, adapters=adapters)
    dest = request.collab
    tmp = dest.parent / f".new-{dest.name}-{uuid.uuid4().hex}"
    tmp.mkdir(parents=True)
    try:
        _write_collaboration(tmp, dest, request, adapters)
    except (corpus.CorpusError, OSError, ValueError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        raise CreationError(str(exc)) from exc
    tmp.rename(dest)
    return CreationResult(
        path=dest, missing_sections=tuple(demande_module.missing(request.demande.text)),
    )


def check_creation(request: CreationRequest, *, adapters: Mapping[str, AgentAdapter]) -> None:
    """Les refus de `create_collaboration`, sans rien écrire : le cadrage avec agent
    les passe **avant** d'ouvrir la session de F (§3.2), pour qu'aucun appel ne soit
    payé au profit d'une création qui serait refusée ensuite."""
    dest = request.collab
    if dest.exists():
        raise CreationError(f"{dest} existe deja")
    if bool(request.source_root) != bool(request.source_list):
        raise CreationError("--source-root et --source-list vont ensemble")
    if request.framing is not None and request.source_root:
        raise CreationError("sources déjà copiées par le cadrage : elles ne sont pas relues")
    framed_corpus = request.framing is not None and (
        request.framing.root / "corpus" / "manifeste.json"
    ).is_file()
    problem = request.kind.missing_source(
        corpus=bool(request.source_root) or framed_corpus, web=request.web_access,
    )
    if problem:
        raise CreationError(problem)
    for who, adapter_id, effort in (
        ("A", request.agent_a, request.effort_a), ("B", request.agent_b, request.effort_b),
    ):
        adapter = adapters.get(adapter_id)
        if adapter is None:
            raise CreationError(f"adaptateur inconnu : {adapter_id!r}")
        levels = adapter.capabilities.effort_levels
        if effort is not None and effort not in levels:
            raise CreationError(
                f"effort {who} : {effort!r} refusé par {adapter_id} — attendu : "
                f"{', '.join(levels) or 'aucun'}"
            )


def _write_collaboration(
    tmp: Path, dest: Path, request: CreationRequest, adapters: Mapping[str, AgentAdapter],
) -> None:
    normalized = contracts.normalize(request.demande.text)
    storage.write_atomic_text(tmp / "demande.md", normalized.text)
    entry: dict[str, Any] = {
        "source": request.demande.origin, "path": request.demande.imported_path,
        "sha256": normalized.sha256,
    }
    corpus_sha: str | None = None
    if request.framing is not None:
        entry, corpus_sha = _write_framing(tmp, request.framing, normalized.sha256)
    demande_module.record(tmp, entry)
    if request.source_root:
        assert request.source_list is not None
        manifest = corpus.build(
            request.source_root, request.source_list, tmp / "corpus",
            request.source_label or request.source_root.name,
        )
        problem = request.kind.missing_source(corpus=bool(manifest.entries), web=request.web_access)
        if problem:
            raise ValueError(f"corpus vide — {problem}")
        manifest_text, _ = storage.read_text(tmp / "corpus" / "manifeste.json")
        corpus_sha = contracts.normalize(manifest_text).sha256
    agent_a, agent_b = adapters[request.agent_a], adapters[request.agent_b]
    config = Configuration(
        schema_version=SCHEMA_VERSION, collaboration_id=dest.name, mission_kind=request.kind,
        reviewer_access=request.reviewer_access, max_revisions=request.max_revisions,
        agent_a=AgentSpec(
            request.agent_a, request.model_a or agent_a.default_model(AgentPurpose.A),
            request.effort_a,
        ),
        agent_b=AgentSpec(
            request.agent_b, request.model_b or agent_b.default_model(AgentPurpose.B),
            request.effort_b,
        ),
        initial_demande_sha256=normalized.sha256, corpus_manifest_sha256=corpus_sha,
        created_at=_now(), web_access=request.web_access,
    )
    state = State(
        schema_version=SCHEMA_VERSION, status=Status.READY, phase=Phase.PROPOSAL_A, revision=0,
        demande_sha256=normalized.sha256, current_document=None, latest_review=None,
        open_finding_ids=[], current_call=None, last_incident=None, updated_at=_now(),
    )
    _write_json(tmp / "configuration.json", config.to_dict())
    _write_json(tmp / "etat.json", state.to_dict())


def _write_framing(
    tmp: Path, framing: FramingArtifacts, accepted_sha: str
) -> tuple[dict[str, Any], str | None]:
    """`cadrage/` (§9) : traces des échanges, transcription, provenance — des chemins
    relatifs seulement. Le corpus est celui que F a lu, copié tel quel. Rend l'entrée
    de `provenance_demande.json` (schéma inchangé, §9.3) et l'empreinte du manifeste."""
    draft_sha = contracts.normalize(framing.draft).sha256
    edited = draft_sha != accepted_sha
    shutil.copytree(framing.root / "appels", tmp / "cadrage" / "appels")
    shutil.copyfile(framing.root / "transcription.md", tmp / "cadrage" / "transcription.md")
    _write_json(tmp / "cadrage" / "provenance.json", {
        **framing.provenance, "agent_draft_sha256": draft_sha,
        "accepted_demande_sha256": accepted_sha, "human_edited": edited,
    })
    corpus_sha = None
    if (framing.root / "corpus" / "manifeste.json").is_file():
        shutil.copytree(framing.root / "corpus", tmp / "corpus")
        text, _ = storage.read_text(tmp / "corpus" / "manifeste.json")
        corpus_sha = contracts.normalize(text).sha256
    return {
        "source": "cadrage", "path": None, "sha256": accepted_sha, "method": "agent",
        "framing_provenance": "cadrage/provenance.json", "agent_draft_sha256": draft_sha,
        "human_edited": edited,
    }, corpus_sha


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)
