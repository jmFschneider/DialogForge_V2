"""Tests de iabinome.corpus : manifeste, copie, règles de chemin."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from iabinome import corpus
from iabinome.corpus import CorpusError


class TestCorpusBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workspace = Path(self._tmp.name)
        self.source = self.workspace / "source"
        self.dest = self.workspace / "dest"
        self.source.mkdir()
        self.dest.mkdir()

    def _write_list(self, lines: list[str]) -> Path:
        path = self.workspace / "liste.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


class TestBuild(TestCorpusBase):
    def test_copies_listed_file_and_writes_manifest(self) -> None:
        (self.source / "a.txt").write_bytes(b"hello")
        manifest = corpus.build(
            self.source, self._write_list(["a.txt"]), self.dest, "etude-cache"
        )
        self.assertEqual((self.dest / "fichiers" / "a.txt").read_bytes(), b"hello")
        self.assertEqual(len(manifest.entries), 1)
        entry = manifest.entries[0]
        self.assertEqual(entry.logical_path, "a.txt")
        self.assertEqual(entry.size, 5)
        self.assertEqual(entry.sha256, __import__("hashlib").sha256(b"hello").hexdigest())

    def test_manifest_json_written_to_disk(self) -> None:
        (self.source / "a.txt").write_bytes(b"contenu")
        corpus.build(self.source, self._write_list(["a.txt"]), self.dest, "etude-cache")
        raw = json.loads((self.dest / "manifeste.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["schema_version"], 1)
        self.assertEqual(raw["origin_label"], "etude-cache")
        self.assertEqual(len(raw["files"]), 1)
        self.assertEqual(raw["files"][0]["chemin"], "a.txt")

    def test_captured_at_is_utc_iso8601(self) -> None:
        (self.source / "a.txt").write_bytes(b"x")
        manifest = corpus.build(self.source, self._write_list(["a.txt"]), self.dest, "label")
        self.assertRegex(manifest.captured_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_nested_logical_path_preserved(self) -> None:
        (self.source / "sous").mkdir()
        (self.source / "sous" / "b.txt").write_bytes(b"nested")
        manifest = corpus.build(
            self.source, self._write_list(["sous/b.txt"]), self.dest, "label"
        )
        self.assertEqual((self.dest / "fichiers" / "sous" / "b.txt").read_bytes(), b"nested")
        self.assertEqual(manifest.entries[0].logical_path, "sous/b.txt")

    def test_blank_lines_ignored(self) -> None:
        (self.source / "a.txt").write_bytes(b"x")
        manifest = corpus.build(
            self.source, self._write_list(["", "a.txt", "", ""]), self.dest, "label"
        )
        self.assertEqual(len(manifest.entries), 1)

    def test_empty_list_produces_empty_manifest(self) -> None:
        manifest = corpus.build(self.source, self._write_list([]), self.dest, "label")
        self.assertEqual(manifest.entries, ())

    def test_no_refresh_function_exposed(self) -> None:
        self.assertFalse(hasattr(corpus, "refresh"))


class TestRefusedBeforePublication(TestCorpusBase):
    def test_absolute_path_rejected(self) -> None:
        (self.source / "a.txt").write_bytes(b"x")
        absolute = str((self.source / "a.txt").resolve())
        with self.assertRaises(CorpusError):
            corpus.build(self.source, self._write_list([absolute]), self.dest, "label")

    def test_dotdot_rejected(self) -> None:
        outside = self.workspace / "outside.txt"
        outside.write_bytes(b"secret")
        with self.assertRaises(CorpusError):
            corpus.build(
                self.source, self._write_list(["../outside.txt"]), self.dest, "label"
            )

    def test_missing_file_rejected(self) -> None:
        with self.assertRaises(CorpusError):
            corpus.build(self.source, self._write_list(["absent.txt"]), self.dest, "label")

    def test_directory_listed_rejected(self) -> None:
        (self.source / "sous").mkdir()
        with self.assertRaises(CorpusError):
            corpus.build(self.source, self._write_list(["sous"]), self.dest, "label")

    def test_symlink_outside_root_rejected(self) -> None:
        outside = self.workspace / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        link = self.source / "lien.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("création de lien symbolique non privilégiée sur cette machine")
        with self.assertRaises(CorpusError):
            corpus.build(self.source, self._write_list(["lien.txt"]), self.dest, "label")

    def test_nothing_published_when_one_entry_is_rejected(self) -> None:
        (self.source / "a.txt").write_bytes(b"ok")
        with self.assertRaises(CorpusError):
            corpus.build(
                self.source, self._write_list(["a.txt", "absent.txt"]), self.dest, "label"
            )
        self.assertFalse((self.dest / "manifeste.json").exists())

    def test_changing_file_during_copy_detected(self) -> None:
        source_file = self.source / "a.txt"
        source_file.write_bytes(b"original")
        fichiers_dir = self.dest / "fichiers"
        with patch("pathlib.Path.read_bytes", side_effect=[b"original", b"modifie"]):
            with self.assertRaises(CorpusError):
                corpus._copy_one(self.source.resolve(), "a.txt", fichiers_dir)


if __name__ == "__main__":
    unittest.main()
