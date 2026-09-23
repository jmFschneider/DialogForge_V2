"""GUI V1, lot 3 : les récents sont un fichier de préférences non métier
(`conception/GUI_V1.md` §5.2, AC-05) — jamais lu par une commande de la CLI,
sans effet sur les collaborations si on le supprime.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome.gui import recents


class RecentsCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.prefs = Path(self._tmp.name) / "prefs" / "recents.json"


class TestRecording(RecentsCase):
    def test_an_absent_file_is_an_empty_list(self) -> None:
        self.assertEqual(recents.load(self.prefs), ())

    def test_recording_a_path_makes_it_the_first_recent(self) -> None:
        path = Path(self._tmp.name) / "collab-1"
        updated = recents.record_opened(path, self.prefs)
        self.assertEqual(updated[0].path, path.resolve())
        self.assertEqual(recents.load(self.prefs), updated)

    def test_reopening_moves_it_back_to_the_front_without_a_duplicate(self) -> None:
        a = Path(self._tmp.name) / "collab-a"
        b = Path(self._tmp.name) / "collab-b"
        recents.record_opened(a, self.prefs)
        recents.record_opened(b, self.prefs)
        updated = recents.record_opened(a, self.prefs)
        self.assertEqual([r.path for r in updated], [a.resolve(), b.resolve()])

    def test_the_list_is_bounded(self) -> None:
        for i in range(5):
            recents.record_opened(Path(self._tmp.name) / f"collab-{i}", self.prefs, max_entries=3)
        self.assertEqual(len(recents.load(self.prefs)), 3)
        # Les trois plus récents, dans cet ordre.
        self.assertEqual(
            [r.path.name for r in recents.load(self.prefs)], ["collab-4", "collab-3", "collab-2"],
        )

    def test_removing_the_file_affects_no_collaboration(self) -> None:
        collab = Path(self._tmp.name) / "collab"
        collab.mkdir()
        (collab / "temoin.txt").write_text("intact", encoding="utf-8")
        recents.record_opened(collab, self.prefs)
        self.prefs.unlink()
        self.assertEqual(recents.load(self.prefs), ())
        self.assertEqual((collab / "temoin.txt").read_text(encoding="utf-8"), "intact")


class TestReadingIsForgiving(RecentsCase):
    def test_a_corrupted_file_is_read_as_empty_rather_than_raising(self) -> None:
        self.prefs.parent.mkdir(parents=True)
        self.prefs.write_text("{ceci n'est pas du JSON", encoding="utf-8")
        self.assertEqual(recents.load(self.prefs), ())

    def test_a_wrong_shape_is_read_as_empty_rather_than_raising(self) -> None:
        self.prefs.parent.mkdir(parents=True)
        self.prefs.write_text('{"schema_version": 1, "recents": "pas une liste"}', encoding="utf-8")
        self.assertEqual(recents.load(self.prefs), ())
