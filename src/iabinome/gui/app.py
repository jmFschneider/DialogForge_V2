"""Point d'entrée de la GUI V1 — une fenêtre, une collaboration, une exécution
au maximum (`conception/GUI_V1.md` §3.1). Appelé par `dialogforge gui`.
"""

from __future__ import annotations

import tkinter as tk

from . import dialogs
from .controller import Controller

_TITLE = "DialogForge"
_MIN_SIZE = (720, 480)
_WAIT_MS = 200

_CLOSE_BODY = (
    "Une exécution est active dans cette fenêtre.\n\n"
    "« Interrompre maintenant » arrête l'appel en cours : il a pu être payé, aucun rejeu "
    "automatique. « Terminer l'appel courant » attend la fin du fil, sans en lancer d'autre, "
    "puis ferme."
)
_CONTINUE = "Continuer à suivre"
_PAUSE_THEN_CLOSE = "Terminer l'appel courant, mettre en pause, puis fermer"
_INTERRUPT = "Interrompre maintenant"


def run() -> None:
    root = tk.Tk()
    root.title(_TITLE)
    root.minsize(*_MIN_SIZE)
    controller = Controller(root)
    controller.show_accueil()
    root.protocol("WM_DELETE_WINDOW", lambda: _on_close(root, controller))
    root.mainloop()


def _on_close(root: tk.Tk, controller: Controller) -> None:
    """§9.2-9.3 : fermer sans exécution active ferme tout de suite. Avec une
    exécution active, les trois branches du §9.3 sont offertes — la fenêtre
    reste ouverte jusqu'à la frontière sûre pour la seconde."""
    if not controller.has_active_run():
        _destroy(root, controller)
        return
    choice = dialogs.choose(
        root, "Une exécution est active", _CLOSE_BODY,
        options=(_CONTINUE, _PAUSE_THEN_CLOSE, _INTERRUPT),
    )
    if choice is None or choice == _CONTINUE:
        return
    if choice == _INTERRUPT:
        controller.interrupt_active_run()
        if controller.has_active_runner():
            _wait_then_close(root, controller)
        else:
            _destroy(root, controller)
        return
    controller.pause_active_run()
    _wait_then_close(root, controller)


def _wait_then_close(root: tk.Tk, controller: Controller) -> None:
    """Un fil unique, celui du moteur, décide quand il est sûr de fermer —
    ce fil Tk ne fait qu'attendre, sans jamais bloquer `mainloop()` (§9.3)."""
    if not controller.has_active_run():
        _destroy(root, controller)
        return
    root.after(_WAIT_MS, lambda: _wait_then_close(root, controller))


def _destroy(root: tk.Tk, controller: Controller) -> None:
    """Un cadrage ouvert ne survit pas à la fenêtre : sa session se ferme et son
    dossier jetable disparaît (`CADRAGE_AGENT.md` §3.2)."""
    controller.discard_framing()
    root.destroy()
