"""Interventions humaines (`conception/GUI_V1.md` §8) : répondre, relancer,
retraiter, corriger, accepter, arrêter. Une seule route pour les neuf
`ActionId` — la table qui dit ce qui est permis reste `decisions.
allowed_actions` (§10.2) ; ce module ne fait qu'inviter le texte requis, puis
confirmer avant tout ce qui peut appeler un agent (§3.5).

`ACCEPT`/`ACCEPT_WITH_RESERVES` ne passent jamais par `Controller.start_run` :
`workflow.decide` est une écriture locale sous verrou, synchrone, sans fil —
comme `decide --accept` en CLI, jamais un appel fournisseur.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from tkinter import Misc
from typing import TYPE_CHECKING

from ... import decisions, settings, workflow
from ...decisions import ActionId, AllowedAction
from .. import dialogs

if TYPE_CHECKING:
    from ..controller import Controller

_LABELS = {
    ActionId.START: "Démarrer la collaboration",
    ActionId.RESUME: "Reprendre le cycle",
    ActionId.ANSWER_AND_RESUME: "Répondre et reprendre",
    ActionId.RETRY_CALL: "Relancer l'appel",
    ActionId.REPROCESS_AND_RESUME: "Retraiter puis reprendre",
    ActionId.ACCEPT: "Accepter cette version",
    ActionId.ACCEPT_WITH_RESERVES: "Accepter avec réserves",
    ActionId.CORRECT: "Demander une correction ciblée",
    ActionId.STOP: "Arrêter définitivement",
}

_INPUT_LABELS = {
    "réponse": "Votre réponse — elle complète la demande, elle ne la remplace pas.",
    "motif": "Motif — pourquoi relancer ou retraiter cet appel.",
    "instruction": "Instruction de correction — elle complète la demande.",
    "réserves": "Vos réserves.",
}

_STOP_BODY = "Cette décision est définitive : aucune reprise n'est possible ensuite."


def label(action_id: ActionId) -> str:
    return _LABELS[action_id]


def run(parent: Misc, controller: Controller, path: Path, action: AllowedAction) -> None:
    """Invite le texte requis (§10.2 : `inputs`), confirme si l'action peut
    appeler un agent (§3.5), puis l'applique. Rien n'est fait si l'humain
    annule à une étape ou l'autre."""
    text: str | None = None
    if action.inputs:
        prompted = dialogs.prompt_text(
            parent, label(action.id), _INPUT_LABELS[action.inputs[0]],
        )
        if prompted is None or not prompted.strip():
            return
        text = prompted
    if action.may_call:
        if not _confirm_call(parent, path, action):
            return
    elif action.id is ActionId.STOP:
        if not dialogs.confirm(
            parent, "Arrêter définitivement ?", _STOP_BODY, ok_label=label(action.id),
        ):
            return
    _dispatch(controller, path, action, text)


def _confirm_call(parent: Misc, path: Path, action: AllowedAction) -> bool:
    resolved = settings.resolve_timeout(None, None, base=path.parent)
    body = (
        f"{label(action.id)} peut atteindre un nouvel appel fournisseur.\n\n"
        f"Délai effectif : {resolved.seconds:g} s\n"
        f"Origine : {resolved.origin}"
    )
    return dialogs.confirm(parent, "Confirmer ?", body, ok_label=label(action.id))


def _dispatch(controller: Controller, path: Path, action: AllowedAction, text: str | None) -> None:
    timeout_seconds = settings.resolve_timeout(None, None, base=path.parent).seconds
    action_id = action.id
    if action_id in (ActionId.START, ActionId.RESUME):
        controller.start_run(path, timeout_seconds=timeout_seconds)
    elif action_id is ActionId.ANSWER_AND_RESUME:
        assert text is not None
        controller.start_run(
            path, timeout_seconds=timeout_seconds, intervention=workflow.Answer(_write_temp(text)),
        )
    elif action_id is ActionId.RETRY_CALL:
        assert text is not None and action.call_id is not None
        controller.start_run(
            path, timeout_seconds=timeout_seconds,
            intervention=workflow.RetryCall(action.call_id, _write_temp(text)),
        )
    elif action_id is ActionId.REPROCESS_AND_RESUME:
        assert text is not None and action.call_id is not None
        controller.start_run(
            path, timeout_seconds=timeout_seconds,
            intervention=workflow.Reprocess(action.call_id, _write_temp(text)),
        )
    elif action_id is ActionId.CORRECT:
        assert text is not None
        controller.start_run(
            path, timeout_seconds=timeout_seconds, intervention=workflow.Correct(_write_temp(text)),
        )
    elif action_id is ActionId.ACCEPT:
        workflow.decide(path, decisions.ACCEPTED)
    elif action_id is ActionId.ACCEPT_WITH_RESERVES:
        assert text is not None
        workflow.decide(path, decisions.ACCEPTED_WITH_RESERVES, reserves=text)
    elif action_id is ActionId.STOP:
        workflow.decide(path, decisions.STOPPED)


def _write_temp(text: str) -> Path:
    """Un fichier jetable pour une intervention qui, en CLI, en désigne un —
    jamais dans la collaboration elle-même (§3.3 : rien n'y est écrit hors du
    moteur, sous verrou)."""
    fd, name = tempfile.mkstemp(prefix="dialogforge-", suffix=".md")
    path = Path(name)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path
