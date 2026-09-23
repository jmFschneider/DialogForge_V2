"""Confirmation modale partagée (`conception/GUI_V1.md` §3.5) : toute commande
susceptible d'atteindre un nouvel appel fournisseur en affiche une, avec des
boutons qui nomment l'acte — jamais un `messagebox.askyesno` générique, dont
les boutons ne disent ni ce qui est local ni ce qui peut payer.
"""

from __future__ import annotations

from tkinter import Misc, Toplevel, ttk


def confirm(
    parent: Misc, title: str, body: str, *, ok_label: str, cancel_label: str = "Annuler",
) -> bool:
    """Bloque jusqu'à la fermeture, rend `True` seulement si `ok_label` a été
    choisi. Le focus par défaut reste sur l'annulation (§12 : navigation
    complète au clavier, jamais un acte payant par défaut sur Entrée)."""
    top = parent.winfo_toplevel()
    window = Toplevel(top)
    window.title(title)
    window.transient(top)
    window.resizable(False, False)
    ttk.Label(window, text=body, justify="left", wraplength=440, padding=16).pack()
    buttons = ttk.Frame(window, padding=(16, 0, 16, 16))
    buttons.pack(fill="x")
    accepted = {"value": False}

    def accept() -> None:
        accepted["value"] = True
        window.destroy()

    def cancel() -> None:
        window.destroy()

    cancel_button = ttk.Button(buttons, text=cancel_label, command=cancel)
    cancel_button.pack(side="right")
    ttk.Button(buttons, text=ok_label, command=accept).pack(side="right", padx=(0, 8))
    window.protocol("WM_DELETE_WINDOW", cancel)
    window.grab_set()
    cancel_button.focus_set()
    top.wait_window(window)
    return accepted["value"]
