"""Point d'entrée de la GUI V1 — une fenêtre, une collaboration, une exécution
au maximum (`conception/GUI_V1.md` §3.1). Appelé par `dialogforge gui`.
"""

from __future__ import annotations

import tkinter as tk

from .controller import Controller

_TITLE = "DialogForge"
_MIN_SIZE = (720, 480)


def run() -> None:
    root = tk.Tk()
    root.title(_TITLE)
    root.minsize(*_MIN_SIZE)
    controller = Controller(root)
    controller.show_accueil()
    root.mainloop()
