"""Tests de iabinome.cli — surface CLI (CONCEPTION_FINALE.md §7, §10).

`cli.ADAPTERS` est toujours substitué par des `FakeAdapter` : la production
câble Claude et Codex, mais la suite de tests n'appelle jamais un vrai
fournisseur (`RULES.md`).
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import cli, transport, workflow
from iabinome.models import Configuration, SchemaError, State
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps."
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.demande = self.root / "demande-source.md"
        self.demande.write_text("Concevoir le cache de FloraPi.", encoding="utf-8")
        self.collab = self.root / "collaboration"
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", ())
        patcher = mock.patch.object(cli, "ADAPTERS", {"fake-a": self.a, "fake-b": self.b})
        patcher.start()
        self.addCleanup(patcher.stop)

    def new_args(self, **overrides: str) -> list[str]:
        args = {
            "collab": str(self.collab), "--demande": str(self.demande),
            "--kind": "conception", "--reviewer-access": "consult",
            "--agent-a": "fake-a", "--agent-b": "fake-b",
        }
        args.update(overrides)
        argv = [args.pop("collab")]
        for key, value in args.items():
            argv += [key, value]
        return argv

    def make_source(self, *, files: dict[str, str]) -> tuple[Path, Path]:
        root = self.root / "source"
        root.mkdir()
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")
        listing = self.root / "manifeste-source.txt"
        listing.write_text("\n".join(files) + "\n", encoding="utf-8")
        return root, listing


class TestNewRequiredOptions(CliCase):
    def test_missing_reviewer_access_is_refused(self) -> None:
        argv = ["new", *self.new_args()]
        argv = [a for a in argv if a not in ("--reviewer-access", "consult")]
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(argv)
        self.assertFalse(self.collab.exists())

    def test_missing_agent_a_is_refused(self) -> None:
        argv = ["new", *self.new_args()]
        argv = [a for a in argv if a not in ("--agent-a", "fake-a")]
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(argv)

    def test_unknown_agent_is_refused(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(["new", *self.new_args(**{"--agent-a": "un-outil-inconnu"})])


class TestNewCorpus(CliCase):
    def test_research_without_corpus_is_refused(self) -> None:
        code = cli.main(["new", *self.new_args(**{"--kind": "recherche"})])
        self.assertEqual(code, 1)
        self.assertFalse(self.collab.exists())

    def test_research_with_empty_corpus_is_refused(self) -> None:
        root = self.root / "source"
        root.mkdir()
        listing = self.root / "vide.txt"
        listing.write_text("", encoding="utf-8")
        code = cli.main(["new", *self.new_args(
            **{"--kind": "recherche", "--source-root": str(root), "--source-list": str(listing)}
        )])
        self.assertEqual(code, 1)
        self.assertFalse(self.collab.exists())

    def test_source_root_without_source_list_is_refused(self) -> None:
        root = self.root / "source"
        root.mkdir()
        code = cli.main(["new", *self.new_args(**{"--source-root": str(root)})])
        self.assertEqual(code, 1)


class TestNewCreatesCollaboration(CliCase):
    def test_a_conception_collaboration_is_created(self) -> None:
        code = cli.main(["new", *self.new_args()])
        self.assertEqual(code, 0)
        config = fakes.read_json(self.collab / "configuration.json")
        self.assertEqual(config["mission_kind"], "CONCEPTION")
        self.assertEqual(config["reviewer_access"], "CONSULT")
        self.assertEqual(config["agent_a"], {"adapter_id": "fake-a", "model": "fake-a-modele-a"})
        etat = fakes.read_json(self.collab / "etat.json")
        self.assertEqual(etat["status"], "READY")
        self.assertEqual(etat["phase"], "PROPOSAL_A")

    def test_model_override_is_kept_over_the_adapter_default(self) -> None:
        cli.main(["new", *self.new_args(**{"--model-a": "un-modele-choisi"})])
        config = fakes.read_json(self.collab / "configuration.json")
        self.assertEqual(config["agent_a"]["model"], "un-modele-choisi")

    def test_existing_destination_is_refused(self) -> None:
        self.collab.mkdir()
        code = cli.main(["new", *self.new_args()])
        self.assertEqual(code, 1)

    def test_a_research_collaboration_carries_the_corpus(self) -> None:
        root, listing = self.make_source(files={"a.md": "Contenu A"})
        code = cli.main(["new", *self.new_args(
            **{"--kind": "recherche", "--source-root": str(root), "--source-list": str(listing)}
        )])
        self.assertEqual(code, 0)
        self.assertTrue((self.collab / "corpus" / "fichiers" / "a.md").exists())
        config = fakes.read_json(self.collab / "configuration.json")
        self.assertIsNotNone(config["corpus_manifest_sha256"])


class TestRunAndResume(CliCase):
    def build(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)

    def test_run_drives_the_engine_and_reports_the_status(self) -> None:
        self.build()
        self.a.responses = [_QUESTION]
        code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 5)
        etat = fakes.read_json(self.collab / "etat.json")
        self.assertEqual(etat["status"], "WAITING_HUMAN")

    def test_a_second_run_while_the_human_is_awaited_is_refused(self) -> None:
        """La porte d'état vue depuis la CLI : refus lisible, pas de traceback,
        et surtout aucun appel supplémentaire (C-01)."""
        self.build()
        self.a.responses = [_QUESTION]
        self.assertEqual(cli.main(["run", str(self.collab)]), 5)
        with redirect_stderr(io.StringIO()) as err:
            code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 1)
        self.assertIn("WAITING_HUMAN", err.getvalue())
        self.assertEqual(self.a.calls, 1, "un appel a ete paye")

    def test_absent_cli_is_reported_not_crashed(self) -> None:
        self.build()
        self.a.present = False
        code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 1)

    def test_answer_does_not_touch_the_corpus(self) -> None:
        root, listing = self.make_source(files={"a.md": "Contenu A"})
        self.assertEqual(cli.main(["new", *self.new_args(
            **{"--kind": "recherche", "--source-root": str(root), "--source-list": str(listing)}
        )]), 0)
        before = fakes.read_json(self.collab / "configuration.json")["corpus_manifest_sha256"]
        self.a.responses = [_QUESTION]
        cli.main(["run", str(self.collab)])
        answer = self.root / "reponse.md"
        answer.write_text("Le critere de fin est la couverture complete.", encoding="utf-8")
        # Les deux agents rendent ensuite leur réponse par défaut, hors contrat
        # pour B : le cycle finit en ERROR, code 4.
        code = cli.main(["resume", str(self.collab), "--answer", str(answer)])
        self.assertEqual(code, 4)
        after = fakes.read_json(self.collab / "configuration.json")["corpus_manifest_sha256"]
        self.assertEqual(before, after)
        self.assertTrue((self.collab / "demande.md.001").exists())
        self.assertIn(
            "couverture complete",
            (self.collab / "demande.md").read_text(encoding="utf-8"),
        )

    def test_retry_call_needs_a_non_empty_reason(self) -> None:
        self.build()
        self.a.responses = []
        self.a.sleep_seconds = 5.0
        # Un appel interrompu par delai, sans reponse : table de reprise §5.
        # Ce test attendait `0` — il figeait le defaut C-03 : INTERRUPTED vaut 3.
        code = cli.main(["run", str(self.collab), "--timeout", "0.05"])
        self.assertEqual(code, 3)
        etat = fakes.read_json(self.collab / "etat.json")
        self.assertEqual(etat["status"], "INTERRUPTED")
        call_id = etat["current_call"]["call_id"]
        empty_reason = self.root / "motif-vide.txt"
        empty_reason.write_text("   ", encoding="utf-8")
        code = cli.main([
            "resume", str(self.collab), "--retry-call", call_id, "--reason-file", str(empty_reason),
        ])
        self.assertEqual(code, 1)


class TestExitCodes(CliCase):
    """Table D-5, un cas par statut observable depuis la CLI.

    Le code décrit le **résultat de la commande**, jamais l'approbation du
    livrable : `AWAITING_APPROVAL` vaut `0` parce que le cycle s'est arrêté où
    il devait. `2` reste réservé à `argparse` — le programme ne le produit
    jamais, et un test le vérifie sur une commande mal formée.
    """

    def build(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)

    def test_awaiting_approval_is_zero(self) -> None:
        self.build()
        self.a.responses = [_DOC, "IABINOME:DOCUMENT\n# Final\nCorps."]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        self.assertEqual(cli.main(["run", str(self.collab)]), 0)

    def test_a_refusal_before_any_mutation_is_one(self) -> None:
        self.build()
        self.a.present = False
        before = (self.collab / "etat.json").read_bytes()
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["run", str(self.collab)]), 1)
        self.assertEqual((self.collab / "etat.json").read_bytes(), before)

    def test_two_is_left_to_argparse(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main(["run"])  # argument obligatoire absent
        self.assertEqual(caught.exception.code, 2)

    def test_interrupted_is_three(self) -> None:
        self.build()
        self.a.sleep_seconds = 5.0
        self.assertEqual(cli.main(["run", str(self.collab), "--timeout", "0.05"]), 3)

    def test_error_is_four(self) -> None:
        self.build()
        self.a.responses = ["Bonjour, voici mon document."]
        self.assertEqual(cli.main(["run", str(self.collab)]), 4)

    def test_waiting_human_is_five(self) -> None:
        """Contre l'avis de Codex, qui recommandait `0` : mettre `WAITING_HUMAN`
        à `0` rendrait « il te faut répondre » et « c'est fini » indiscernables
        au niveau du code de sortie — le défaut même que C-03 reproche."""
        self.build()
        self.a.responses = [_QUESTION]
        self.assertEqual(cli.main(["run", str(self.collab)]), 5)
        self.assertNotEqual(
            cli.main(["status", str(self.collab)]), 5, "status reste en lecture seule"
        )


class TestNumericArguments(CliCase):
    """C-08 : `--timeout` acceptait `0`, les négatifs, `inf` et `nan`.

    `nan` est le cas grave : `time.monotonic() >= deadline` reste **faux** pour
    lui, si bien que le délai dur — la seule borne du cycle — ne se déclenchait
    jamais. Refusé par `argparse`, donc en code **2**, et refusé aussi aux
    entrées Python, que les tests appellent directement.
    """

    def refused_timeout(self, value: str) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main(["run", str(self.collab), "--timeout", value])
        self.assertEqual(caught.exception.code, 2)

    def test_zero_negative_inf_and_nan_timeouts_are_refused(self) -> None:
        for value in ("0", "-1", "inf", "nan", "pas-un-nombre"):
            with self.subTest(timeout=value):
                self.refused_timeout(value)

    def test_a_negative_max_revisions_is_refused(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main(["new", *self.new_args(**{"--max-revisions": "-1"})])
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse(self.collab.exists())

    def test_the_python_entry_points_refuse_them_too(self) -> None:
        """`workflow.run` et `transport.run` sont des surfaces appelées
        directement : la validation n'appartient pas qu'à `argparse`."""
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        for value in (0.0, -1.0, float("inf"), float("nan")):
            with self.subTest(timeout=value):
                with self.assertRaises(SchemaError):
                    workflow.run(
                        self.collab, adapters={"fake-a": self.a, "fake-b": self.b},
                        timeout_seconds=value,
                    )
                with self.assertRaises(SchemaError):
                    transport.run(
                        ["python", "-c", "pass"], cwd=self.collab,
                        call_dir=self.collab, timeout_seconds=value,
                    )
        self.assertEqual(self.a.calls, 0, "un appel est parti avec un delai invalide")


class TestLoadedConfiguration(CliCase):
    def test_a_negative_max_revisions_is_refused_at_load(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        config = fakes.read_json(self.collab / "configuration.json")
        config["max_revisions"] = -1
        fakes.write_json(self.collab / "configuration.json", config)
        with self.assertRaises(SchemaError):
            Configuration.from_dict(fakes.read_json(self.collab / "configuration.json"))

    def test_a_boolean_schema_version_is_refused(self) -> None:
        """`True != 1` est faux : `schema_version: true` passait pour la
        version 1, alors que `_int` refuse déjà les booléens ailleurs."""
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        etat = fakes.read_json(self.collab / "etat.json")
        etat["schema_version"] = True
        with self.assertRaises(SchemaError):
            State.from_dict(etat)


class TestStatus(CliCase):
    def test_status_json_reports_the_current_phase(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            code = cli.main(["status", str(self.collab), "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"phase": "PROPOSAL_A"', buf.getvalue())
        self.assertIn('"status": "READY"', buf.getvalue())


if __name__ == "__main__":
    unittest.main()
