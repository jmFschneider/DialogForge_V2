"""Tests de iabinome.storage : écriture atomique, BOM toléré, résistance au déplacement."""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from iabinome.storage import read_text, write_atomic_bytes, write_atomic_text


class TestWriteAtomicText(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.target = self.dir / "etat.json"

    def test_creates_file_with_exact_content(self) -> None:
        write_atomic_text(self.target, "{}\n")
        self.assertEqual(self.target.read_bytes(), b"{}\n")

    def test_no_bom_written(self) -> None:
        write_atomic_text(self.target, "contenu\n")
        self.assertFalse(self.target.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_no_carriage_return_introduced(self) -> None:
        write_atomic_text(self.target, "ligne1\nligne2\n")
        self.assertNotIn(b"\r", self.target.read_bytes())

    def test_overwrite_replaces_content_fully(self) -> None:
        write_atomic_text(self.target, "ancien\n")
        write_atomic_text(self.target, "nouveau\n")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "nouveau\n")

    def test_no_stray_temp_file_after_success(self) -> None:
        write_atomic_text(self.target, "contenu\n")
        self.assertEqual(list(self.dir.iterdir()), [self.target])

    def test_content_never_leaks_absolute_temp_path(self) -> None:
        write_atomic_text(self.target, "contenu\n")
        content = self.target.read_text(encoding="utf-8")
        self.assertNotIn(str(self.dir), content)

    def test_survives_directory_move_then_read(self) -> None:
        write_atomic_text(self.target, "contenu\n")
        moved = self.dir.parent / "collaboration-deplacee"
        shutil.move(str(self.dir), str(moved))
        self.addCleanup(shutil.rmtree, moved, ignore_errors=True)
        text, had_bom = read_text(moved / "etat.json")
        self.assertEqual(text, "contenu\n")
        self.assertFalse(had_bom)


class TestFailureBeforeReplace(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.target = self.dir / "etat.json"

    def test_fsync_failure_leaves_target_untouched(self) -> None:
        write_atomic_text(self.target, "ancien\n")
        with patch("iabinome.storage.os.fsync", side_effect=OSError("disque plein")):
            with self.assertRaises(OSError):
                write_atomic_text(self.target, "nouveau\n")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "ancien\n")

    def test_fsync_failure_leaves_no_temp_file(self) -> None:
        with patch("iabinome.storage.os.fsync", side_effect=OSError("disque plein")):
            with self.assertRaises(OSError):
                write_atomic_text(self.target, "contenu\n")
        self.assertEqual(list(self.dir.iterdir()), [])


class TestFailureAfterReplace(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.target = self.dir / "etat.json"

    def test_directory_fsync_failure_does_not_undo_publication(self) -> None:
        with patch("iabinome.storage._fsync_dir", side_effect=OSError("indisponible")):
            with self.assertRaises(OSError):
                write_atomic_text(self.target, "contenu\n")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "contenu\n")


class TestReadText(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_bom_tolerated_stripped_and_reported(self) -> None:
        path = self.dir / "demande.md"
        path.write_bytes(b"\xef\xbb\xbfcontenu\n")
        text, had_bom = read_text(path)
        self.assertEqual(text, "contenu\n")
        self.assertTrue(had_bom)

    def test_no_bom_reported_false(self) -> None:
        path = self.dir / "demande.md"
        path.write_bytes(b"contenu\n")
        text, had_bom = read_text(path)
        self.assertEqual(text, "contenu\n")
        self.assertFalse(had_bom)


class TestUniqueTempFiles(unittest.TestCase):
    def test_successive_writes_leave_a_single_final_file(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "etat.json"
            for i in range(5):
                write_atomic_bytes(target, f"{i}".encode())
            self.assertEqual(list(Path(tmp).iterdir()), [target])
            self.assertEqual(target.read_bytes(), b"4")


if __name__ == "__main__":
    unittest.main()
