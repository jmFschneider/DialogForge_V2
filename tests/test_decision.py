"""Tests du lot 1, point 1.4 : le résultat se lit, et l'humain décide.

Validation du plan : **un parcours complet avec faux agents est réalisable sans
copier-coller les réponses entre conversations ; les artefacts restent lisibles
hors du logiciel.**

« Terminé » n'est pas « accepté » : le cycle s'arrête en `AWAITING_APPROVAL`, et
l'acceptation est une décision de l'humain, datée, portant sur une version précise.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from iabinome import cli, decisions, demande, facade, planlink, settings, workflow
from iabinome.models import State, Status
from tests import fakes
from tests.test_objections import finding, reply, review_v2
from tests.test_promotion import PromotionCase, revision
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"


class _Stop(RuntimeError):
    """Arrêt injecté — simule la mort du processus entre deux écritures."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DecisionCase(PromotionCase):
    def clean(self) -> Path:
        """Un cycle terminé sans objection : `AWAITING_APPROVAL`, rien d'accepté."""
        return self.cycle((_DOC,), (review_v2("ACCEPTER"),))

    def with_disagreement(self) -> Path:
        """Un cycle terminé au plafond, avec `B-001` resté ouvert."""
        return self.cycle((_DOC,), (review_v2("REVISER", finding()),), max_revisions=0)

    def state(self, collab: Path) -> State:
        return State.from_dict(fakes.read_json(collab / "etat.json"))

    def decide(self, collab: Path, kind: str, **kwargs: str) -> State:
        return workflow.decide(collab, kind, **kwargs)

    def refused(self, collab: Path, kind: str, **kwargs: str) -> str:
        try:
            self.decide(collab, kind, **kwargs)
        except workflow.WorkflowError as exc:
            return str(exc)
        self.fail("aucun refus")


class TestAcceptanceIsADecisionNotAStatus(DecisionCase):
    def test_a_finished_cycle_is_not_accepted_and_says_so(self) -> None:
        collab = self.clean()
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertIsNone(decisions.latest(collab))
        self.assertIn("il n'est pas accepté", decisions.describe(collab, self.state(collab)))

    def test_accepting_records_a_dated_decision_on_the_precise_version(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        (entry,) = decisions.read(collab)
        self.assertEqual(entry["decision"], "ACCEPTE")
        self.assertRegex(entry["at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        version = entry["version"]
        delivered = collab / "livrables" / "version_finale.md"
        self.assertEqual(version["livrable_sha256"], sha(delivered))
        self.assertEqual(version["revue_sha256"], sha(collab / version["revue"]))
        self.assertEqual(version["demande_sha256"], self.state(collab).demande_sha256)

    def test_the_engine_status_does_not_change_when_the_human_accepts(self) -> None:
        collab = self.clean()
        before = (collab / "etat.json").read_bytes()
        self.decide(collab, decisions.ACCEPTED)
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertIn("acceptée le", decisions.describe(collab, self.state(collab)))

    def test_a_result_is_never_accepted_twice(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        self.assertIn("déjà accepté", self.refused(collab, decisions.ACCEPTED))
        self.assertEqual(len(decisions.read(collab)), 1)

    def test_nothing_is_accepted_before_the_cycle_is_over(self) -> None:
        collab = self.cycle((_QUESTION,), ())
        self.assertEqual(self.status(collab), "WAITING_HUMAN")
        message = self.refused(collab, decisions.ACCEPTED)
        self.assertIn("WAITING_HUMAN", message)
        self.assertEqual(decisions.read(collab), [], "une décision a été consignée à tort")

    def test_a_decision_recorded_twice_by_a_replay_stays_single(self) -> None:
        collab = self.clean()
        state = self.state(collab)
        decisions.record(collab, decisions.ACCEPTED, state)
        decisions.record(collab, decisions.ACCEPTED, state)
        self.assertEqual(len(decisions.read(collab)), 1)


class TestReserves(DecisionCase):
    def test_acceptance_with_reserves_needs_the_reserves(self) -> None:
        collab = self.with_disagreement()
        self.assertIn("exige le texte", self.refused(collab, decisions.ACCEPTED_WITH_RESERVES))
        self.assertIn(
            "exige le texte",
            self.refused(collab, decisions.ACCEPTED_WITH_RESERVES, reserves="   "),
        )
        self.assertEqual(decisions.read(collab), [])

    def test_the_reserves_are_kept_and_shown_beside_the_open_objections(self) -> None:
        collab = self.with_disagreement()
        self.decide(collab, decisions.ACCEPTED_WITH_RESERVES, reserves="À revoir avec le PO.")
        latest = decisions.latest(collab)
        assert latest is not None
        self.assertEqual(latest["reserves"], "À revoir avec le PO.")
        shown = decisions.render(collab, self.state(collab), with_document=False)
        reserves = shown.split("Réserves :")[1].split("Prochaine action")[0]
        self.assertIn("B-001", reserves)
        self.assertIn("de l'humain : À revoir avec le PO.", reserves)
        self.assertIn("acceptée avec réserves", shown)


class TestADecisionIsAboutOneVersion(DecisionCase):
    def test_a_livrable_changed_after_the_decision_is_flagged(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        state = self.state(collab)
        self.assertNotIn("antérieure", decisions.describe(collab, state))
        delivered = collab / "livrables" / "version_finale.md"
        changed = delivered.read_text(encoding="utf-8") + "\nModifié.\n"
        delivered.write_text(changed, encoding="utf-8")
        self.assertIn("porte sur une version antérieure", decisions.describe(collab, state))
        self.assertNotIn("le résultat est accepté", decisions.next_action(collab, state))

    def test_a_correction_leaves_the_earlier_acceptance_about_the_earlier_version(self) -> None:
        collab = self.with_disagreement()
        first = sha(collab / "livrables" / "version_finale.md")
        self.decide(collab, decisions.ACCEPTED_WITH_RESERVES, reserves="Réserve.")
        instruction = self.root / "correction.md"
        instruction.write_text("Traite B-001.", encoding="utf-8")
        self.a.responses = [revision(reply())]
        self.b.responses = [review_v2("ACCEPTER", finding(disposition="RESOLVED",
                                                          justification="Corrigé."))]
        self.run_engine(collab, command_label="decide", intervention=workflow.Correct(instruction))
        entries = decisions.read(collab)
        self.assertEqual([e["decision"] for e in entries],
                         ["ACCEPTE_AVEC_RESERVES", "CORRECTION_CIBLEE"])
        self.assertEqual(entries[0]["version"]["livrable_sha256"], first)
        self.assertNotEqual(sha(collab / "livrables" / "version_finale.md"), first)
        state = self.state(collab)
        # La dernière décision est la correction, et elle porte sur la version d'avant :
        # le nouveau livrable n'est accepté par personne.
        described = decisions.describe(collab, state)
        self.assertIn("correction ciblée demandée", described)
        self.assertIn("porte sur une version antérieure", described)
        self.assertNotIn("le résultat est accepté", decisions.next_action(collab, state))
        self.assertIn("--accept", decisions.next_action(collab, state))


class TestAnAcceptanceNeedsItsArtifactsOnDisk(DecisionCase):
    """Audit du 2026-09-25, F01 et F02 : une acceptation porte sur un livrable, une
    revue et une demande **présents sur le disque**, la demande relue et non reprise
    de l'état. Chaque cas est joué sur une copie du même cycle terminé."""

    # (artefact, altération) → ce que le diagnostic doit nommer
    _EXPECTED = {
        ("livrable", "absent"): "livrable absent",
        ("livrable", "modifié"): "le livrable a changé",
        ("revue", "absent"): "revue absente",
        ("revue", "modifié"): "la revue a changé",
        ("demande", "absent"): "demande.md absente",
        ("demande", "modifié"): "la demande a changé",
    }

    def setUp(self) -> None:
        super().setUp()
        patcher = mock.patch.object(settings, "SEARCH_PATHS", ())
        patcher.start()
        self.addCleanup(patcher.stop)

    def copies(self, *, accept: bool) -> list[tuple[str, Path, str, bool]]:
        """Une copie par altération, avec le diagnostic attendu et si une nouvelle
        acceptation doit être refusée : un livrable ou une revue modifiés mais
        présents sont une autre version, qu'on peut accepter ; une absence ou une
        demande qui ne correspond plus à l'état ne le sont pas."""
        base = self.clean()
        if accept:
            self.decide(base, decisions.ACCEPTED)
        found = []
        for (artifact, how), expected in self._EXPECTED.items():
            copy = Path(shutil.copytree(base, self.root / f"{artifact}-{how}"))
            self.alter(copy, artifact, how)
            refused = how == "absent" or artifact == "demande"
            found.append((f"{artifact} {how}", copy, expected, refused))
        return found

    def alter(self, collab: Path, artifact: str, how: str) -> None:
        path = {
            "livrable": collab / decisions.DELIVERED,
            "revue": collab / str(self.state(collab).latest_review),
            "demande": collab / "demande.md",
        }[artifact]
        if how == "absent":
            path.rename(path.with_name(path.name + ".audit-backup"))
        elif artifact == "revue":  # une revue modifiée qui reste un JSON valide
            path.write_text(json.dumps(json.loads(path.read_text(encoding="utf-8"))),
                            encoding="utf-8")
        else:
            path.write_bytes(path.read_bytes() + b"\nAjout hors cycle.\n")

    def run_cli(self, *argv: str) -> tuple[int, str]:
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = cli.main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def test_an_absence_or_a_changed_demande_is_refused_and_nothing_recorded(self) -> None:
        for case, collab, expected, refused in self.copies(accept=False):
            if not refused:
                continue
            with self.subTest(case):
                self.assertIn(expected, self.refused(collab, decisions.ACCEPTED))
                self.assertIn(expected, self.refused(
                    collab, decisions.ACCEPTED_WITH_RESERVES, reserves="Réserve."))
                code, out = self.run_cli("decide", str(collab), "--accept")
                self.assertEqual(code, 1)
                self.assertIn(expected, out)
                self.assertEqual(decisions.read(collab), [])

    def test_an_earlier_acceptance_no_longer_applies_wherever_it_is_shown(self) -> None:
        for case, collab, expected, refused in self.copies(accept=True):
            with self.subTest(case):
                state = self.state(collab)
                self.assertFalse(decisions.accepted(collab, state))
                described = decisions.describe(collab, state)
                self.assertIn(f"porte sur une version antérieure : {expected}", described)
                self.assertNotIn("le résultat est accepté", decisions.next_action(collab, state))
                snapshot = facade.inspect_collaboration(collab)
                self.assertEqual(snapshot.presentation.status_label,
                                 "Cycle terminé — décision requise")
                self.assertIn(expected, snapshot.current_decision.discrepancies)
                self.assertIn(f"  Décision : {described}.", planlink.summary(collab))
                for command in ("status", "show"):
                    code, out = self.run_cli(command, str(collab))
                    self.assertEqual(code, 0, out)
                    self.assertIn(expected, out)
                    self.assertNotIn("le résultat est accepté", out)
                if refused:
                    self.assertIn(expected, self.refused(collab, decisions.ACCEPTED))
                    self.assertEqual(len(decisions.read(collab)), 1, "l'ancienne est gardée")
                else:  # une autre version, présente : elle s'accepte explicitement
                    self.decide(collab, decisions.ACCEPTED)
                    self.assertEqual(len(decisions.read(collab)), 2)
                    self.assertTrue(decisions.accepted(collab, self.state(collab)))

    def test_an_artifact_put_back_makes_the_acceptance_apply_again(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        delivered = collab / decisions.DELIVERED
        delivered.rename(delivered.with_name("mis-de-cote"))
        self.assertFalse(decisions.accepted(collab, self.state(collab)))
        delivered.with_name("mis-de-cote").rename(delivered)
        self.assertTrue(decisions.accepted(collab, self.state(collab)))

    def test_an_acceptance_recorded_without_a_livrable_is_not_an_acceptance(self) -> None:
        collab = self.clean()
        (collab / decisions.DELIVERED).unlink()
        state = self.state(collab)
        decisions.record(collab, decisions.ACCEPTED, state)  # ce qu'écrivait `decide` avant
        self.assertIsNone(decisions.read(collab)[0]["version"]["livrable_sha256"])
        self.assertFalse(decisions.accepted(collab, state))
        self.assertIn("livrable absent", decisions.describe(collab, state))

    def test_the_demande_is_read_with_the_engine_normalization(self) -> None:
        collab = self.clean()
        path = collab / "demande.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes().replace(b"\n", b"\r\n"))
        self.decide(collab, decisions.ACCEPTED)
        self.assertTrue(decisions.accepted(collab, self.state(collab)))

    def test_a_stop_needs_no_livrable(self) -> None:
        collab = self.clean()
        (collab / decisions.DELIVERED).unlink()
        self.assertIs(self.decide(collab, decisions.STOPPED).status, Status.STOPPED)


class TestStop(DecisionCase):
    def test_stopping_a_finished_cycle_is_final(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.STOPPED, reason="Plus utile.")
        self.assertEqual(self.status(collab), "STOPPED")
        entry = decisions.latest(collab)
        assert entry is not None
        self.assertEqual((entry["decision"], entry["reason"]), ("ARRET", "Plus utile."))
        self.assertIn("arrêtée le", decisions.describe(collab, self.state(collab)))

    def test_a_stopped_collaboration_cannot_be_run_accepted_or_stopped_again(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.STOPPED)
        with self.assertRaises(workflow.WorkflowError) as run_refused:
            self.run_engine(collab)
        self.assertIn("arrêtée par décision humaine", str(run_refused.exception))
        self.assertIn("STOPPED", self.refused(collab, decisions.ACCEPTED))
        self.assertIn("STOPPED", self.refused(collab, decisions.STOPPED))
        self.assertEqual(self.b.calls, 1, "un appel a été payé après l'arrêt")

    def test_a_waiting_collaboration_can_be_abandoned(self) -> None:
        collab = self.cycle((_QUESTION,), ())
        self.decide(collab, decisions.STOPPED)
        self.assertEqual(self.status(collab), "STOPPED")

    def test_an_interrupted_collaboration_can_be_abandoned_and_keeps_its_evidence(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.sleep_seconds = 5.0
        workflow.run(collab, adapters=self.adapters, timeout_seconds=0.05)
        self.assertEqual(self.status(collab), "INTERRUPTED")
        self.decide(collab, decisions.STOPPED)
        self.assertEqual(self.status(collab), "STOPPED")
        self.assertTrue(any((collab / "appels").iterdir()), "la preuve de l'appel a disparu")


class TestCorrectionCiblee(DecisionCase):
    """Le tour supplémentaire demandé après le plafond : explicite et tracé."""

    def instruction(self, text: str = "Ajoute la limite Z.") -> Path:
        path = self.root / "correction.md"
        path.write_text(text, encoding="utf-8")
        return path

    def correct(self, collab: Path) -> None:
        self.a.responses = [revision(reply(justification=""))]
        self.b.responses = [review_v2("ACCEPTER", finding(disposition="RESOLVED",
                                                          justification="Corrigé."))]
        self.run_engine(collab, command_label="decide",
                        intervention=workflow.Correct(self.instruction()))

    def test_the_extra_round_starts_from_the_livrable_body_and_the_human_instruction(self) -> None:
        collab = self.with_disagreement()
        self.correct(collab)
        prompt = self.a.prompts[1]
        self.assertIn("Ajoute la limite Z.", prompt)
        self.assertIn("# Proposition", prompt)
        self.assertNotIn("n'est pas approuvé", prompt, "l'en-tête du programme est passé à A")

    def test_the_round_goes_beyond_the_cap_and_is_traced(self) -> None:
        collab = self.with_disagreement()
        self.assertEqual(self.state(collab).revision, 0)
        self.correct(collab)
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual(self.state(collab).revision, 1, "le tour de plus n'a pas eu lieu")
        entry = decisions.latest(collab)
        assert entry is not None
        self.assertEqual((entry["decision"], entry["extra_round"]), ("CORRECTION_CIBLEE", 1))
        self.assertIn("Corrections ciblées demandées par l'humain : 1", self.bilan(collab))

    def test_the_instruction_completes_the_demande_and_never_replaces_it(self) -> None:
        collab = self.with_disagreement()
        before = (collab / "demande.md").read_text(encoding="utf-8")
        self.correct(collab)
        after = (collab / "demande.md").read_text(encoding="utf-8")
        self.assertTrue(after.startswith(before.rstrip()))
        self.assertIn("## Précisions n°1\n\nAjoute la limite Z.", after)
        self.assertEqual((collab / "demande.md.001").read_text(encoding="utf-8"), before)
        (only,) = demande.read(collab)
        self.assertEqual(only["source"], "correction")

    def test_the_relecture_after_it_is_targeted_and_sees_the_answers(self) -> None:
        collab = self.with_disagreement()
        self.correct(collab)
        self.assertIn("relecture ciblée", self.b.prompts[1])
        self.assertIn("Réponse de A : CORRIGE", self.b.prompts[1])

    def test_only_a_delivered_result_can_be_corrected(self) -> None:
        collab = self.cycle((_QUESTION,), ())
        with self.assertRaises(workflow.WorkflowError) as refused:
            self.run_engine(collab, command_label="decide",
                            intervention=workflow.Correct(self.instruction()))
        self.assertIn("résultat livré", str(refused.exception))
        self.assertEqual(self.a.calls, 1, "un appel a été payé pour une correction refusée")

    def test_a_stop_during_the_correction_is_replayed_without_a_second_round_or_decision(
        self,
    ) -> None:
        collab = self.with_disagreement()
        self.a.responses = [revision(reply())]
        self.b.responses = [review_v2("ACCEPTER", finding(disposition="RESOLVED",
                                                          justification="Corrigé."))]
        instruction = self.instruction()
        with mock.patch.object(decisions, "record", side_effect=_Stop("arret injecte")):
            with self.assertRaises(_Stop):
                self.run_engine(collab, command_label="decide",
                                intervention=workflow.Correct(instruction))
        # La demande est déjà complétée, mais l'état ne dit pas encore rien de la correction.
        self.assertIn("Précisions n°1", (collab / "demande.md").read_text(encoding="utf-8"))
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")

        self.run_engine(collab, command_label="decide", intervention=workflow.Correct(instruction))

        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        text = (collab / "demande.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Précisions n°"), 1, "l'instruction a été ajoutée deux fois")
        corrections = [d for d in decisions.read(collab) if d["decision"] == "CORRECTION_CIBLEE"]
        self.assertEqual(len(corrections), 1)
        self.assertEqual(self.a.calls, 2, "la reprise a rejoué un appel")


class TestWhatTheHumanReads(DecisionCase):
    def corrected(self) -> Path:
        return self.cycle(
            (_DOC, revision(reply(justification="Section ajoutée."))),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER", finding(disposition="RESOLVED", justification="Bien traité."))),
        )

    def test_the_result_shows_corrections_reserves_next_action_and_the_document(self) -> None:
        collab = self.corrected()
        shown = decisions.render(collab, self.state(collab), with_document=True)
        for heading in ("Décision :", "Corrections principales :", "Réserves :",
                        "Prochaine action :", "--- Document"):
            self.assertIn(heading, shown)
        fixed = shown.split("Corrections principales :")[1].split("Réserves :")[0]
        self.assertIn("B-001", fixed)
        self.assertIn("A : Section ajoutée.", fixed)
        self.assertIn("B : Bien traité.", fixed)
        self.assertIn("aucune", shown.split("Réserves :")[1].split("Prochaine")[0])
        delivered = (collab / "livrables" / "version_finale.md").read_text(encoding="utf-8")
        self.assertTrue(shown.rstrip("\n").endswith(delivered.rstrip("\n")))

    def test_the_document_can_be_left_out(self) -> None:
        collab = self.corrected()
        shown = decisions.render(collab, self.state(collab), with_document=False)
        self.assertNotIn("--- Document", shown)
        self.assertIn("Prochaine action :", shown)

    def test_open_objections_are_the_reserves(self) -> None:
        collab = self.with_disagreement()
        shown = decisions.render(collab, self.state(collab), with_document=False)
        self.assertIn("- B-001 [MAJOR] Manque X.", shown.split("Réserves :")[1])
        self.assertIn("aucune objection n'a été corrigée", shown)

    def test_a_cycle_that_is_not_over_shows_no_document_and_a_next_action(self) -> None:
        collab = self.cycle((_QUESTION,), ())
        shown = decisions.render(collab, self.state(collab), with_document=True)
        self.assertNotIn("--- Document", shown)
        self.assertNotIn("Corrections principales", shown)
        self.assertIn("la question de A", shown)


class TestNextAction(DecisionCase):
    def action(self, collab: Path) -> str:
        return decisions.next_action(collab, self.state(collab))

    def test_a_finished_cycle_names_the_four_decisions(self) -> None:
        text = self.action(self.clean())
        for option in ("--accept", "--accept-with-reserves", "--correct", "--stop", "bilan.md"):
            self.assertIn(option, text)

    def test_an_accepted_result_asks_for_nothing(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        self.assertIn("aucune : le résultat est accepté", self.action(collab))

    def test_a_question_points_at_the_question_and_the_answer_command(self) -> None:
        collab = self.cycle((_QUESTION,), ())
        text = self.action(collab)
        self.assertIn("echanges/0001-question-A.md", text)
        self.assertIn("resume --answer", text)

    def test_an_interruption_names_the_call_and_says_it_may_have_been_paid(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.sleep_seconds = 5.0
        workflow.run(collab, adapters=self.adapters, timeout_seconds=0.05)
        call_id = self.state(collab).current_call.call_id  # type: ignore[union-attr]
        text = self.action(collab)
        self.assertIn(call_id, text)
        self.assertIn("a pu être payé", text)
        self.assertIn("--retry-call", text)
        self.assertIn("--reason-file", text)

    def test_an_error_names_the_kind_and_where_the_raw_answer_is(self) -> None:
        collab = self.cycle(("Bonjour, voici mon document.",), ())
        text = self.action(collab)
        self.assertIn("CONTRACT_ERROR", text)
        self.assertIn("appels/", text)
        incident = decisions.incident_line(collab, self.state(collab))
        assert incident is not None
        self.assertTrue(incident.startswith("CONTRACT_ERROR"))

    def test_a_stopped_collaboration_asks_for_nothing(self) -> None:
        collab = self.clean()
        self.decide(collab, decisions.STOPPED)
        self.assertIn("arrêtée par décision humaine", self.action(collab))

    def test_a_ready_collaboration_says_to_run(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.assertIn("run", self.action(collab))


class TestTheCommandLine(WorkflowCase):
    """Le parcours complet, par les vraies commandes, sans copier-coller."""

    def setUp(self) -> None:
        super().setUp()
        self.demande = self.root / "demande-source.md"
        self.demande.write_text(fakes.DEMANDE_COMPLETE, encoding="utf-8")
        self.collab = self.root / "collaboration"
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", ())
        for patcher in (
            mock.patch.object(cli, "ADAPTERS", {"fake-a": self.a, "fake-b": self.b}),
            mock.patch.object(settings, "SEARCH_PATHS", ()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def new(self) -> None:
        code, _, _ = self.run_cli(
            "new", str(self.collab), "--demande", str(self.demande),
            "--kind", "recherche", "--web-access",
            "--reviewer-access", "consult", "--agent-a", "fake-a", "--agent-b", "fake-b",
            "--max-revisions", "0",
        )
        self.assertEqual(code, 0)

    def test_a_complete_journey_from_the_request_to_the_accepted_result(self) -> None:
        self.new()
        self.a.responses = [_DOC]
        self.b.responses = [review_v2("REVISER", finding())]
        self.assertEqual(self.run_cli("run", str(self.collab))[0], 0)

        code, out, _ = self.run_cli("show", str(self.collab))
        self.assertEqual(code, 0)
        self.assertIn("il n'est pas accepté", out)
        self.assertIn("- B-001 [MAJOR] Manque X.", out)
        self.assertIn("# Proposition", out)

        code, out, _ = self.run_cli("decide", str(self.collab), "--accept-with-reserves",
                                    "B-001 reste ouvert.")
        self.assertEqual((code, "acceptée avec réserves" in out), (0, True))

        code, out, _ = self.run_cli("status", str(self.collab), "--json")
        self.assertEqual(code, 0)
        self.assertIn("acceptée avec réserves", out)
        self.assertIn('"next_action": "aucune : le résultat est accepté"', out)

    def test_a_targeted_correction_through_decide_runs_the_engine(self) -> None:
        self.new()
        self.a.responses = [_DOC]
        self.b.responses = [review_v2("REVISER", finding())]
        self.run_cli("run", str(self.collab))
        instruction = self.root / "correction.md"
        instruction.write_text("Traite B-001 et cite la source.", encoding="utf-8")
        self.a.responses = [revision(reply())]
        self.b.responses = [review_v2("ACCEPTER", finding(disposition="RESOLVED",
                                                          justification="Corrigé."))]
        code, out, _ = self.run_cli("decide", str(self.collab), "--correct", str(instruction))
        self.assertEqual(code, 0, out)
        self.assertIn("AWAITING_APPROVAL", out)
        self.assertIn("cite la source", self.a.prompts[1])
        self.assertEqual(decisions.corrections(self.collab), 1)

    def test_one_decision_at_a_time_and_a_reason_only_with_a_stop(self) -> None:
        self.new()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as none:
            cli.main(["decide", str(self.collab)])
        self.assertEqual(none.exception.code, 2)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as both:
            cli.main(["decide", str(self.collab), "--accept", "--stop"])
        self.assertEqual(both.exception.code, 2)
        code, _, err = self.run_cli("decide", str(self.collab), "--accept", "--reason", "x")
        self.assertEqual(code, 1)
        self.assertIn("--reason ne vaut qu'avec --stop", err)

    def test_a_refused_decision_is_a_readable_refusal_not_a_traceback(self) -> None:
        self.new()
        code, _, err = self.run_cli("decide", str(self.collab), "--accept")
        self.assertEqual(code, 1)
        self.assertIn("erreur :", err)
        self.assertIn("READY", err)

    def test_stop_from_the_command_line(self) -> None:
        self.new()
        code, out, _ = self.run_cli("decide", str(self.collab), "--stop", "--reason", "Abandon.")
        self.assertEqual(code, 0)
        self.assertIn("arrêtée", out)
        code, _, err = self.run_cli("run", str(self.collab))
        self.assertEqual(code, 1)
        self.assertIn("STOPPED", err)


class TestListingComesFromTheFolders(WorkflowCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = mock.patch.object(settings, "SEARCH_PATHS", ())
        patcher.start()
        self.addCleanup(patcher.stop)

    def snapshot(self) -> list[str]:
        return sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*"))

    def make(self, name: str) -> Path:
        base = self.root / name
        base.mkdir()
        collab = fakes.collaboration(base)
        collab.rename(self.root / f"c-{name}")
        base.rmdir()
        return self.root / f"c-{name}"

    def test_the_list_is_computed_from_the_folders_and_creates_nothing(self) -> None:
        self.make("un")
        self.make("deux")
        (self.root / "pas-une-collaboration").mkdir()
        broken = self.root / "cassee"
        broken.mkdir()
        (broken / "etat.json").write_text("{ pas du json", encoding="utf-8")
        before = self.snapshot()
        with redirect_stdout(io.StringIO()) as out:
            code = cli.main(["list", str(self.root)])
        self.assertEqual(code, 0)
        listing = out.getvalue()
        self.assertIn("c-un  READY", listing)
        self.assertIn("c-deux  READY", listing)
        self.assertIn("cassee  illisible", listing)
        self.assertNotIn("pas-une-collaboration", listing)
        self.assertEqual(self.snapshot(), before, "la commande a écrit quelque chose")

    def test_an_empty_or_missing_folder_is_said_plainly(self) -> None:
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(["list", str(self.root)]), 0)
        self.assertIn("aucune collaboration", out.getvalue())
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main(["list", str(self.root / "absent")]), 1)
        self.assertIn("n'est pas un dossier", err.getvalue())

    def test_the_decision_of_each_collaboration_is_in_the_list(self) -> None:
        collab = self.make("fin")
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (review_v2("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        workflow.decide(collab, decisions.ACCEPTED)
        with redirect_stdout(io.StringIO()) as out:
            cli.main(["list", str(self.root)])
        self.assertRegex(
            out.getvalue(),
            r"c-fin  AWAITING_APPROVAL  CLOSED  révision 0  décision : acceptée le ",
        )
        self.assertTrue(re.search(r"livrable [0-9a-f]{12}", out.getvalue()))
