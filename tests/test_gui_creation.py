"""GUI V1, lot 4 : l'écran de création (`conception/GUI_V1.md` §6), derrière
la racine Tk masquée déjà partagée par `tests/test_gui_views.py` (§15.2).

La validation autoritaire vient de `facade.create_collaboration`, déjà testée
sans Tk dans `tests/test_facade_creation.py` ; ici, on éprouve que l'écran lui
transmet la bonne requête, et rien de plus (AC-06 à AC-14).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome.gui.controller import Controller
from iabinome.gui.views.creation import CreationView
from iabinome.gui.views.suivi import SuiviView
from tests import fakes
from tests.test_gui_views import _ROOT, _find_button, collect_tk_garbage

_ADAPTERS = {"fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ())}


class CreationCase(unittest.TestCase):
    def setUp(self) -> None:
        collect_tk_garbage()
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root_dir = Path(self._tmp.name)
        self.controller = Controller(_ROOT, recents_path=self.root_dir / "recents.json")
        self.addCleanup(lambda: [c.destroy() for c in list(_ROOT.winfo_children())])
        for target in ("iabinome.gui.views.creation.ADAPTERS", "iabinome.gui.controller.ADAPTERS"):
            patcher = mock.patch(target, _ADAPTERS)
            patcher.start()
            self.addCleanup(patcher.stop)

    def view(self) -> CreationView:
        return CreationView(_ROOT, self.controller)

    def fill_minimum(self, view: CreationView, *, dest: Path | None = None) -> None:
        view._dossier.set(str(dest or self.root_dir / "ma-collab"))
        view._demande_text.insert("1.0", "Concevoir le cache de FloraPi.")
        view._agent_a.set("fake-a")
        view._agent_b.set("fake-b")


class TestTheDemandeIsAlwaysVisible(CreationCase):
    """AC-06 : saisissable ou importable, toujours visible avant création."""

    def test_typed_text_stays_in_the_box(self) -> None:
        view = self.view()
        view._demande_text.insert("1.0", "Un objectif tape a la main.")
        self.assertIn("Un objectif", view._current_text())

    def test_direct_entry_is_provenance_cadrage(self) -> None:
        view = self.view()
        view._demande_text.insert("1.0", "Un objectif.")
        source = view._demande_source()
        self.assertEqual(source.origin, "cadrage")
        self.assertIsNone(source.imported_path)

    def test_an_unmodified_import_is_provenance_fichier(self) -> None:
        imported = self.root_dir / "demande-source.md"
        imported.write_text("Contenu importe.", encoding="utf-8")
        view = self.view()
        with mock.patch(
            "iabinome.gui.views.creation.filedialog.askopenfilename",
            return_value=str(imported),
        ):
            _find_button(view, "Importer…").invoke()
        source = view._demande_source()
        self.assertEqual(source.origin, "fichier")
        self.assertEqual(source.imported_path, str(imported))
        self.assertIn("Contenu importe.", view._current_text())

    def test_a_modified_import_reverts_to_provenance_cadrage(self) -> None:
        """AC-07 : un import modifié est persisté avec la provenance `cadrage`."""
        imported = self.root_dir / "demande-source.md"
        imported.write_text("Contenu importe.", encoding="utf-8")
        view = self.view()
        with mock.patch(
            "iabinome.gui.views.creation.filedialog.askopenfilename",
            return_value=str(imported),
        ):
            _find_button(view, "Importer…").invoke()
        view._demande_text.insert("end", " Et un ajout.")
        source = view._demande_source()
        self.assertEqual(source.origin, "cadrage")
        self.assertIsNone(source.imported_path)


class TestTheCorpusBlock(CreationCase):
    def test_the_corpus_block_is_hidden_for_conception(self) -> None:
        """AC-08 : le corpus n'apparaît qu'en recherche."""
        view = self.view()
        self.assertEqual(view._corpus_frame.winfo_manager(), "")

    def test_the_corpus_block_appears_for_recherche(self) -> None:
        view = self.view()
        view._kind.set("Recherche")
        view._toggle_kind()
        self.assertEqual(view._corpus_frame.winfo_manager(), "pack")


class TestCreateOnly(CreationCase):
    def test_it_produces_a_ready_collaboration_with_zero_calls(self) -> None:
        """AC-13 : `READY`, zéro appel."""
        view = self.view()
        self.fill_minimum(view)
        with mock.patch("iabinome.gui.views.creation.messagebox.showinfo"):
            _find_button(view, "Créer seulement").invoke()
        collab = self.root_dir / "ma-collab"
        self.assertTrue(collab.is_dir())
        etat = fakes.read_json(collab / "etat.json")
        self.assertEqual(etat["status"], "READY")
        self.assertEqual(fakes.launched_calls(collab), 0)
        self.assertIsInstance(self.controller._frame, SuiviView)

    def test_an_empty_destination_is_refused_locally_and_creates_nothing(self) -> None:
        """AC-12 : un refus ne laisse aucun dossier partiel."""
        view = self.view()
        view._demande_text.insert("1.0", "Un objectif.")
        _find_button(view, "Créer seulement").invoke()
        self.assertEqual(view._error.cget("text"), "Le dossier est requis.")
        self.assertEqual(list(self.root_dir.iterdir()), [])

    def test_an_authoritative_refusal_is_shown_and_the_form_stays(self) -> None:
        existing = self.root_dir / "deja-la"
        existing.mkdir()
        view = self.view()
        self.fill_minimum(view, dest=existing)
        _find_button(view, "Créer seulement").invoke()
        self.assertIn("existe", view._error.cget("text"))
        self.assertIsNone(self.controller._frame)


class TestCreateAndStart(CreationCase):
    """AC-14 : la création locale et le lancement payant restent distincts."""

    def test_cancelling_the_confirmation_creates_nothing(self) -> None:
        view = self.view()
        self.fill_minimum(view)
        with mock.patch("iabinome.gui.views.creation.dialogs.confirm", return_value=False):
            _find_button(view, "Créer et démarrer").invoke()
        self.assertEqual(list(self.root_dir.iterdir()), [])
        self.assertIsNone(self.controller._frame)

    def test_the_confirmation_names_the_agent_phase_and_delay(self) -> None:
        """AC-11 : origine et valeur du délai affichées avant tout appel possible."""
        view = self.view()
        self.fill_minimum(view)
        with mock.patch(
            "iabinome.gui.views.creation.dialogs.confirm", return_value=False,
        ) as confirm:
            _find_button(view, "Créer et démarrer").invoke()
        (_, _, body), _ = confirm.call_args
        self.assertIn("fake-a", body)
        self.assertIn("proposition initiale", body)
        self.assertIn("Délai effectif", body)
        self.assertIn("Origine", body)

    def test_confirming_creates_then_navigates_and_starts_the_run(self) -> None:
        view = self.view()
        self.fill_minimum(view)
        with mock.patch("iabinome.gui.views.creation.dialogs.confirm", return_value=True), \
             mock.patch.object(Controller, "start_run") as start_run:
            _find_button(view, "Créer et démarrer").invoke()
        collab = self.root_dir / "ma-collab"
        self.assertTrue(collab.is_dir(), "la collaboration locale n'a pas ete creee")
        self.assertIsInstance(self.controller._frame, SuiviView)
        start_run.assert_called_once()
        (path,), kwargs = start_run.call_args
        self.assertEqual(path, collab)
        self.assertGreater(kwargs["timeout_seconds"], 0)

    def test_the_timeout_is_never_written_to_the_configuration(self) -> None:
        """AC-10."""
        view = self.view()
        self.fill_minimum(view)
        view._timeout_override.set("120")
        with mock.patch("iabinome.gui.views.creation.dialogs.confirm", return_value=True), \
             mock.patch.object(Controller, "start_run"):
            _find_button(view, "Créer et démarrer").invoke()
        config_text = (self.root_dir / "ma-collab" / "configuration.json").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("timeout", config_text)
