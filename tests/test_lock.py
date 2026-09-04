"""Tests de iabinome.lock : identité du verrou, détenteur vivant, verrou mort,
et **courses entre vrais processus** — un comportement d'OS ne se teste pas
contre un objet simulé (RULES.md)."""

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import lock
from iabinome.lock import LockError, LockHeld, LockHolder

# Chaque concurrent attend le top de départ, tente **une** acquisition, garde le
# verrou assez longtemps pour qu'un arrivant tardif le voie détenu, puis écrit
# ce qu'il a obtenu. Les chemins passent par argv : rien à échapper.
_RACER = (
    "import pathlib, sys, time\n"
    "from iabinome import lock\n"
    "verrou, top, resultat = (pathlib.Path(p) for p in sys.argv[1:4])\n"
    "while not top.exists():\n"
    "    time.sleep(0.002)\n"
    "try:\n"
    "    with lock.acquire(verrou, 'course'):\n"
    "        resultat.write_text('acquis', encoding='utf-8')\n"
    "        time.sleep(0.4)\n"
    "except Exception:\n"
    "    if not resultat.exists():\n"
    "        resultat.write_text('refuse', encoding='utf-8')\n"
)
# Le `if not resultat.exists()` n'est pas une précaution : deux entrants font
# échouer la libération de l'un d'eux, et sans lui ce second entrant se
# déclarerait refusé — le test masquerait exactement le défaut qu'il cherche.
# Mesuré le 2026-09-04 contre l'ancien verrou : trois entrants annoncés refusés.


def _dead_pid() -> int:
    """Un PID garanti mort : un sous-processus qu'on attend jusqu'à sa sortie."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def _holder(pid: int, *, lock_id: str = "l0", command: str = "commande") -> str:
    return json.dumps({
        "lock_id": lock_id, "pid": pid,
        "acquired_at": "2026-01-01T00:00:00Z", "command": command,
    })


class LockCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.path = self.root / "verrou.json"
        self.claim = self.root / "verrou.json.recuperation"

    def write_lock(self, pid: int, **kwargs: str) -> None:
        self.path.write_text(_holder(pid, **kwargs), encoding="utf-8")


class TestAcquireRelease(LockCase):
    def test_lock_content_has_id_pid_date_command(self) -> None:
        with lock.acquire(self.path, "python -m iabinome run etude-cache"):
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["pid"], os.getpid())
            self.assertEqual(raw["command"], "python -m iabinome run etude-cache")
            self.assertRegex(raw["acquired_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertRegex(raw["lock_id"], r"^[0-9a-f]{32}$")

    def test_two_acquisitions_have_different_ids(self) -> None:
        with lock.acquire(self.path, "cmd"):
            first = json.loads(self.path.read_text(encoding="utf-8"))["lock_id"]
        with lock.acquire(self.path, "cmd"):
            second = json.loads(self.path.read_text(encoding="utf-8"))["lock_id"]
        self.assertNotEqual(first, second)

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
        self.write_lock(os.getpid(), command="autre commande")
        with self.assertRaises(LockHeld):
            with lock.acquire(self.path, "ma commande"):
                pass
        # Le verrou refusé n'est jamais touché.
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(raw["command"], "autre commande")

    def test_malformed_lock_missing_key_refused(self) -> None:
        self.path.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass

    def test_malformed_lock_extra_key_refused(self) -> None:
        raw = json.loads(_holder(os.getpid()))
        raw["surnumeraire"] = "x"
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass

    def test_malformed_lock_wrong_pid_type_refused(self) -> None:
        self.path.write_text(
            json.dumps({"lock_id": "l0", "pid": "pas-un-entier",
                        "acquired_at": "2026-01-01T00:00:00Z", "command": "c"}),
            encoding="utf-8",
        )
        with self.assertRaises(LockError):
            with lock.acquire(self.path, "cmd"):
                pass


class TestDeadLockReclaim(LockCase):
    def test_dead_holder_lock_reclaimed(self) -> None:
        self.write_lock(_dead_pid(), command="commande abandonnee")
        with lock.acquire(self.path, "ma commande"):
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["pid"], os.getpid())
            self.assertEqual(raw["command"], "ma commande")

    def test_reclaim_leaves_no_token_behind(self) -> None:
        self.write_lock(_dead_pid())
        with lock.acquire(self.path, "ma commande"):
            self.assertFalse(self.claim.exists())
        self.assertFalse(self.claim.exists())

    def test_orphan_token_refuses_and_names_the_file(self) -> None:
        """Le jeton resté d'une récupération interrompue bloque : c'est le prix
        de la sûreté, et le message dit quoi faire."""
        self.write_lock(_dead_pid())
        self.claim.write_text("{}", encoding="utf-8")
        with self.assertRaises(LockHeld) as ctx:
            with lock.acquire(self.path, "cmd"):
                pass
        self.assertIn("verrou.json.recuperation", str(ctx.exception))
        self.assertTrue(self.path.exists())


class TestNeverDeletesAnothersLock(LockCase):
    def test_release_refuses_a_foreign_lock_id_under_our_own_pid(self) -> None:
        """Le PID ne suffit pas : c'est le `lock_id` qui identifie *notre*
        acquisition, sinon un verrou remplacé serait effacé par mégarde."""
        self.write_lock(os.getpid(), lock_id="celui-d-un-autre")
        notre = LockHolder("le-notre", os.getpid(), "2026-01-01T00:00:00Z", "c")
        with self.assertRaises(LockError):
            lock._release(self.path, notre)
        self.assertTrue(self.path.exists())

    def test_body_error_survives_a_failed_release(self) -> None:
        """N-02 : la cause première remonte, l'échec de libération est annoté."""
        with self.assertRaises(ValueError) as ctx:
            with lock.acquire(self.path, "cmd"):
                self.write_lock(os.getpid(), lock_id="remplace-pendant-le-corps")
                raise ValueError("boom")
        self.assertEqual(str(ctx.exception), "boom")
        self.assertIn("verrou non libéré", "".join(ctx.exception.__notes__))
        self.assertTrue(self.path.exists())


class TestRaceBetweenRealProcesses(LockCase):
    """La course est ce que le verrou existe pour perdre : elle se joue entre de
    vrais processus, jamais entre deux objets simulés."""

    def race(self, count: int) -> list[str]:
        top = self.root / "top-depart"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
        results = [self.root / f"resultat-{i}.txt" for i in range(count)]
        procs = [
            subprocess.Popen(
                [sys.executable, "-c", _RACER, str(self.path), str(top), str(r)], env=env
            )
            for r in results
        ]
        time.sleep(0.5)  # laisser chaque enfant atteindre la barrière
        top.write_text("go", encoding="utf-8")
        for proc in procs:
            proc.wait(timeout=60)
        return [
            r.read_text(encoding="utf-8") if r.exists() else "absent" for r in results
        ]

    def test_two_processes_on_a_free_lock_only_one_enters(self) -> None:
        self.assertEqual(sorted(self.race(2)), ["acquis", "refuse"])

    def test_three_processes_on_a_dead_lock_only_one_enters(self) -> None:
        self.write_lock(_dead_pid(), command="commande abandonnee")
        results = self.race(3)
        self.assertEqual(results.count("acquis"), 1, results)
        self.assertNotIn("absent", results)


if __name__ == "__main__":
    unittest.main()
