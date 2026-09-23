"""Façade applicative commune à la CLI et à la GUI (`conception/GUI_V1.md` §10.1,
§10.3). Lot 3 : seule `inspect_collaboration` existe — une façade sans appelant
serait une API spéculative (voir `task_plan.md`, Decisions Made). Elle ne mute
rien : charger, valider, présenter.

**Le dossier fait foi, jamais une mémoire de fenêtre** (§3.3) : chaque appel
relit `configuration.json` et `etat.json`, sans cache du statut ni de la phase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import decisions, incidents, settings, storage
from .decisions import AllowedAction
from .models import CallStatus, Configuration, Phase, SchemaError, State, Status

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

_PHASE_ORDER = (Phase.PROPOSAL_A, Phase.REVIEW_B, Phase.REVISION_A, Phase.CLOSED)
_PHASE_STEP_LABELS = ("Proposition A", "Critique B", "Révision A", "Clôture")
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
class Presentation:
    status_label: str
    phase_label: str
    activity_label: str
    allowed_actions: tuple[AllowedAction, ...]
    readable_documents: tuple[str, ...]
    phase_steps: tuple[tuple[str, str], ...]
    next_action_text: str


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
        phase_steps=_phase_steps(state),
        next_action_text=decisions.next_action(path, state),
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
    return DecisionSummary(
        kind=str(latest["decision"]), at=str(latest["at"]),
        applies_to_current_version=decisions.applies_to_current(path, latest, state),
        version_digest=None if digest is None else str(digest)[:12],
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


def _phase_steps(state: State) -> tuple[tuple[str, str], ...]:
    """§7.1 : une marque par phase — faite (`✓`), courante (`●` ou `!` sous
    intervention/incident), à venir (`○`), ou sans objet (`—`) — une révision
    qui n'a jamais eu lieu, quand B a accepté d'emblée."""
    current = _PHASE_ORDER.index(state.phase)
    closed = state.phase is Phase.CLOSED
    steps: list[tuple[str, str]] = []
    for index, phase in enumerate(_PHASE_ORDER):
        if phase is Phase.REVISION_A and state.revision == 0 and closed:
            symbol = "—"
        elif index < current or (index == current and closed):
            # Une fois clos, plus rien n'est « en cours » : la dernière phase
            # atteinte se lit comme les précédentes, faite (§8.6, §8.7).
            symbol = "✓"
        elif index == current:
            symbol = "!" if state.status in _STOPPED_LOOKING else "●"
        else:
            symbol = "○"
        steps.append((symbol, _PHASE_STEP_LABELS[index]))
    return tuple(steps)


def _readable_documents(path: Path, state: State) -> tuple[str, ...]:
    """Ce que l'écran de suivi propose à la lecture — seulement ce qui existe,
    dans l'ordre où un humain les lirait (§7, §8.6)."""
    candidates = (
        "demande.md", state.current_document, state.latest_review,
        decisions.DELIVERED, "livrables/bilan.md",
    )
    seen: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen and (path / candidate).is_file():
            seen.append(candidate)
    return tuple(seen)


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)
