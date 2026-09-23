"""GUI V1, lot 3 : la façade relit le dossier, jamais une mémoire de fenêtre
(`conception/GUI_V1.md` §3.3, §10.3). Testée sans Tk (§15.1) : elle habille
`decisions.allowed_actions` d'une présentation lisible, elle ne réinvente
aucune règle — les mêmes situations qu'au lot 1 (`tests/test_actions.py`) le
prouvent, statut par statut.
"""

from __future__ import annotations

from pathlib import Path

from iabinome import decisions, facade
from iabinome.models import Status
from tests import fakes
from tests.test_actions import ActionsCase
from tests.test_promotion import PromotionCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_DOC2 = fakes.revision()


class TestInspectionMatchesTheEngine(ActionsCase):
    def test_allowed_actions_come_straight_from_decisions(self) -> None:
        for name in (
            "ready_fresh", "ready_paused", "running", "question", "awaiting",
            "accepted", "accepted_then_changed", "stopped",
        ):
            with self.subTest(name):
                collab = self.situation(name)
                expected = decisions.allowed_actions(collab, self.state(collab))
                snapshot = facade.inspect_collaboration(collab)
                self.assertEqual(snapshot.presentation.allowed_actions, expected)

    def test_a_running_collaboration_this_gui_does_not_own_is_not_shown_as_active(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("running"))
        self.assertEqual(
            snapshot.presentation.activity_label,
            "État enregistré : appel en cours ou processus arrêté ; activité non prouvée",
        )
        self.assertFalse(snapshot.execution_observation.owned_by_this_gui)
        self.assertIsNone(snapshot.execution_observation.runner_alive)

    def test_a_running_call_owned_by_this_gui_says_a_call_is_in_progress(self) -> None:
        collab = self.situation("running")
        snapshot = facade.inspect_collaboration(collab, owned_by_this_gui=True)
        self.assertEqual(snapshot.presentation.activity_label, "Appel fournisseur en cours")

    def test_accepted_shows_the_version_accepted_substate(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("accepted"))
        self.assertEqual(snapshot.presentation.status_label, "Version acceptée")
        self.assertTrue(snapshot.current_decision.applies_to_current_version)
        self.assertEqual(snapshot.current_decision.kind, decisions.ACCEPTED)
        self.assertIsNotNone(snapshot.current_decision.version_digest)

    def test_a_changed_deliverable_makes_an_old_acceptance_not_apply(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("accepted_then_changed"))
        self.assertEqual(snapshot.presentation.status_label, "Cycle terminé — décision requise")
        self.assertFalse(snapshot.current_decision.applies_to_current_version)

    def test_awaiting_without_a_decision_says_so(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("awaiting"))
        self.assertEqual(snapshot.presentation.status_label, "Cycle terminé — décision requise")
        self.assertIsNone(snapshot.current_decision.kind)

    def test_stopped_offers_nothing(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("stopped"))
        self.assertIs(snapshot.state.status, Status.STOPPED)
        self.assertEqual(snapshot.presentation.allowed_actions, ())

    def test_an_incident_is_explained_in_the_snapshot(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("timed_out"))
        assert snapshot.incident is not None
        self.assertIn("TIMEOUT", snapshot.incident)

    def test_no_incident_when_nothing_happened(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("ready_fresh"))
        self.assertIsNone(snapshot.incident)

    def test_readable_documents_only_list_what_exists_on_disk(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("accepted"))
        for document in snapshot.presentation.readable_documents:
            self.assertTrue((snapshot.path / document).is_file())
        self.assertIn(decisions.DELIVERED, snapshot.presentation.readable_documents)

    def test_a_fresh_collaboration_has_only_the_request_to_read(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("ready_fresh"))
        self.assertEqual(snapshot.presentation.readable_documents, ("demande.md",))

    def test_an_invalid_folder_is_named_not_fixed(self) -> None:
        missing = self.root / "inexistant"
        with self.assertRaises(facade.InspectionError):
            facade.inspect_collaboration(missing)

    def test_the_runtime_timeout_is_resolved_against_the_parent_of_the_collaboration(self) -> None:
        snapshot = facade.inspect_collaboration(self.situation("ready_fresh"))
        self.assertGreater(snapshot.runtime_resolution.timeout_seconds, 0)
        self.assertTrue(snapshot.runtime_resolution.origin)


class TestPhaseSteps(PromotionCase):
    def steps(self, collab: Path) -> dict[str, str]:
        snapshot = facade.inspect_collaboration(collab)
        return {label: symbol for symbol, label in snapshot.presentation.phase_steps}

    def test_an_immediate_acceptance_never_runs_a_revision(self) -> None:
        collab = self.cycle((_DOC,), (fakes.review("ACCEPTER"),))
        steps = self.steps(collab)
        self.assertEqual(steps["Proposition A"], "✓")
        self.assertEqual(steps["Critique B"], "✓")
        self.assertEqual(steps["Révision A"], "—")
        self.assertEqual(steps["Clôture"], "✓")

    def test_a_revision_that_ran_is_marked_done_once_closed(self) -> None:
        resolved = ({
            "id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED", "statement": "Manque X.",
        },)
        collab = self.cycle(
            (_DOC, _DOC2), (fakes.review("REVISER"), fakes.review("ACCEPTER", findings=resolved)),
        )
        steps = self.steps(collab)
        self.assertEqual(steps["Révision A"], "✓")

    def test_the_current_phase_of_a_running_cycle_is_marked_current(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        by_label = self.steps(collab)
        self.assertEqual(by_label["Proposition A"], "●")
        self.assertEqual(by_label["Critique B"], "○")

    def test_a_blocked_current_phase_is_marked_stopped(self) -> None:
        collab = self.cycle(("IABINOME:QUESTION\nQuel est le critere de fin ?",), ())
        self.assertEqual(self.steps(collab)["Proposition A"], "!")
