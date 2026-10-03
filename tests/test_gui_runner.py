"""Passage GUI vers le Runner sans appel fournisseur ni WSL requis."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import decisions, workflow
from iabinome.gui.runner_session import RunnerRequest, RunnerSession
from tests import fakes


class RunnerGuiTest(unittest.TestCase):
    def test_accepted_conception_exports_then_receives_bridge_result(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        collab = fakes.collaboration(root)
        a = fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Plan\nContenu.",))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30)
        workflow.decide(collab, decisions.ACCEPTED)
        fake_bridge = root / "fake_bridge.py"
        fake_bridge.write_text(
            "import json, sys\n"
            "request = json.loads(sys.stdin.readline())\n"
            "assert request['action'] == 'start'\n"
            "assert request['token'] == 'fake-token'\n"
            "assert sys.stdin.readline().strip() == 'pause'\n"
            "print(json.dumps({'event': 'prepared', 'run': request['run']}), flush=True)\n"
            "print(json.dumps({'event': 'completed', 'package': '/tmp/review-package'}), "
            "flush=True)\n",
            encoding="utf-8",
        )
        export = root / "export"
        request = RunnerRequest(
            action="start", collaboration=collab, export=export,
            repo=root / "repo", base="HEAD", validations=[["python3", "-m", "pytest", "tests"]],
            run="~/dialogforge-runs/test", token="fake-token", timeout=60,
            validation_timeout=30,
        )
        with mock.patch(
            "iabinome.gui.runner_session._bridge_command",
            return_value=[sys.executable, str(fake_bridge)],
        ):
            session = RunnerSession(request)
            session.signal("pause")
            session.start()
            session.thread.join(timeout=15)
        self.assertFalse(session.thread.is_alive())
        self.assertIsNone(session.error)
        self.assertEqual(session.package, "/tmp/review-package")
        self.assertEqual(request.token, "")
        self.assertIn("Plan", (export / "export.md").read_text(encoding="utf-8"))
        metadata = json.loads((export / "export.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["source_collaboration"], collab.name)
