"""Point d'entrée de la GUI V1 — une fenêtre, une collaboration, une exécution
au maximum (`conception/GUI_V1.md` §3.1). Appelé par `dialogforge gui`.
"""

from __future__ import annotations

import tkinter as tk

from . import dialogs
from .controller import Controller

_TITLE = "DialogForge"
_MIN_SIZE = (720, 480)

_CLOSE_BODY = (
    "Une exécution est active dans cette fenêtre.\n\n"
    "Fermer maintenant interrompt l'appel en cours : il a pu être payé, aucun rejeu automatique."
)


def run() -> None:
    root = tk.Tk()
    root.title(_TITLE)
    root.minsize(*_MIN_SIZE)
    controller = Controller(root)
    controller.show_accueil()
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(root, controller))
    root.mainloop()


def _on_close(root: tk.Tk, controller: Controller) -> None:
    """§9.2-9.3 : fermer sans exécution active ferme tout de suite ; sinon,
    seules les branches « continuer à suivre » et « interrompre maintenant »
    sont offertes — la pause-puis-fermeture différée reste à faire (lot 5/6)."""
    if not controller.has_active_run():
        root.destroy()
        return
    if dialogs.confirm(
        root, "Fermer maintenant ?", _CLOSE_BODY, ok_label="Interrompre et fermer",
    ):
        controller.interrupt_active_run()
        root.destroy()
