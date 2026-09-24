"""GUI V1, lot 5 : `views.intervention.run` — la seule route entre un bouton
de l'écran de suivi et une intervention du moteur (`conception/GUI_V1.md`
§8). `decisions.allowed_actions` reste la seule table de ce qui est permis ;
ce module invite le texte requis, confirme ce qui peut appeler, puis
transmet — jamais une règle dupliquée.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

from iabinome import decisions, workflow
from iabinome.decisions import ActionId
from iabinome.gui import dialogs
from iabinome.gui.controller import Controller
from iabinome.gui.views import intervention
from tests.test_actions import ActionsCase
from tests.test_gui_views import _ROOT, collect_tk_garbage


class InterventionCase(ActionsCase):
    def setUp(self) -> None:
        collect_tk_garbage()
        super().setUp()
        self.controller = Controller(_ROOT)
        self.addCleanup(lambda: [c.destroy() for c in list(_ROOT.winfo_children())])

    def action(self, collab: Path, action_id: ActionId) -> decisions.AllowedAction:
        return next(
            a for a in decisions.allowed_actions(collab, self.state(collab)) if a.id is action_id
        )


class TestLocalDecisionsNeverCallStartRun(InterventionCase):
    def test_accept_needs_no_prompt_and_no_confirmation(self) -> None:
        collab = self.situation("awaiting")
        with mock.patch.object(dialogs, "prompt_text") as prompt, \
             mock.patch.object(dialogs, "confirm") as confirm, \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(_ROOT, self.controller, collab, self.action(collab, ActionId.ACCEPT))
        prompt.assert_not_called()
        confirm.assert_not_called()
        start_run.assert_not_called()
        entry = decisions.latest(collab)
        assert entry is not None
        self.assertEqual(entry["decision"], decisions.ACCEPTED)

    def test_accept_with_reserves_needs_the_reserves(self) -> None:
        collab = self.situation("awaiting")
        with mock.patch.object(dialogs, "prompt_text", return_value="   "):
            intervention.run(
                _ROOT, self.controller, collab,
                self.action(collab, ActionId.ACCEPT_WITH_RESERVES),
            )
        self.assertIsNone(decisions.latest(collab))

    def test_accept_with_reserves_applies_the_typed_text(self) -> None:
        collab = self.situation("awaiting")
        with mock.patch.object(dialogs, "prompt_text", return_value="Réserve X."):
            intervention.run(
                _ROOT, self.controller, collab,
                self.action(collab, ActionId.ACCEPT_WITH_RESERVES),
            )
        entry = decisions.latest(collab)
        assert entry is not None
        self.assertEqual(entry["decision"], decisions.ACCEPTED_WITH_RESERVES)
        self.assertEqual(entry["reserves"], "Réserve X.")

    def test_stop_asks_a_plain_confirmation_and_applies_it(self) -> None:
        collab = self.situation("awaiting")
        with mock.patch.object(dialogs, "confirm", return_value=True) as confirm:
            intervention.run(_ROOT, self.controller, collab, self.action(collab, ActionId.STOP))
        confirm.assert_called_once()
        entry = decisions.latest(collab)
        assert entry is not None
        self.assertEqual(entry["decision"], decisions.STOPPED)

    def test_cancelling_the_stop_confirmation_does_nothing(self) -> None:
        collab = self.situation("awaiting")
        with mock.patch.object(dialogs, "confirm", return_value=False):
            intervention.run(_ROOT, self.controller, collab, self.action(collab, ActionId.STOP))
        self.assertIsNone(decisions.latest(collab))


class TestActionsThatMayCall(InterventionCase):
    def test_cancelling_the_prompt_never_reaches_the_confirmation(self) -> None:
        collab = self.situation("question")
        with mock.patch.object(dialogs, "prompt_text", return_value=None), \
             mock.patch.object(dialogs, "confirm") as confirm, \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(
                _ROOT, self.controller, collab,
                self.action(collab, ActionId.ANSWER_AND_RESUME),
            )
        confirm.assert_not_called()
        start_run.assert_not_called()

    def test_cancelling_the_confirmation_never_starts_a_run(self) -> None:
        collab = self.situation("question")
        with mock.patch.object(dialogs, "prompt_text", return_value="Le critère est X."), \
             mock.patch.object(dialogs, "confirm", return_value=False), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(
                _ROOT, self.controller, collab,
                self.action(collab, ActionId.ANSWER_AND_RESUME),
            )
        start_run.assert_not_called()

    def test_answering_writes_the_text_and_starts_a_run(self) -> None:
        collab = self.situation("question")
        with mock.patch.object(dialogs, "prompt_text", return_value="Le critère est X."), \
             mock.patch.object(dialogs, "confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(
                _ROOT, self.controller, collab,
                self.action(collab, ActionId.ANSWER_AND_RESUME),
            )
        start_run.assert_called_once()
        (path,), kwargs = start_run.call_args
        self.assertEqual(path, collab)
        answer = kwargs["intervention"]
        self.assertIsInstance(answer, workflow.Answer)
        self.assertEqual(answer.path.read_text(encoding="utf-8"), "Le critère est X.")

    def test_a_retry_call_names_the_call_it_targets(self) -> None:
        collab = self.situation("timed_out")
        action = self.action(collab, ActionId.RETRY_CALL)
        with mock.patch.object(dialogs, "prompt_text", return_value="Un motif."), \
             mock.patch.object(dialogs, "confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(_ROOT, self.controller, collab, action)
        (_,), kwargs = start_run.call_args
        retry = kwargs["intervention"]
        self.assertIsInstance(retry, workflow.RetryCall)
        self.assertEqual(retry.call_id, action.call_id)

    def test_a_reprocess_names_the_call_it_targets(self) -> None:
        collab = self.situation("contract_error")
        action = self.action(collab, ActionId.REPROCESS_AND_RESUME)
        with mock.patch.object(dialogs, "prompt_text", return_value="Un motif."), \
             mock.patch.object(dialogs, "confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(_ROOT, self.controller, collab, action)
        (_,), kwargs = start_run.call_args
        reprocess = kwargs["intervention"]
        self.assertIsInstance(reprocess, workflow.Reprocess)
        self.assertEqual(reprocess.call_id, action.call_id)

    def test_a_correction_writes_the_instruction_and_starts_a_run(self) -> None:
        collab = self.situation("accepted")
        action = self.action(collab, ActionId.CORRECT)
        with mock.patch.object(dialogs, "prompt_text", return_value="Précisez le point X."), \
             mock.patch.object(dialogs, "confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(_ROOT, self.controller, collab, action)
        (path,), kwargs = start_run.call_args
        self.assertEqual(path, collab)
        correction = kwargs["intervention"]
        self.assertIsInstance(correction, workflow.Correct)
        self.assertEqual(correction.path.read_text(encoding="utf-8"), "Précisez le point X.")


class TestResumeNeedsNoInterventionObject(InterventionCase):
    """§8.2 : reprendre un `RUNNING` persistant est local d'abord (récupération
    depuis les preuves), sans intervention à transmettre — la mécanique de
    récupération elle-même est celle de `workflow.run`, déjà éprouvée par
    `tests/test_recovery.py` ; ici, seule la route GUI est en cause."""

    def test_resuming_a_running_collaboration_starts_a_run_without_intervention(self) -> None:
        collab = self.situation("running")
        action = self.action(collab, ActionId.RESUME)
        with mock.patch.object(dialogs, "confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            intervention.run(_ROOT, self.controller, collab, action)
        start_run.assert_called_once()
        (path,), kwargs = start_run.call_args
        self.assertEqual(path, collab)
        self.assertIsNone(kwargs.get("intervention"))
