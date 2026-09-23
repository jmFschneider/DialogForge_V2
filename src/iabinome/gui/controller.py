"""Contrôleur GUI (`conception/GUI_V1.md` §10.4) : navigation dans une seule
fenêtre, préférences non métier. Lot 3, lecture seule — il ne possède ni fil
moteur ni `ExecutionControl` : rien ne les consommerait encore (`workflow.run`
n'est appelé qu'à partir du lot 5). Il ne construit ni `etat.json`, ni
incident, ni décision — seule la façade lit le dossier.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import Tk, messagebox, ttk

from .. import facade
from . import recents


class Controller:
    def __init__(self, root: Tk, *, recents_path: Path = recents.DEFAULT_PATH) -> None:
        self.root = root
        self.recents_path = recents_path
        self._frame: ttk.Frame | None = None

    # -- Navigation : les vues remplacent le contenu de la même fenêtre (§4) --

    def _swap(self, build: Callable[[], ttk.Frame]) -> None:
        if self._frame is not None:
            self._frame.destroy()
        self._frame = build()
        self._frame.pack(fill="both", expand=True)

    def show_accueil(self) -> None:
        from .views.accueil import AccueilView

        self._swap(lambda: AccueilView(self.root, self))

    def show_suivi(self, path: Path) -> None:
        from .views.suivi import SuiviView

        self._swap(lambda: SuiviView(self.root, self, path))

    def show_creation_stub(self) -> None:
        """Le formulaire de création est livré au lot 4 : un repère honnête
        plutôt qu'un bouton silencieusement sans effet."""
        from .views.stub import StubView

        self._swap(lambda: StubView(
            self.root, self, "Écran de création de collaboration — livré au lot 4.",
        ))

    # -- Ouverture, strictement en lecture (§5.1, AC-02) --

    def open_collaboration(self, path: Path) -> None:
        try:
            self.inspect(path)
        except facade.InspectionError as exc:
            messagebox.showerror("Dossier introuvable ou invalide", str(exc))
            return
        recents.record_opened(path, self.recents_path)
        self.show_suivi(path)

    def inspect(self, path: Path) -> facade.CollaborationSnapshot:
        return facade.inspect_collaboration(path)

    def recent_entries(self) -> tuple[recents.Recent, ...]:
        return recents.load(self.recents_path)
