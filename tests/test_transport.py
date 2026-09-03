"""Tests de iabinome.transport : deux flux concurrents, sortie vide, code non
nul, délai, arbre terminé, plafond dur, partiel jamais présenté comme complet.

Les enfants sont de vrais sous-processus Python (`tests.fakes`) — jamais un
fournisseur, jamais le réseau."""

import hashlib
import json
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import transport
from iabinome.transport import CallResult, Outcome
from tests import fakes

_REAL_MONOTONIC = time.monotonic
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class _InterruptOnSecondCall:
    """Simule un Ctrl-C pendant l'attente : le deuxième relevé d'horloge lève.

    C'est le premier que fait la boucle d'attente ; les suivants rendent l'heure
    réelle, pour ne pas dérégler la terminaison qui suit."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        if self.calls == 2:
            raise KeyboardInterrupt
        return _REAL_MONOTONIC()


class TransportCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.call_dir = self.root / "appels" / "0001-A-uuid"
        self.call_dir.mkdir(parents=True)

    def run_fake(self, *, timeout_seconds: float = 30.0, **kwargs: Any) -> CallResult:
        return transport.run(
            fakes.command(**kwargs),
            cwd=self.root,
            call_dir=self.call_dir,
            timeout_seconds=timeout_seconds,
        )

    def read(self, name: str) -> bytes:
        return (self.call_dir / name).read_bytes()


class TestCleanExit(TransportCase):
    def test_both_streams_captured(self) -> None:
        result = self.run_fake(stdout="proposition", stderr="avertissement")
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(self.read("stdout.txt"), b"proposition")
        self.assertEqual(self.read("stderr.txt"), b"avertissement")

    def test_empty_output(self) -> None:
        result = self.run_fake()
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertEqual((result.stdout_bytes, result.stderr_bytes), (0, 0))
        self.assertEqual(result.stdout_sha256, _EMPTY_SHA256)
        self.assertEqual(self.read("stdout.txt"), b"")

    def test_non_zero_return_code_is_still_a_clean_exit(self) -> None:
        result = self.run_fake(stderr="quota", exit_code=3)
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertEqual(result.return_code, 3)
        self.assertIsNotNone(transport.read_result(self.call_dir))

    def test_two_large_concurrent_streams(self) -> None:
        """Un lecteur qui ne draine qu'un tube à la fois s'interbloquerait ici."""
        size = 1 << 20
        result = self.run_fake(stdout_bytes=size, stderr_bytes=size, rounds=16)
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertEqual(result.stdout_bytes, size)
        self.assertEqual(result.stderr_bytes, size)
        self.assertEqual(self.read("stdout.txt"), b"x" * size)
        self.assertEqual(self.read("stderr.txt"), b"y" * size)

    def test_sizes_and_hashes_match_the_files(self) -> None:
        result = self.run_fake(stdout="document", stderr="note")
        self.assertEqual(result.stdout_bytes, len(self.read("stdout.txt")))
        self.assertEqual(result.stdout_sha256, hashlib.sha256(self.read("stdout.txt")).hexdigest())
        self.assertEqual(result.stderr_sha256, hashlib.sha256(self.read("stderr.txt")).hexdigest())

    def test_cwd_is_the_collaboration(self) -> None:
        """Le `cwd` transmis est bien le dossier de collaboration. Cela ne
        prétend pas tester une isolation : `cwd` n'est pas un bac à sable de
        lecture, et la spécification le dit (§1, frontière d'effets)."""
        result = transport.run(
            [sys.executable, "-c", "import pathlib; pathlib.Path('temoin.txt').write_text('ici')"],
            cwd=self.root,
            call_dir=self.call_dir,
            timeout_seconds=30.0,
        )
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertTrue((self.root / "temoin.txt").exists())


class TestPidFile(TransportCase):
    def test_pid_written_even_when_the_call_never_completes(self) -> None:
        """`pid.txt` est écrit dès le retour de Popen, pas à la fin."""
        result = self.run_fake(sleep_seconds=30.0, timeout_seconds=0.5)
        self.assertIs(result.outcome, Outcome.TIMEOUT)
        self.assertGreater(int(self.read("pid.txt")), 0)


class TestHardTimeout(TransportCase):
    def test_timeout_terminates_and_keeps_partial_streams(self) -> None:
        result = self.run_fake(stdout="partiel", sleep_seconds=30.0, timeout_seconds=1.0)
        self.assertIs(result.outcome, Outcome.TIMEOUT)
        self.assertLess(result.duration_seconds, 15.0)
        self.assertEqual(self.read("stdout.txt"), b"partiel")

    def test_timeout_writes_no_result(self) -> None:
        self.run_fake(sleep_seconds=30.0, timeout_seconds=0.5)
        self.assertFalse((self.call_dir / "resultat.json").exists())
        self.assertIsNone(transport.read_result(self.call_dir))


class TestOutputLimit(TransportCase):
    def test_limit_is_eight_mebibytes_without_option(self) -> None:
        self.assertEqual(transport.OUTPUT_LIMIT_BYTES, 8 * 1024 * 1024)

    def test_overflow_truncates_terminates_and_writes_no_result(self) -> None:
        result = transport.run(
            fakes.command(stdout_bytes=5000, sleep_seconds=30.0),
            cwd=self.root,
            call_dir=self.call_dir,
            timeout_seconds=30.0,
            limit_bytes=1024,
        )
        self.assertIs(result.outcome, Outcome.OUTPUT_LIMIT)
        self.assertEqual(result.stdout_bytes, 1024)
        self.assertEqual(len(self.read("stdout.txt")), 1024)
        self.assertLess(result.duration_seconds, 15.0)
        self.assertFalse((self.call_dir / "resultat.json").exists())

    def test_output_exactly_at_the_limit_is_not_an_overflow(self) -> None:
        result = transport.run(
            fakes.command(stdout_bytes=1024),
            cwd=self.root,
            call_dir=self.call_dir,
            timeout_seconds=30.0,
            limit_bytes=1024,
        )
        self.assertIs(result.outcome, Outcome.COMPLETED)
        self.assertEqual(result.stdout_bytes, 1024)


class TestProcessTree(TransportCase):
    def test_timeout_terminates_the_whole_tree(self) -> None:
        """Le petit-fils ne doit jamais déposer sa marque : tuer le seul enfant
        laisserait l'arbre vivant."""
        marker = self.root / "petit-fils.txt"
        result = self.run_fake(
            child_marker=str(marker),
            child_delay_seconds=2.0,
            sleep_seconds=30.0,
            timeout_seconds=0.5,
        )
        self.assertIs(result.outcome, Outcome.TIMEOUT)
        time.sleep(3.0)
        self.assertFalse(marker.exists(), "un descendant a survecu a la terminaison")


class TestInterruption(TransportCase):
    def test_ctrl_c_terminates_and_keeps_the_call_incomplete(self) -> None:
        with mock.patch("iabinome.transport.time.monotonic", new=_InterruptOnSecondCall()):
            result = self.run_fake(stdout="debut", sleep_seconds=30.0)
        self.assertIs(result.outcome, Outcome.INTERRUPTED_BY_USER)
        self.assertTrue((self.call_dir / "pid.txt").exists())
        self.assertTrue((self.call_dir / "stdout.txt").exists())
        self.assertFalse((self.call_dir / "resultat.json").exists())


class TestReadResult(TransportCase):
    def _written(self) -> dict[str, object]:
        self.run_fake(stdout="document", exit_code=0)
        raw = json.loads((self.call_dir / "resultat.json").read_text(encoding="utf-8"))
        assert isinstance(raw, dict)
        return raw

    def _write(self, raw: object) -> None:
        (self.call_dir / "resultat.json").write_text(
            json.dumps(raw, ensure_ascii=False), encoding="utf-8"
        )

    def test_roundtrip(self) -> None:
        written = self.run_fake(stdout="document")
        reread = transport.read_result(self.call_dir)
        self.assertEqual(reread, written)

    def test_absent_is_none(self) -> None:
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_unreadable_is_none(self) -> None:
        (self.call_dir / "resultat.json").write_text("{ pas du json", encoding="utf-8")
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_future_schema_version_is_none(self) -> None:
        raw = self._written()
        raw["schema_version"] = 2
        self._write(raw)
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_extra_key_is_none(self) -> None:
        raw = self._written()
        raw["cout_estime"] = 42
        self._write(raw)
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_missing_key_is_none(self) -> None:
        raw = self._written()
        del raw["stdout_sha256"]
        self._write(raw)
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_wrong_type_is_none(self) -> None:
        raw = self._written()
        raw["return_code"] = "0"
        self._write(raw)
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_boolean_is_not_an_integer(self) -> None:
        raw = self._written()
        raw["return_code"] = True
        self._write(raw)
        self.assertIsNone(transport.read_result(self.call_dir))

    def test_integer_duration_is_tolerated(self) -> None:
        raw = self._written()
        raw["duration_seconds"] = 1
        self._write(raw)
        reread = transport.read_result(self.call_dir)
        assert reread is not None
        self.assertEqual(reread.duration_seconds, 1.0)

    def test_reread_result_is_always_completed(self) -> None:
        """Un `resultat.json` valide ne peut signifier qu'une sortie propre :
        c'est ce sur quoi la reprise conclut « flux complets » (§5)."""
        self.run_fake(stdout="document", exit_code=7)
        reread = transport.read_result(self.call_dir)
        assert reread is not None
        self.assertIs(reread.outcome, Outcome.COMPLETED)


if __name__ == "__main__":
    unittest.main()
