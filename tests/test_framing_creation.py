"""Tests de `new --cadrer-avec-agent` de bout en bout (`conception/CADRAGE_AGENT.md` §2.6,
§3, §9, §14.1, §14.4 à §14.6, §14.8 ; lot 3 de la phase 6) : refus avant tout appel,
relecture avant création, artefacts `cadrage/`, provenances, et un cycle A/B qui ne
voit jamais le cadrage.

`cli.ADAPTERS` est substitué par des `FakeAdapter`, `input` par une liste de saisies :
jamais un fournisseur, jamais un terminal réel."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import cli, contracts, framing, settings
from tests import fakes
from tests.test_framing import DRAFT_OUT, QUESTION_OUT, READY_OUT

_SECRET = "reponse-jamais-dans-la-demande"


class FramingCliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.collab = self.root / "collaboration"
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", ())
        self.f = fakes.FakeAdapter("fake-f", ())
        for patcher in (
            mock.patch.object(cli, "ADAPTERS", {"fake-a": self.a, "fake-b": self.b,
                                                "fake-f": self.f}),
            mock.patch.object(settings, "SEARCH_PATHS", ()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.roots: list[Path] = []
        real_prepare = framing.prepare

        def prepare(*args: Any, **kwargs: Any) -> Path:
            self.roots.append(real_prepare(*args, **kwargs))
            self.addCleanup(shutil.rmtree, self.roots[-1], ignore_errors=True)
            return self.roots[-1]
        prepared = mock.patch.object(framing, "prepare", prepare)
        prepared.start()
        self.addCleanup(prepared.stop)

    def new(self, inputs: list[Any], *replies: Any, extra: tuple[str, ...] = (),
            kind: str = "conception") -> int:
        self.f.framing_responses = list(replies)
        argv = [
            "new", str(self.collab), "--cadrer-avec-agent", "--agent-cadrage", "fake-f",
            "--kind", kind, "--reviewer-access", "consult", "--agent-a", "fake-a",
            "--agent-b", "fake-b", *extra,
        ]
        with mock.patch("builtins.input", side_effect=inputs), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            return cli.main(argv)

    def sources(self) -> tuple[str, ...]:
        project = self.root / "projet"
        project.mkdir()
        (project / "note.md").write_text("contenu du projet", encoding="utf-8")
        (self.root / "liste.txt").write_text("note.md\n", encoding="utf-8")
        return ("--source-root", str(project), "--source-list", str(self.root / "liste.txt"))

    def read_json(self, *parts: str) -> Any:
        return json.loads(self.collab.joinpath(*parts).read_text(encoding="utf-8"))


# Idée, réponse à la question, « rédiger » sur la proposition, « valider » le brouillon.
NOMINAL = ["Un cache pour FloraPi", ".", _SECRET, ".", "r", "v"]


class TestNominal(FramingCliCase):
    def test_the_reviewed_draft_becomes_the_demande(self) -> None:
        """Tests 43, 44, 52, 57, 58, 60, 61, 63, 64, 76 ; critères 15, 16, 20."""
        rc = self.new(NOMINAL, QUESTION_OUT, READY_OUT, DRAFT_OUT, extra=self.sources())
        self.assertEqual(rc, 0)
        draft = DRAFT_OUT.removeprefix("IABINOME:DEMANDE\n")
        demande = (self.collab / "demande.md").read_text(encoding="utf-8")
        self.assertEqual(demande, draft)
        sha = contracts.normalize(draft).sha256
        self.assertEqual(self.read_json("configuration.json")["initial_demande_sha256"], sha)
        self.assertEqual(self.read_json("etat.json")["demande_sha256"], sha)
        (entry,) = self.read_json("provenance_demande.json")["versions"]
        self.assertEqual(entry["source"], "cadrage")
        self.assertEqual(entry["method"], "agent")
        self.assertEqual(entry["framing_provenance"], "cadrage/provenance.json")
        self.assertEqual((entry["agent_draft_sha256"], entry["human_edited"]), (sha, False))
        self.assertEqual(self.read_json("provenance_demande.json")["schema_version"], 1)
        prov = self.read_json("cadrage", "provenance.json")
        self.assertEqual(prov["session"], {
            "persistent": True, "new_for_this_framing": True, "resumable": False,
        })
        self.assertEqual(prov["closure"], "AGENT_PROPOSED")
        self.assertEqual((prov["turn_count"], prov["exchange_count"]), (1, 3))
        self.assertEqual(len(list((self.collab / "cadrage" / "appels").iterdir())), 3)
        self.assertEqual(prov["open_questions"], ["Question : durée de vie ?"])
        self.assertTrue(prov["sources"]["provided"])
        transcript = (self.collab / "cadrage" / "transcription.md").read_bytes()
        self.assertEqual(prov["transcription_sha256"], hashlib.sha256(transcript).hexdigest())
        self.assertIsNotNone(self.read_json("configuration.json")["corpus_manifest_sha256"])
        self.assertEqual(len(self.f.framing_sessions), 1)

    def test_no_absolute_source_path_and_no_leftover(self) -> None:
        """Test 7 et critère 7 ; test 51 côté création : le dossier jetable disparaît."""
        extra = self.sources()
        self.assertEqual(self.new(NOMINAL, QUESTION_OUT, READY_OUT, DRAFT_OUT, extra=extra), 0)
        project = str(self.root / "projet")
        for path in self.collab.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                self.assertNotIn(project, text, path)
                self.assertNotIn(project.replace("\\", "\\\\"), text, path)
        self.assertFalse(self.roots[0].exists())

    def test_ab_never_see_the_framing(self) -> None:
        """Tests 54, 55 et 56 : A lit `demande.md`, jamais la transcription ; B ne reçoit
        aucun artefact de cadrage. La session de F est fermée avant A."""
        self.assertEqual(self.new(NOMINAL, QUESTION_OUT, READY_OUT, DRAFT_OUT), 0)
        self.a.responses = ["IABINOME:DOCUMENT\n# Proposition\nCorps."]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(cli.main(["run", str(self.collab)]), 0)
        for prompt in self.a.prompts + self.b.prompts:
            self.assertNotIn(_SECRET, prompt)
            self.assertNotIn("cadrage/", prompt)
        self.assertIn("Décider de la stratégie de cache.", self.a.prompts[0])


class TestReview(FramingCliCase):
    def test_a_human_edit_is_applied_before_creation(self) -> None:
        """Tests 41, 43 et 59 : `m` remplace le brouillon ; empreintes du texte relu."""
        edited = DRAFT_OUT.removeprefix("IABINOME:DEMANDE\n").replace("Python seul.", "Rust.")
        inputs = ["idée", ".", "r", "m", *edited.splitlines(), ".", "v"]
        self.assertEqual(self.new(inputs, READY_OUT, DRAFT_OUT), 0)
        demande = (self.collab / "demande.md").read_text(encoding="utf-8")
        self.assertIn("Rust.", demande)
        (entry,) = self.read_json("provenance_demande.json")["versions"]
        self.assertTrue(entry["human_edited"])
        self.assertNotEqual(entry["agent_draft_sha256"], entry["sha256"])
        self.assertEqual(
            self.read_json("configuration.json")["initial_demande_sha256"], entry["sha256"]
        )

    def test_an_invalid_edit_is_refused_and_the_draft_kept(self) -> None:
        inputs = ["idée", ".", "r", "m", "juste une ligne", ".", "v"]
        self.assertEqual(self.new(inputs, READY_OUT, DRAFT_OUT), 0)
        (entry,) = self.read_json("provenance_demande.json")["versions"]
        self.assertFalse(entry["human_edited"])

    def test_closing_early_is_confirmed_then_recorded(self) -> None:
        """`/clore` : confirmation locale, puis rédaction ; clôture USER_CLOSED."""
        inputs = ["idée", ".", "/clore", ".", "o", "v"]
        self.assertEqual(self.new(inputs, QUESTION_OUT, DRAFT_OUT), 0)
        self.assertEqual(self.read_json("cadrage", "provenance.json")["closure"], "USER_CLOSED")

    def test_continuing_after_the_draft_keeps_the_session(self) -> None:
        """Test 45 et 75 : `c` après le brouillon, même session, nouvelle proposition."""
        inputs = ["idée", ".", "r", "c", "ajoute une contrainte", ".", "r", "v"]
        self.assertEqual(self.new(inputs, READY_OUT, DRAFT_OUT, READY_OUT, DRAFT_OUT), 0)
        self.assertEqual(len(self.f.framing_sessions), 1)
        self.assertEqual(self.read_json("cadrage", "provenance.json")["exchange_count"], 4)


class TestNothingCreated(FramingCliCase):
    def assert_nothing(self, rc: int) -> None:
        self.assertEqual(rc, 1)
        self.assertFalse(self.collab.exists())
        self.assertEqual([p.name for p in self.root.iterdir() if p.name.startswith(".new-")], [])
        for root in self.roots:
            self.assertFalse(root.exists())

    def test_cancel_eof_and_interrupt(self) -> None:
        """Tests 13, 35 et 51."""
        cases: tuple[list[Any], ...] = (
            ["idée", ".", "/annuler", "."],
            ["idée", ".", "r", "a"],
            ["idée", ".", EOFError()],
            ["idée", ".", KeyboardInterrupt()],
        )
        for inputs in cases:
            with self.subTest(inputs=inputs):
                self.assert_nothing(self.new(list(inputs), QUESTION_OUT if "/annuler" in inputs
                                             else READY_OUT))

    def test_deterministic_refusals_come_before_any_call(self) -> None:
        """§3.2 et tests 8, 9 : destination, recherche sans corpus, adaptateur de F."""
        self.f.capabilities = fakes.FakeAdapter(
            supports_persistent_framing_session=False
        ).capabilities
        self.assert_nothing(self.new([]))
        self.f.capabilities = fakes.FakeAdapter().capabilities
        self.assert_nothing(self.new([], kind="recherche"))
        self.collab.mkdir()
        with mock.patch("builtins.input", side_effect=AssertionError("aucune saisie")):
            self.assertEqual(self.new([]), 1)
        self.assertEqual(self.f.framing_sessions, {})

    def test_framing_options_need_the_agent_mode(self) -> None:
        """§3.1 : options propres à F refusées hors mode agent ; F exigé en mode agent."""
        demande = self.root / "demande.md"
        demande.write_text("Concevoir.", encoding="utf-8")
        with mock.patch("sys.stderr"):
            rc = cli.main([
                "new", str(self.collab), "--demande", str(demande), "--agent-cadrage", "fake-f",
                "--kind", "conception", "--reviewer-access", "consult",
                "--agent-a", "fake-a", "--agent-b", "fake-b",
            ])
            self.assertEqual(rc, 1)
            rc = cli.main([
                "new", str(self.collab), "--cadrer-avec-agent", "--kind", "conception",
                "--reviewer-access", "consult", "--agent-a", "fake-a", "--agent-b", "fake-b",
            ])
        self.assertEqual(rc, 1)
        self.assertFalse(self.collab.exists())

    def test_the_help_says_the_agent_mode_may_call(self) -> None:
        """Critère 2."""
        parser = cli.build_parser()
        help_text = " ".join(parser.format_help().split())
        self.assertIn("le cadrage avec agent peut effectuer des appels", help_text)


if __name__ == "__main__":
    unittest.main()
