"""GUI V1, lot 3 : la façade relit le dossier, jamais une mémoire de fenêtre
(`conception/GUI_V1.md` §3.3, §10.3). Testée sans Tk (§15.1) : elle habille
`decisions.allowed_actions` d'une présentation lisible, elle ne réinvente
aucune règle — les mêmes situations qu'au lot 1 (`tests/test_actions.py`) le
prouvent, statut par statut.
"""

from __future__ import annotations

from pathlib import Path

from iabinome import decisions, facade, workflow
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


class TestProgress(PromotionCase):
    """Retour d'usage du 2026-09-28 : agent actif, étape courante, étapes faites,
    numéro de révision et attente humaine — lisibles quel que soit l'outil."""

    def progress(self, collab: Path) -> facade.Progress:
        return facade.inspect_collaboration(collab).presentation.progress

    def grid(self, collab: Path) -> list[tuple[str, str]]:
        return [
            (f"{a.symbol} {a.label}", f"{b.symbol} {b.label}")
            for a, b in self.progress(collab).rounds
        ]

    def test_an_immediate_acceptance_shows_one_round_and_waits_for_the_human(self) -> None:
        collab = self.cycle((_DOC,), (fakes.review("ACCEPTER"),))
        progress = self.progress(collab)
        self.assertEqual(self.grid(collab), [("✓ Proposition", "✓ Critique")])
        self.assertEqual(progress.human, facade.Step("●", "Décision : à prendre"))
        self.assertTrue(progress.now.startswith("À vous"))

    def test_each_column_names_its_role_tool_and_model(self) -> None:
        progress = self.progress(self.build(a=(_DOC,), b=()))
        config = facade.inspect_collaboration(self.build(a=(), b=())).configuration
        self.assertEqual(
            progress.agent_a, f"A · {config.agent_a.adapter_id} ({config.agent_a.model})",
        )
        self.assertTrue(progress.agent_b.startswith("B · "))

    def test_an_acceptance_closes_the_human_step(self) -> None:
        collab = self.cycle((_DOC,), (fakes.review("ACCEPTER"),))
        workflow.decide(collab, decisions.ACCEPTED)
        progress = self.progress(collab)
        self.assertEqual(progress.human.symbol, "✓")
        self.assertEqual(progress.now, "Terminé : version acceptée.")

    def test_a_revision_that_ran_is_marked_done_once_closed(self) -> None:
        resolved = ({
            "id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED", "statement": "Manque X.",
        },)
        collab = self.cycle(
            (_DOC, _DOC2), (fakes.review("REVISER"), fakes.review("ACCEPTER", findings=resolved)),
        )
        self.assertEqual(
            self.grid(collab),
            [("✓ Proposition", "✓ Critique"), ("✓ Révision 1", "✓ Relecture 1")],
        )

    def test_a_fresh_collaboration_announces_conditional_revisions_up_to_the_cap(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        cap = facade.inspect_collaboration(collab).configuration.max_revisions
        grid = self.grid(collab)
        self.assertEqual(len(grid), cap + 1)
        self.assertEqual(grid[0], ("● Proposition", "○ Critique"))
        self.assertEqual(grid[1], ("○ Révision 1 (si B la demande)", "○ Relecture 1"))
        self.assertTrue(self.progress(collab).now.startswith("Prête : au démarrage, Proposition"))

    def test_a_question_marks_the_current_step_and_says_who_waits(self) -> None:
        collab = self.cycle(("IABINOME:QUESTION\nQuel est le critere de fin ?",), ())
        progress = self.progress(collab)
        self.assertEqual(progress.rounds[0][0], facade.Step("!", "Proposition"))
        self.assertEqual(progress.now, "À vous : A pose une question (Proposition).")

    def test_a_failed_call_points_to_its_trace_and_names_the_tool(self) -> None:
        collab = self.build(a=("ERROR: modele inconnu",), b=())
        self.a.exit_codes = [1]
        self.run_engine(collab)
        snapshot = facade.inspect_collaboration(collab)
        trace = snapshot.presentation.trace_dir
        self.assertIsNotNone(trace)
        self.assertIn(f"{trace}/stdout.txt", snapshot.presentation.readable_documents)
        self.assertNotIn(f"{trace}/stderr.txt", snapshot.presentation.readable_documents)
        self.assertEqual(snapshot.presentation.progress.rounds[0][0].symbol, "!")
        self.assertIn("n'a pas abouti (Proposition)", snapshot.presentation.progress.now)

    def test_no_trace_is_offered_when_nothing_failed(self) -> None:
        snapshot = facade.inspect_collaboration(self.cycle((_DOC,), (fakes.review("ACCEPTER"),)))
        self.assertIsNone(snapshot.presentation.trace_dir)
        self.assertFalse(
            [d for d in snapshot.presentation.readable_documents if d.startswith("appels/")]
        )
