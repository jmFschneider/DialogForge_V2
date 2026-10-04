"""Remise d'un candidat dans `code/` puis acceptation du commit essayé, sans agent ni jeton.

Le candidat vient d'un vrai parcours Runner (pont en sous-processus, faux agent, profil local) ;
seul le transport du bundle depuis Ubuntu est remplacé par l'appel direct au Runner. Le parcours
remet déjà le candidat après sa réussite : refaire la remise ne doit rien changer.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from iabinome import delivery, development, executions
from tests.runner_support import git
from tests.test_runner_flow import FlowCase


class DeliveryCase(FlowCase):
    def deliver(self) -> delivery.Delivered:
        state = self.state()
        return delivery.deliver(self.collab, executions.find(self.collab), state,
                                source=Path(state["package"]))

    def accept(self) -> Path:
        return delivery.accept(self.collab, executions.find(self.collab))

    def head_of(self, package: str) -> Any:
        return development.read_package(Path(package))[1]["identity"]["head_oid"]


class NewProjectDeliveryTest(DeliveryCase):
    def test_a_package_is_delivered_in_code_then_accepted_on_its_branch(self) -> None:
        self.assertIsNone(self.go("start").error)
        package = self.reference()["paquets"][0]
        shown = self.deliver()
        self.assertEqual((shown.code, shown.branch), (self.code, "dialogforge/candidat-001"))
        self.assertEqual(shown.head, self.head_of(package))
        self.assertEqual((self.code / "app.txt").read_text(encoding="utf-8"),
                         "resultat de l'agent\n")
        self.assertEqual(self.reference()["projet"]["branche"], "main")
        self.assertEqual(git(self.code, "rev-parse", "main"),
                         self.reference()["projet"]["base_oid"])
        bundles = list((executions.dev_dir(self.collab) / "candidats").glob("*.bundle"))
        self.assertEqual(len(bundles), 1)
        self.assertEqual(self.deliver(), shown, "refaire la remise ne change rien")
        receipt = self.accept()
        self.assertEqual(git(self.code, "rev-parse", "main"), shown.head)
        record = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual((record["head_oid"], record["branch"], record["package"]),
                         (shown.head, "main", "001"))
        found = executions.find(self.collab)
        self.assertTrue(delivery.current(self.collab, found).accepted)  # type: ignore[union-attr]
        self.assertEqual(self.accept(), receipt)
        self.assertEqual(self.agent_calls(), 1)

    def test_user_changes_in_code_stop_the_delivery_and_are_kept(self) -> None:
        self.assertIsNone(self.go("start").error)
        (self.code / "notes.txt").write_text("à moi", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "rien n'est écrasé"):
            self.deliver()
        self.assertEqual((self.code / "notes.txt").read_text(encoding="utf-8"), "à moi")

    def test_only_the_tried_commit_can_be_accepted(self) -> None:
        self.assertIsNone(self.go("start").error)
        self.deliver()
        (self.code / "essai.txt").write_text("x", encoding="utf-8")
        git(self.code, "add", "essai.txt")
        git(self.code, "commit", "-qm", "essai local")
        with self.assertRaisesRegex(ValueError, "aucune version remise"):
            self.accept()
        self.assertEqual(git(self.code, "rev-parse", "main"),
                         self.reference()["projet"]["base_oid"])

    def test_a_correction_after_acceptance_advances_from_the_accepted_version(self) -> None:
        self.assertIsNone(self.go("start").error)
        first = self.deliver()
        self.accept()
        self.mode("improve")
        self.assertIsNone(self.resume("correct", correction="Améliorer le texte.").error)
        second = self.deliver()
        self.assertEqual(second.branch, "dialogforge/candidat-002")
        self.assertIn(b"lior", (self.code / "app.txt").read_bytes())  # encodage local de l'agent
        self.accept()
        self.assertEqual(git(self.code, "rev-parse", "main"), second.head)
        self.assertEqual(git(self.code, "rev-parse", "dialogforge/candidat-001"), first.head,
                         "la version précédente reste disponible")

    def test_a_diverged_target_branch_asks_for_a_human(self) -> None:
        self.assertIsNone(self.go("start").error)
        shown = self.deliver()
        git(self.code, "switch", "-q", "main")
        (self.code / "autre.txt").write_text("x", encoding="utf-8")
        git(self.code, "add", "autre.txt")
        git(self.code, "commit", "-qm", "travail parallèle")
        diverged = git(self.code, "rev-parse", "main")
        git(self.code, "switch", "-q", shown.branch)
        with self.assertRaisesRegex(ValueError, "intervention humaine"):
            self.accept()
        self.assertEqual(git(self.code, "rev-parse", "main"), diverged)


class ExistingRepositoryDeliveryTest(DeliveryCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.root / "depot"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        (self.repo / "code.txt").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")

    def test_a_trial_copy_is_delivered_and_the_user_repository_moves_only_on_acceptance(
        self,
    ) -> None:
        self.assertIsNone(self.go("start", mode="existant", repo=self.repo).error)
        shown = self.deliver()
        self.assertEqual(shown.code, self.code)
        self.assertNotEqual(shown.code, self.repo)
        self.assertTrue((self.code / "app.txt").is_file())
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertFalse((self.repo / "app.txt").exists())
        (self.repo / "brouillon.txt").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "dépôt cible"):
            self.accept()
        (self.repo / "brouillon.txt").unlink()
        self.accept()
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), shown.head)
        self.assertEqual((self.repo / "app.txt").read_text(encoding="utf-8"),
                         "resultat de l'agent\n")


class PackageReceptionTest(DeliveryCase):
    def test_refuses_a_running_or_foreign_package(self) -> None:
        self.assertIsNone(self.go("start").error)
        state, found = self.state(), executions.find(self.collab)
        for changed in ({**state, "locked": True}, {**state, "package": "/foreign/package"},
                        {**state, "package": None}):
            with self.subTest(state=changed), self.assertRaises(ValueError):
                delivery.receive_package(self.collab, found, changed,
                                         source=Path(state["package"]))

    def test_an_altered_package_is_refused(self) -> None:
        self.assertIsNone(self.go("start").error)
        state = self.state()
        source = Path(state["package"])
        (source / "revision" / "diff.patch").write_text("altéré", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modifié"):
            delivery.receive_package(self.collab, executions.find(self.collab), state,
                                     source=source)


class LinuxPathTest(unittest.TestCase):
    def test_linux_source_must_be_inside_run(self) -> None:
        data = {"run": "/home/test/runner"}
        good = "/home/test/runner/results/collect-0001/package"
        self.assertEqual(delivery._source_path(data, good, "Ubuntu").name, "package")
        with self.assertRaisesRegex(ValueError, "étranger"):
            delivery._source_path(data, "/home/test/other/package", "Ubuntu")
