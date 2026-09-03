"""Tests de iabinome.workflow : prévol, cycle complet, transitions, frontière.

Tous les appels passent par `FakeAdapter` — aucun fournisseur, aucun réseau,
aucun coût (CONCEPTION_FINALE.md §10)."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import workflow
from iabinome.adapters.base import Capabilities
from iabinome.models import Phase, Status
from iabinome.workflow import WorkflowError
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_DOC2 = "IABINOME:DOCUMENT\n# Revision\nCorps revise."
_FINAL = "IABINOME:DOCUMENT\n# Final\nCorps final."
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"

# B reprend chaque constat antérieur exactement une fois, même pour le fermer :
# le faire disparaître est un échec de contrat (§6).
_RESOLVED = ({
    "id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED", "statement": "Manque X.",
},)


class WorkflowCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def build(self, a: tuple[str, ...], b: tuple[str, ...], **kwargs: object) -> Path:
        self.a = fakes.FakeAdapter("fake-a", a)
        self.b = fakes.FakeAdapter("fake-b", b)
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        return fakes.collaboration(self.root, **kwargs)  # type: ignore[arg-type]

    def run_engine(self, collab: Path, **kwargs: object) -> object:
        return workflow.run(
            collab, adapters=self.adapters, timeout_seconds=30.0, **kwargs  # type: ignore[arg-type]
        )

    def etat(self, collab: Path) -> dict[str, object]:
        raw = fakes.read_json(collab / "etat.json")
        assert isinstance(raw, dict)
        return raw


class TestFullCycle(WorkflowCase):
    def test_cycle_reaches_awaiting_approval(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2, _FINAL),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        state = workflow.run(collab, adapters=self.adapters, timeout_seconds=30.0)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertIs(state.phase, Phase.CLOSED)
        self.assertIsNone(state.current_call)
        self.assertEqual(state.current_document, "livrables/version_finale.md")
        self.assertEqual(self.a.calls, 3)
        self.assertEqual(self.b.calls, 2)

    def test_exchange_artifacts_are_named_and_ordered(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2, _FINAL),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        self.run_engine(collab)
        names = sorted(p.name for p in (collab / "echanges").iterdir())
        self.assertEqual(names, [
            "0001-proposition-A.md",
            "0002-critique-B.json",
            "0003-revision-1-A.md",
            "0004-critique-B.json",
        ])

    def test_final_document_opens_on_the_program_written_line(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2, _FINAL),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
            corpus_captured_at="2026-09-03",
        )
        self.run_engine(collab)
        final = (collab / "livrables" / "version_finale.md").read_text(encoding="utf-8")
        self.assertIn("n'est pas approuvé", final)
        self.assertIn("Revue B : CONSULT", final)
        self.assertIn("constats restés ouverts : 0 (dont 0 BLOCKING)", final)
        self.assertIn("corpus figé le 2026-09-03", final)
        self.assertTrue(final.endswith("Corps final."))

    def test_calling_is_published_before_popen(self) -> None:
        """Étape 4 : l'adaptateur relit `etat.json` juste avant `Popen`."""
        collab = self.build(a=(_QUESTION,), b=())
        self.run_engine(collab)
        self.assertEqual(self.a.observed_status, ["RUNNING"])
        self.assertEqual(fakes.read_json(collab / "etat.json")["status"], "WAITING_HUMAN")

    def test_intention_records_the_observed_version_not_a_provider_name(self) -> None:
        collab = self.build(a=(_QUESTION,), b=())
        self.run_engine(collab)
        call_dir = next((collab / "appels").iterdir())
        intention = fakes.read_json(call_dir / "intention.json")
        self.assertEqual(intention["observed_version"], "fake 0.1.0")
        self.assertEqual(intention["adapter_id"], "fake-a")
        self.assertIsNone(intention["retries"])
        self.assertNotIn("fake", call_dir.name.split("-")[-1])


class TestTransitions(WorkflowCase):
    def test_question_stops_before_b(self) -> None:
        collab = self.build(a=(_QUESTION,), b=(fakes.review(),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        self.assertEqual(self.b.calls, 0)
        self.assertTrue((collab / "echanges" / "0001-question-A.md").exists())

    def test_bloque_hands_back_to_the_human(self) -> None:
        collab = self.build(a=(_DOC,), b=(fakes.review("BLOQUE"),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        self.assertEqual(self.etat(collab)["open_finding_ids"], ["B-001"])

    def test_revision_limit_goes_straight_to_final(self) -> None:
        collab = self.build(
            a=(_DOC, _FINAL),
            b=(fakes.review("REVISER"),),
            max_revisions=0,
        )
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)  # type: ignore[attr-defined]
        self.assertEqual(self.a.calls, 2)

    def test_accepter_with_open_blocking_keeps_the_decision_and_hands_back(self) -> None:
        blocking = ({
            "id": "B-009", "severity": "BLOCKING", "disposition": "OPEN",
            "statement": "La reprise ne couvre pas le cas X.",
        },)
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER", findings=blocking),))
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.WAITING_HUMAN)  # type: ignore[attr-defined]
        etat = self.etat(collab)
        self.assertEqual(etat["open_finding_ids"], ["B-009"])
        # La revue est persistée telle quelle : la décision de B n'est pas réécrite.
        review = fakes.read_json(collab / "echanges" / "0002-critique-B.json")
        self.assertEqual(review["decision"], "ACCEPTER")
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "ACCEPTER_WITH_OPEN_BLOCKING")

    def test_prior_findings_reach_the_next_review(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2, _FINAL),
            b=(fakes.review("REVISER"), fakes.review("ACCEPTER", findings=_RESOLVED)),
        )
        self.run_engine(collab)
        self.assertIn("Manque X.", self.b.prompts[1])
        self.assertIn("B-001", self.b.prompts[1])


class TestContractFailure(WorkflowCase):
    def test_unknown_tag_is_an_error_with_the_raw_response_preserved(self) -> None:
        collab = self.build(a=("Bonjour, voici mon document.",), b=())
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.ERROR)  # type: ignore[attr-defined]
        call_dir = next((collab / "appels").iterdir())
        self.assertEqual(
            (call_dir / "reponse_brute.txt").read_text(encoding="utf-8"),
            "Bonjour, voici mon document.",
        )
        incident = fakes.read_json(call_dir / "incident.json")
        self.assertEqual(incident["kind"], "CONTRACT_ERROR")

    def test_lost_prior_finding_is_a_contract_error(self) -> None:
        collab = self.build(
            a=(_DOC, _DOC2),
            b=(fakes.review("REVISER"), fakes.review("REVISER", findings=())),
        )
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.ERROR)  # type: ignore[attr-defined]


class TestPreflight(WorkflowCase):
    def test_unknown_adapter_refused_before_any_mutation(self) -> None:
        collab = self.build(a=(_DOC,), b=(), adapter_a="absent")
        before = (collab / "etat.json").read_text(encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)
        self.assertEqual((collab / "etat.json").read_text(encoding="utf-8"), before)
        self.assertFalse((collab / "appels").exists())

    def test_absent_cli_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.present = False
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_context_only_refused_when_unsupported(self) -> None:
        collab = self.build(a=(_DOC,), b=(), reviewer_access="CONTEXT_ONLY")
        self.b.capabilities = Capabilities(False, True)
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)
        self.assertEqual(self.a.calls, 0)

    def test_model_override_refused_when_unsupported(self) -> None:
        collab = self.build(a=(_DOC,), b=(), model_a="autre-modele")
        self.a.capabilities = Capabilities(True, False)
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_edited_demande_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        (collab / "demande.md").write_text("Autre demande.", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_research_without_corpus_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=(), mission_kind="RECHERCHE")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)

    def test_altered_corpus_manifest_refused(self) -> None:
        collab = self.build(a=(_DOC,), b=(), corpus_captured_at="2026-09-01")
        (collab / "corpus" / "manifeste.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            self.run_engine(collab)


class TestPermutations(WorkflowCase):
    def test_the_four_couples_run_the_same_cycle(self) -> None:
        """A et B sont chacun l'un ou l'autre outil : même workflow, même contrat."""
        for id_a in ("outil-1", "outil-2"):
            for id_b in ("outil-1", "outil-2"):
                with self.subTest(a=id_a, b=id_b):
                    tmp = TemporaryDirectory()
                    self.addCleanup(tmp.cleanup)
                    a = fakes.FakeAdapter(id_a, (_DOC, _FINAL))
                    b = fakes.FakeAdapter(id_b, (fakes.review("ACCEPTER", findings=()),))
                    adapters = {id_a: a, id_b: b} if id_a != id_b else {id_a: a}
                    if id_a == id_b:
                        a.responses = [_DOC, fakes.review("ACCEPTER", findings=()), _FINAL]
                    collab = fakes.collaboration(
                        Path(tmp.name), adapter_a=id_a, adapter_b=id_b,
                        model_a=f"{id_a}-modele-a", model_b=f"{id_b}-modele-b",
                    )
                    state = workflow.run(collab, adapters=adapters, timeout_seconds=30.0)
                    self.assertIs(state.status, Status.AWAITING_APPROVAL)


class TestEffectBoundary(WorkflowCase):
    def test_a_diff_or_shell_block_stays_text(self) -> None:
        """Aucun symbole de production n'applique ni n'exécute : l'absence de
        chemin fonctionnel vaut mieux qu'une détection lexicale (§10)."""
        payload = (
            "IABINOME:DOCUMENT\n"
            "```sh\nrm -rf /\ntouch temoin.txt\n```\n"
            "```diff\n--- a\n+++ b\n```\nhttps://exemple.test/x"
        )
        collab = self.build(a=(payload,), b=(fakes.review("BLOQUE"),))
        self.run_engine(collab)
        document = (collab / "echanges" / "0001-proposition-A.md").read_text(encoding="utf-8")
        self.assertIn("rm -rf /", document)
        self.assertIn("https://exemple.test/x", document)
        self.assertFalse((collab / "temoin.txt").exists())


if __name__ == "__main__":
    unittest.main()
