"""Un écran qui n'existe pas encore, nommé honnêtement plutôt qu'un bouton sans
effet — l'écran de création (lot 4) en a besoin tant qu'il n'est pas construit.
"""

from __future__ import annotations

from tkinter import Misc, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller import Controller


class StubView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller, message: str) -> None:
        super().__init__(master)
        self._controller = controller
        ttk.Label(self, text=message, padding=16).pack()
        ttk.Button(self, text="Retour à l'accueil", command=controller.show_accueil).pack()
