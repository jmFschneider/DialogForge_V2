"""Référence d'exécution, formulaire de validations et mandat transmis — sans fournisseur."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import development, executions, mission
from tests.runner_support import accepted_conception


class ExecutionsTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.collab = accepted_conception(self.root)

    def save(self, found: executions.Found, **overrides: object) -> Path:
        export = executions.ensure_export(self.collab, found)
        arguments: dict[str, object] = {
            "mode": "nouveau", "repo": self.root / "code", "base": "HEAD",
            "validations": [["node", "--test"]], "run": "~/dialogforge-runs/essai-001",
            "agent_timeout": 3600.0, "validation_timeout": 300.0, **overrides,
        }
        return executions.save(found, export, **arguments)  # type: ignore[arg-type]

    def test_without_mission_everything_sits_next_to_the_conception(self) -> None:
        found = executions.find(self.collab)
        self.assertEqual(found.dev, self.collab.parent / "collaboration-developpement")
        self.assertEqual(executions.default_code(self.collab), self.root / "collaboration-code")
        self.assertEqual((found.export, found.reference, found.number), (None, None, 1))
        self.assertFalse(found.dev.exists(), "chercher n'écrit rien")

    def test_a_mission_keeps_export_and_code_inside(self) -> None:
        mission_root = self.root / "Mastermind"
        mission_root.mkdir()
        shutil.move(self.collab, mission_root / "conception")
        mission.attach(mission_root, mission_root / "conception", "conception")
        collab = mission_root / "conception"
        self.assertEqual(executions.dev_dir(collab), mission_root / "developpement")
        self.assertEqual(executions.default_code(collab), mission_root / "code")
        self.assertEqual(executions.project_name(collab), "Mastermind")
        found = executions.find(collab)
        export = executions.ensure_export(collab, found)
        self.assertEqual(export, mission_root / "developpement" / "export-001")
        reference = executions.save(
            found, export, mode="nouveau", repo=mission_root / "code", base="HEAD",
            validations=[["node", "--test"]], run="/home/u/run", agent_timeout=60.0,
            validation_timeout=30.0,
        )
        data = executions.load(reference)
        self.assertEqual(reference, mission_root / "developpement" / "executions" / "001.json")
        self.assertEqual((data["conception"], data["export"]["path"]),
                         ("conception", "developpement/export-001"))

    def test_the_reference_is_published_with_only_non_secret_fields(self) -> None:
        found = executions.find(self.collab)
        path = self.save(found)
        data = executions.load(path)
        self.assertEqual(set(data), {
            "schema_version", "conception", "export", "projet", "profil", "wsl", "run",
            "validations", "delais", "paquets",
        })
        self.assertEqual(data["projet"], {
            "mode": "nouveau", "depot": str(self.root / "code"), "base_demandee": "HEAD",
            "base_oid": None, "identite": None,
        })
        self.assertEqual(data["validations"], [["node", "--test"]])
        self.assertEqual(data["delais"], {"agent": 3600.0, "validation": 300.0})
        self.assertNotRegex(path.read_text(encoding="utf-8").lower(), "token|oauth|secret")

    def test_an_identical_export_is_reused_and_a_new_acceptance_gets_a_new_one(self) -> None:
        found = executions.find(self.collab)
        reference = self.save(found)
        again = executions.find(self.collab)
        self.assertEqual((again.export, again.reference, again.number),
                         (found.dev / "export-001", reference, 1))
        self.assertEqual(executions.ensure_export(self.collab, again), found.dev / "export-001")
        self.assertEqual(len(list(found.dev.glob("export-*"))), 1)
        (found.dev / "export-001" / "export.md").write_text("modifié", encoding="utf-8")
        changed = executions.find(self.collab)
        self.assertEqual((changed.export, changed.reference, changed.number), (None, None, 2))
        second = executions.ensure_export(self.collab, changed)
        self.assertEqual(second.name, "export-002")
        self.assertEqual((found.dev / "export-001" / "export.md").read_text("utf-8"), "modifié")

    def test_updates_merge_known_fields_and_refuse_the_others(self) -> None:
        path = self.save(executions.find(self.collab))
        executions.update(path, run="/home/u/run", wsl={"distribution": "Ubuntu-24.04"},
                          projet={"base_oid": "a" * 40, "identite": "N <n@x>"},
                          paquets=["/home/u/run/results/collect-0001/package"])
        executions.update(path, paquets=["/home/u/run/results/collect-0001/package"])
        data = executions.load(path)
        self.assertEqual(data["run"], "/home/u/run")
        self.assertEqual(data["wsl"]["distribution"], "Ubuntu-24.04")
        self.assertEqual(
            (data["projet"]["mode"], data["projet"]["base_oid"]), ("nouveau", "a" * 40),
        )
        self.assertEqual(len(data["paquets"]), 1)
        with self.assertRaisesRegex(ValueError, "non modifiable"):
            executions.update(path, token="secret")

    def test_saving_again_keeps_what_the_runner_recorded(self) -> None:
        found = executions.find(self.collab)
        path = self.save(found)
        executions.update(path, projet={"base_oid": "b" * 40, "identite": "N <n@x>"},
                          wsl={"distribution": "Ubuntu-24.04"})
        resumed = executions.find(self.collab)
        self.save(resumed, validations=[["node", "--test", "tests"]])
        data = executions.load(path)
        self.assertEqual(data["projet"]["base_oid"], "b" * 40)
        self.assertEqual(data["wsl"]["distribution"], "Ubuntu-24.04")
        self.assertEqual(data["validations"], [["node", "--test", "tests"]])
        self.save(resumed, mode="existant")
        self.assertIsNone(executions.load(path)["projet"]["base_oid"],
                          "une autre voie ne reprend pas la base d'un projet neuf")

    def test_another_folder_does_not_inherit_the_initial_base_of_the_first(self) -> None:
        path = self.save(executions.find(self.collab))
        executions.update(path, projet={"base_oid": "c" * 40, "identite": "N <n@x>"})
        self.save(executions.find(self.collab), repo=self.root / "ailleurs")
        project = executions.load(path)["projet"]
        self.assertEqual((project["depot"], project["base_oid"], project["identite"]),
                         (str(self.root / "ailleurs"), None, None))

    def test_an_invalid_reference_is_diagnosed_not_replaced(self) -> None:
        path = self.save(executions.find(self.collab))
        data = json.loads(path.read_text(encoding="utf-8"))
        data["jeton"] = "x"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "001.json : référence d'exécution invalide"):
            executions.find(self.collab)
        path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "illisible"):
            executions.find(self.collab)

    def test_a_modified_export_or_conception_stops_before_any_agent_call(self) -> None:
        found = executions.find(self.collab)
        path = self.save(found)
        executions.check_current(self.collab, path)
        (found.dev / "export-001" / "export.md").write_text("modifié", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "nouvel export et une nouvelle exécution"):
            executions.check_current(self.collab, path)

    def test_an_open_finding_reaches_the_developer_mandate(self) -> None:
        collab = accepted_conception(self.root / "reserves", open_finding=True)
        mandate = development.export_files(collab)["export.md"].decode("utf-8")
        opened = mandate.split("## Constats ouverts", 1)[1].split("## Passage de relais")[0]
        self.assertIn('"id": "B-001"', opened)
        self.assertIn('"disposition": "OPEN"', opened)
        self.assertIn("La revue du candidat les réexaminera", opened)


class FormRulesTest(unittest.TestCase):
    def test_a_row_is_an_executable_and_its_arguments_without_shell(self) -> None:
        self.assertEqual(executions.argv(" node ", "--test"), ["node", "--test"])
        self.assertEqual(executions.argv("python3", '-m pytest "tests unitaires"'),
                         ["python3", "-m", "pytest", "tests unitaires"])
        self.assertEqual(executions.argv("node", "--test && rm -rf x"),
                         ["node", "--test", "&&", "rm", "-rf", "x"])
        with self.assertRaisesRegex(ValueError, "exécutable"):
            executions.argv("  ", "--test")
        with self.assertRaisesRegex(ValueError, "arguments de « node »"):
            executions.argv("node", '"non fermé')

    def test_blank_rows_are_ignored_but_one_validation_is_required(self) -> None:
        self.assertEqual(
            executions.validations_from_rows([("", ""), ("node", "--test"), ("", "  ")]),
            [["node", "--test"]],
        )
        with self.assertRaisesRegex(ValueError, "au moins une validation"):
            executions.validations_from_rows([("", ""), ("  ", "")])
        with self.assertRaisesRegex(ValueError, "exécutable"):
            executions.validations_from_rows([("", "--test")])

    def test_saved_commands_round_trip_through_the_rows(self) -> None:
        commands = [["node", "--test"], ["python3", "-m", "pytest", "tests unitaires"]]
        rows = executions.rows_from_validations(commands)
        self.assertEqual(executions.validations_from_rows(rows), commands)

    def test_each_stage_offers_only_its_start(self) -> None:
        self.assertEqual(executions.actions(None), ("start",))
        self.assertEqual(executions.actions({"stage": "absent"}), ("start",))
        self.assertEqual(executions.actions({"stage": "prepare"}), ("launch", "collect"))
        for stage in ("appel", "validations"):
            self.assertEqual(executions.actions({"stage": stage}), ("continue", "collect"))
        self.assertEqual(executions.actions({"stage": "paquet"}), ("correct",))
        self.assertEqual(executions.actions({"stage": "invalide"}), ())
        for stage in ("prepare", "appel", "validations", "paquet"):
            self.assertNotIn("start", executions.actions({"stage": stage}))

    def test_the_description_names_the_situation(self) -> None:
        self.assertIn("la préparation peut commencer", executions.describe(None))
        self.assertIn("agent non lancé", executions.describe({"stage": "prepare"}))
        called = executions.describe({"stage": "appel", "calls": 2, "last_call_complete": False})
        self.assertIn("2 appel(s)", called)
        self.assertIn("interrompu", called)
        self.assertIn("paquet : /x. Son commit est remis dans code/", executions.describe(
            {"stage": "paquet", "package": "/x"}))
        self.assertIn("jamais supprimé", executions.describe(
            {"stage": "prepare", "locked": True}))
