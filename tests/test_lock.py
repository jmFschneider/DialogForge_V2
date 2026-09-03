"""Tests de iabinome.lock : PID/date/commande, détenteur vivant, verrou mort."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import lock
from iabinome.lock import LockError, LockHeld


def _dead_pid() -> int:
    """Un PID garanti mort : un sous-processus qu'on attend jusqu'à sa sortie."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


class TestAcquireRelease(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "verrou.json"

    def test_lock_content_has_pid_date_command(self) -> None:
        with lock.acquire(self.path, "python -m iabinome run etude-cache"):
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["pid"], os.getpid())
            self.assertEqual(raw["command"], "python -m iabinome run etude-cache")
            self.assertRegex(raw["acquired_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_release_on_normal_exit_removes_file(self) -> None:
        with lock.acquire(self.path, "cmd"):
            self.assertTrue(self.path.exists())
        self.assertFalse(self.path.exists())

    def test_release_on_exception_still_removes_file(self) -> None:
        with self.assertRaises(ValueError):
            with lock.acquire(self.path, "cmd"):
                raise ValueError("boom")
        self.assertFalse(self.path.exists())

    def test_alive_holder_refused(self) -> None:
        self.path.write_text(
            json.dumps({"pid": os.getpid(), "acquired_at": "2026-01-01T00:00:00Z",
                        "command": "autre commande"}),
            encoding="utf-8",
        )
        with self.assertRaises(LockHeld):
            with lock.acquire(self.path, "ma commande"):
                pass
        # Le verrou refusé n'est jamais touché.
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(raw["command"], "autre commande")

    def test_dead_holder_lock_reclaimed(self) -> None:
        dead_pid = _dead_pid()
        self.path.write_text(
            json.dumps({"pid": dead_pid, "acquired_at": "2026-01-01T00:00:00Z",
                        "command": "commande abandonnee"}),
            encoding="utf-8",
        )
        with lock.acquire(self.path, "ma commande"):
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["pid"], os.getpid())
            self.assertEqual(raw["command"], "ma commande")

    def test_malformed_lock_missing_key_refused(self) -> None:
        self.path.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass

    def test_malformed_lock_extra_key_refused(self) -> None:
        self.path.write_text(
            json.dumps({"pid": os.getpid(), "acquired_at": "2026-01-01T00:00:00Z",
                        "command": "c", "surnumeraire": "x"}),
            encoding="utf-8",
        )
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass

    def test_malformed_lock_wrong_pid_type_refused(self) -> None:
        self.path.write_text(
            json.dumps({"pid": "pas-un-entier", "acquired_at": "2026-01-01T00:00:00Z",
                        "command": "c"}),
            encoding="utf-8",
        )
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass


class TestNeverDeletesAnothersLock(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "verrou.json"

    def test_release_refuses_foreign_pid(self) -> None:
        foreign_pid = os.getpid() + 1
        self.path.write_text(
            json.dumps({"pid": foreign_pid, "acquired_at": "2026-01-01T00:00:00Z",
                        "command": "commande d'un autre"}),
            encoding="utf-8",
        )
        with self.assertRaises(LockError):
            lock._release(self.path)
        self.assertTrue(self.path.exists())


if __name__ == "__main__":
    unittest.main()
