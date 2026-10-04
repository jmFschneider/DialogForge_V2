"""Le paquet prêt avance vers une revue locale, sans nouvel appel au Runner."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from iabinome import decisions, delivery, development, executions, mission, workflow
from tests import fakes, runner_support


class DeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.collab = runner_support.accepted_conception(self.root / "conception")
        mission.attach(self.root, self.collab, "conception")
        self.repo = self.root / "repo"
        self.repo.mkdir()
        with runner_support.git_home(self.root):
            runner_support.git(self.repo, "init")
            runner_support.git(self.repo, "commit", "--allow-empty", "-m", "base")
            self.base = runner_support.git(self.repo, "rev-parse", "HEAD")
            (self.repo / "app.txt").write_text("Mastermind\n", encoding="utf-8")
            runner_support.git(self.repo, "add", "app.txt")
            runner_support.git(self.repo, "commit", "-m", "candidat")
            self.head = runner_support.git(self.repo, "rev-parse", "HEAD")
            found = executions.find(self.collab)
            export = executions.ensure_export(self.collab, found)
            self.source = self.root / "runner" / "results" / "collect-0001" / "package"
            development.build_package(export, self.repo, self.base, self.head, self.source)
        self.reference = executions.save(
            found, export, mode="nouveau", repo=self.repo, base="HEAD",
            validations=[["node", "--test"]], run=str(self.root / "runner"),
            agent_timeout=10, validation_timeout=10,
        )
        executions.update(self.reference, paquets=[str(self.source)],
                          projet={"base_oid": self.base})
        self.found = executions.find(self.collab)
        self.state = {"stage": "paquet", "package": str(self.source), "locked": False}

    def test_receive_is_verified_and_idempotent(self) -> None:
        first = delivery.receive_package(self.collab, self.found, self.state, source=self.source)
        second = delivery.receive_package(self.collab, self.found, self.state, source=self.source)
        self.assertEqual(first, second)
        self.assertEqual(first.parent, executions.dev_dir(self.collab) / "paquets")
        self.assertEqual(
            development.read_package(first)[1]["package_id"],
            development.read_package(self.source)[1]["package_id"],
        )
        (self.source / "revision" / "diff.patch").write_text("altéré", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modifié"):
            delivery.receive_package(self.collab, self.found, self.state, source=self.source)

    def test_review_creation_reuses_same_review(self) -> None:
        package = delivery.receive_package(self.collab, self.found, self.state, source=self.source)
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ()),
            "fake-b": fakes.FakeAdapter("fake-b", ()),
        }
        with mock.patch.object(delivery, "ADAPTERS", adapters):
            first = delivery.create_review(self.collab, package)
            second = delivery.create_review(self.collab, package)
        self.assertEqual(first, second)
        self.assertEqual(development.verify_package(package, first)["status"], "READY")
        self.assertEqual(delivery.review_context(first)[0], self.collab)
        located = mission.locate(first)
        assert located is not None and located.step is not None
        self.assertEqual(located.step.role, "revue")

    def test_accepted_review_integrates_exact_head_once(self) -> None:
        package = delivery.receive_package(self.collab, self.found, self.state, source=self.source)
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Rapport\n",)),
            "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        with mock.patch.object(delivery, "ADAPTERS", adapters):
            review = delivery.create_review(self.collab, package)
        with self.assertRaisesRegex(ValueError, "accepter d'abord"):
            delivery.integrate_candidate(review)
        workflow.run(review, adapters=adapters, timeout_seconds=15)
        workflow.decide(review, decisions.ACCEPTED)
        target = self.root / "target"
        bundle = self.root / "candidate.bundle"
        with runner_support.git_home(self.root):
            runner_support.git(self.repo, "bundle", "create", str(bundle), "HEAD",
                               f"^{self.base}")
            runner_support.git(self.root, "clone", str(self.repo), str(target))
            runner_support.git(target, "reset", "--hard", self.base)
            executions.update(self.reference, projet={"depot": str(target)})
            with mock.patch.object(delivery, "_local_bundle", return_value=bundle):
                receipt = delivery.integrate_candidate(review)
                self.assertEqual(runner_support.git(target, "rev-parse", "HEAD"), self.head)
                self.assertEqual(delivery.integrate_candidate(review), receipt)
            self.assertTrue(receipt.is_file())
            (target / "untracked.txt").write_text("local", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changements locaux"):
                delivery.integrate_candidate(review)

    def test_refuses_unfinished_or_foreign_package(self) -> None:
        for state in (
            {**self.state, "stage": "appel"},
            {**self.state, "locked": True},
            {**self.state, "package": "/foreign/package"},
        ):
            with self.subTest(state=state), self.assertRaises(ValueError):
                delivery.receive_package(self.collab, self.found, state, source=self.source)

    def test_linux_source_must_be_inside_run(self) -> None:
        data = {"run": "/home/test/runner"}
        good = "/home/test/runner/results/collect-0001/package"
        source = delivery._source_path(data, good, "Ubuntu")
        self.assertTrue(str(source).endswith("collect-0001\\package" if os.name == "nt"
                                             else "collect-0001/package"))
        with self.assertRaisesRegex(ValueError, "étranger"):
            delivery._source_path(data, "/home/test/other/package", "Ubuntu")


if __name__ == "__main__":
    unittest.main()
