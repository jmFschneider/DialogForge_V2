"""Les pauses et la décision envoient des copies entières et distinctes."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import cli, copies, settings
from iabinome.models import State, Status
from tests import fakes


class CopyCase(unittest.TestCase):
    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.local = self.root / "local"
        self.cloud = self.root / "nextcloud"
        self.mission = self.local / "mission"
        self.step = fakes.collaboration(self.mission)
        (self.mission / "mission.json").write_text(json.dumps({
            "schema_version": 1, "name": "mission",
            "steps": [{"path": "collaboration", "role": "recherche", "source": None}],
        }), encoding="utf-8")
        self.config = self.root / "copies.toml"
        self.config.write_text(
            f'local_root = "{self.local.as_posix()}"\n'
            f'nextcloud_root = "{self.cloud.as_posix()}"\n', encoding="utf-8",
        )
        patcher = mock.patch.object(copies, "CONFIG_PATH", self.config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def state(self, status: Status) -> State:
        return replace(State.from_dict(fakes.read_json(self.step / "etat.json")), status=status)


class TestCopies(CopyCase):
    def test_question_validation_and_final_decision_each_copy_the_whole_mission(self) -> None:
        self.assertIsNone(copies.after_run(self.step, self.state(Status.READY)))
        first = copies.after_run(self.step, self.state(Status.WAITING_HUMAN))
        assert first is not None
        (self.step / "reponse.md").write_text("Réponse", encoding="utf-8")
        second = copies.after_run(self.step, self.state(Status.AWAITING_APPROVAL))
        assert second is not None
        (self.step / "decisions.json").write_text("acceptée", encoding="utf-8")
        final = copies.after_decision(self.step)
        assert final is not None
        self.assertEqual(len({first, second, final}), 3)
        self.assertEqual(len(list(self.cloud.iterdir())), 3)
        for target in (first, second, final):
            self.assertEqual((target / "mission.json").read_bytes(),
                             (self.mission / "mission.json").read_bytes())
            self.assertTrue((target / "collaboration" / "etat.json").is_file())
            self.assertTrue((target / "COPIE_TERMINEE.txt").is_file())
        self.assertFalse((first / "collaboration" / "reponse.md").exists())
        self.assertFalse((second / "collaboration" / "decisions.json").exists())
        self.assertEqual((final / "collaboration" / "decisions.json").read_text(
            encoding="utf-8"), "acceptée")
        self.assertFalse((self.mission / "COPIE_TERMINEE.txt").exists())

    def test_failed_copy_does_not_touch_the_local_mission(self) -> None:
        self.cloud.write_text("indisponible", encoding="utf-8")
        before = (self.step / "etat.json").read_bytes()
        with self.assertRaisesRegex(copies.CopyError, "copie Nextcloud échouée"):
            copies.after_run(self.step, self.state(Status.WAITING_HUMAN))
        self.assertEqual((self.step / "etat.json").read_bytes(), before)

    def test_other_local_folders_are_not_sent_automatically(self) -> None:
        outside = fakes.collaboration(self.root / "autre")
        self.assertIsNone(copies.after_run(outside, self.state(Status.WAITING_HUMAN)))
        self.assertFalse(self.cloud.exists())

    def test_cli_retries_a_full_copy(self) -> None:
        self.assertEqual(cli.main(["copy", str(self.step)]), 0)
        (target,) = self.cloud.iterdir()
        self.assertTrue((target / "collaboration" / "configuration.json").is_file())


class TestCliIntegration(CopyCase):
    def test_failed_nextcloud_copy_keeps_the_successful_cycle(self) -> None:
        self.cloud.write_text("indisponible", encoding="utf-8")
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Proposition\nCorps.",)),
            "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        stderr = io.StringIO()
        with mock.patch.object(cli, "ADAPTERS", adapters), \
             mock.patch.object(settings, "SEARCH_PATHS", ()), \
             redirect_stderr(stderr):
            code = cli.main(["run", str(self.step)])
        self.assertEqual(code, 0)
        self.assertEqual(fakes.read_json(self.step / "etat.json")["status"], "AWAITING_APPROVAL")
        self.assertIn("attention : copie Nextcloud échouée", stderr.getvalue())

    def test_run_and_decide_copy_after_their_local_writes(self) -> None:
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Proposition\nCorps.",)),
            "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        with mock.patch.object(cli, "ADAPTERS", adapters), \
             mock.patch.object(settings, "SEARCH_PATHS", ()):
            self.assertEqual(cli.main(["run", str(self.step)]), 0)
            self.assertEqual(cli.main(["decide", str(self.step), "--accept"]), 0)
        names = [p.name for p in self.cloud.iterdir()]
        self.assertEqual(len(names), 2)
        self.assertTrue(any("__awaiting_approval__" in name for name in names))
        final = next(p for p in self.cloud.iterdir() if "__final__" in p.name)
        self.assertTrue((final / "collaboration" / "decisions.json").is_file())
