"""Confirmation modale partagée (`conception/GUI_V1.md` §3.5) : toute commande
susceptible d'atteindre un nouvel appel fournisseur en affiche une, avec des
boutons qui nomment l'acte — jamais un `messagebox.askyesno` générique, dont
les boutons ne disent ni ce qui est local ni ce qui peut payer.
"""

from __future__ import annotations

from collections.abc import Callable
from tkinter import Misc, Toplevel, ttk
from tkinter.scrolledtext import ScrolledText


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


def prompt_text(parent: Misc, title: str, label: str) -> str | None:
    """Une invite **multiligne** — une réponse humaine ou un motif tiennent
    rarement sur une ligne (`simpledialog.askstring` ne conviendrait pas).
    Rend `None` si annulée ; le texte tel quel sinon, y compris vide — à
    l'appelant de refuser un motif vide (§8.4, §8.5 : le motif est exigé)."""
    top = parent.winfo_toplevel()
    window = Toplevel(top)
    window.title(title)
    window.transient(top)
    ttk.Label(window, text=label, padding=(16, 16, 16, 4)).pack(anchor="w")
    text = ScrolledText(window, width=64, height=10, wrap="word")
    text.pack(fill="both", expand=True, padx=16)
    buttons = ttk.Frame(window, padding=16)
    buttons.pack(fill="x")
    result: dict[str, str | None] = {"value": None}

    def accept() -> None:
        result["value"] = text.get("1.0", "end-1c")
        window.destroy()

    def cancel() -> None:
        window.destroy()

    cancel_button = ttk.Button(buttons, text="Annuler", command=cancel)
    cancel_button.pack(side="right")
    ttk.Button(buttons, text="Continuer", command=accept).pack(side="right", padx=(0, 8))
    window.protocol("WM_DELETE_WINDOW", cancel)
    window.grab_set()
    text.focus_set()
    top.wait_window(window)
    return result["value"]


def choose(parent: Misc, title: str, body: str, *, options: tuple[str, ...]) -> str | None:
    """Plus de deux issues possibles (§9.3 : continuer à suivre / pause puis
    fermeture / interrompre maintenant) — rend l'option choisie, ou `None` si
    la fenêtre est fermée sans choisir (compté comme la plus prudente)."""
    top = parent.winfo_toplevel()
    window = Toplevel(top)
    window.title(title)
    window.transient(top)
    window.resizable(False, False)
    ttk.Label(window, text=body, justify="left", wraplength=440, padding=16).pack()
    buttons = ttk.Frame(window, padding=(16, 0, 16, 16))
    buttons.pack(fill="x")
    result: dict[str, str | None] = {"value": None}

    def picker(option: str) -> Callable[[], None]:
        def pick() -> None:
            result["value"] = option
            window.destroy()

        return pick

    for option in reversed(options):
        ttk.Button(buttons, text=option, command=picker(option)).pack(side="right", padx=(8, 0))
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    window.grab_set()
    top.wait_window(window)
    return result["value"]
