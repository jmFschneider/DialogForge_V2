"""GUI V1, lot 3 : vues Tkinter/ttk, éprouvées derrière une racine Tk masquée
(`conception/GUI_V1.md` §15.2 : « racine Tk masquée lorsque possible »).

L'écran de suivi est strictement en lecture seule à ce lot : ces tests
n'invoquent jamais `workflow.run` depuis la GUI — seulement pour construire des
collaborations de départ, comme `tests/fakes.py` le fait déjà ailleurs.
"""

from __future__ import annotations

import gc
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import ttk
from unittest import mock

from iabinome import decisions, workflow
from iabinome.gui import recents
from iabinome.gui.controller import Controller
from iabinome.gui.views.accueil import AccueilView
from iabinome.gui.views.creation import CreationView
from iabinome.gui.views.suivi import SuiviView
from tests import fakes

# Racine masquée, partagée par le module : mesuré fonctionnel sous Windows
# (`task_plan.md`, reprise du lot 3). Une machine sans affichage ferait échouer
# l'import du module entier, pas un test un par un — cohérent avec le reste de
# la suite, qui ne masque pas les dépendances de plateforme.
_ROOT = tk.Tk()
_ROOT.withdraw()


def collect_tk_garbage() -> None:
    """À appeler avant tout test qui lance un fil moteur. Les vues des tests précédents
    laissent des `tkinter.Variable` en cycles de références ; si le ramasse-miettes les
    finalise dans le fil moteur, chaque `Variable.__del__` appelle Tk hors du fil
    principal, qui ne tourne pas `mainloop()` ici : « main thread is not in main loop »,
    un appel retardé, et le cycle finit `INTERRUPTED` (mesuré le 2026-09-25, 6 fois sur 6
    sur `pytest tests -k "(gui or framing) and not cadrage"`). En production,
    `mainloop()` tourne et Tk route ces appels : le défaut n'existe que dans les tests."""
    gc.collect()


def _find_button(widget: tk.Misc, text: str) -> ttk.Button:
    for child in widget.winfo_children():
        if isinstance(child, ttk.Button) and str(child.cget("text")) == text:
            return child
        try:
            return _find_button(child, text)
        except LookupError:
            continue
    raise LookupError(f"bouton introuvable : {text!r}")


class ViewCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root_dir = Path(self._tmp.name)
        self.prefs = self.root_dir / "recents.json"
        self.controller = Controller(_ROOT, recents_path=self.prefs)
        self.addCleanup(lambda: [c.destroy() for c in list(_ROOT.winfo_children())])

    def fresh_collaboration(self) -> Path:
        return fakes.collaboration(self.root_dir)

    def accepted_collaboration(self) -> Path:
        collab = fakes.collaboration(self.root_dir)
        a = fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Proposition\nCorps du document.",))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        workflow.decide(collab, decisions.ACCEPTED)
        return collab


class TestAccueilView(ViewCase):
    def test_it_lists_recents_with_their_situation_read_from_disk(self) -> None:
        collab = self.fresh_collaboration()
        missing = self.root_dir / "disparu"
        recents.record_opened(missing, self.prefs)
        recents.record_opened(collab, self.prefs)
        view = AccueilView(_ROOT, self.controller)
        rows = [view._table.item(row, "values") for row in view._table.get_children()]
        situations = {row[0]: row[1] for row in rows}
        self.assertEqual(situations[collab.name], "Prête")
        self.assertEqual(situations["disparu"], "Dossier introuvable")

    def test_opening_the_selected_recent_navigates_to_the_tracking_screen(self) -> None:
        collab = self.fresh_collaboration()
        recents.record_opened(collab, self.prefs)
        self.controller.show_accueil()
        view = self.controller._frame
        assert isinstance(view, AccueilView)
        row = view._table.get_children()[0]
        view._table.selection_set(row)
        view._open_selected()
        self.assertIsInstance(self.controller._frame, SuiviView)

    def test_the_open_button_opens_the_chosen_folder(self) -> None:
        collab = self.fresh_collaboration()
        self.controller.show_accueil()
        view = self.controller._frame
        assert isinstance(view, AccueilView)
        with mock.patch(
            "iabinome.gui.views.accueil.filedialog.askdirectory", return_value=str(collab),
        ):
            _find_button(view, "Ouvrir une collaboration…").invoke()
        self.assertIsInstance(self.controller._frame, SuiviView)

    def test_an_invalid_chosen_folder_is_named_and_the_accueil_stays(self) -> None:
        self.controller.show_accueil()
        view = self.controller._frame
        assert isinstance(view, AccueilView)
        invalid = self.root_dir / "pas-une-collaboration"
        invalid.mkdir()
        with mock.patch(
            "iabinome.gui.views.accueil.filedialog.askdirectory", return_value=str(invalid),
        ), mock.patch("iabinome.gui.controller.messagebox.showerror") as show_error:
            _find_button(view, "Ouvrir une collaboration…").invoke()
        show_error.assert_called_once()
        self.assertIs(self.controller._frame, view)

    def test_the_new_collaboration_button_opens_the_creation_form(self) -> None:
        self.controller.show_accueil()
        view = self.controller._frame
        assert isinstance(view, AccueilView)
        _find_button(view, "Nouvelle collaboration").invoke()
        self.assertIsInstance(self.controller._frame, CreationView)


class TestSuiviView(ViewCase):
    def test_it_shows_the_accepted_substate_and_lists_documents(self) -> None:
        collab = self.accepted_collaboration()
        view = SuiviView(_ROOT, self.controller, collab)
        self.assertIn("Version acceptée", str(view._title.cget("text")))
        names = [str(child.cget("text")) for child in view._documents_row.winfo_children()]
        self.assertIn(Path(decisions.DELIVERED).name, names)

    def test_an_acceptance_that_no_longer_applies_names_what_changed(self) -> None:
        collab = self.accepted_collaboration()
        demande = collab / "demande.md"
        demande.write_bytes(demande.read_bytes() + b"\nAjout hors cycle.\n")
        view = SuiviView(_ROOT, self.controller, collab)
        self.assertNotIn("Version acceptée", str(view._title.cget("text")))
        self.assertIn("porte sur une version antérieure : la demande a changé",
                      str(view._result.cget("text")))

    def test_clicking_a_document_shows_its_content_read_only(self) -> None:
        collab = self.accepted_collaboration()
        view = SuiviView(_ROOT, self.controller, collab)
        _find_button(view._documents_row, Path(decisions.DELIVERED).name).invoke()
        content = view._viewer.get("1.0", "end-1c")
        self.assertIn("Proposition", content)
        self.assertEqual(str(view._viewer.cget("state")), "disabled")

    def test_refresh_rereads_the_folder_without_writing_anything(self) -> None:
        collab = self.accepted_collaboration()
        view = SuiviView(_ROOT, self.controller, collab)
        before = (collab / "etat.json").read_bytes()
        view._refresh()
        self.assertEqual((collab / "etat.json").read_bytes(), before)

    def test_a_fresh_collaboration_shows_ready_and_no_incident(self) -> None:
        collab = self.fresh_collaboration()
        view = SuiviView(_ROOT, self.controller, collab)
        self.assertIn("Prête", str(view._title.cget("text")))
        self.assertNotIn("Incident", str(view._activity.cget("text")))

    def test_an_invalid_folder_is_named_without_crashing(self) -> None:
        missing = self.root_dir / "disparu"
        view = SuiviView(_ROOT, self.controller, missing)
        self.assertIn("Dossier illisible", str(view._subtitle.cget("text")))

    def test_the_back_button_returns_to_the_accueil(self) -> None:
        collab = self.accepted_collaboration()
        view = SuiviView(_ROOT, self.controller, collab)
        _find_button(view, "Retour à l'accueil").invoke()
        self.assertIsInstance(self.controller._frame, AccueilView)
