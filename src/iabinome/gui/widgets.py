"""Petites briques d'écran sans état métier, partagées par les vues."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import StringVar, filedialog, ttk


def disclosure(parent: ttk.Frame, title: str, fill: Callable[[ttk.Frame], None]) -> None:
    """Une section repliable : fermée au départ, ouverte d'un clic sur son titre."""
    content = ttk.Frame(parent)
    state = {"open": False}

    def toggle() -> None:
        state["open"] = not state["open"]
        button.configure(text=f"{'▾' if state['open'] else '▸'} {title}")
        if state["open"]:
            content.pack(fill="x", padx=(12, 0), pady=(0, 8))
        else:
            content.pack_forget()

    button = ttk.Button(parent, text=f"▸ {title}", command=toggle)
    button.pack(anchor="w", pady=(8, 0))
    fill(content)


def browse(var: StringVar, title: str, *, folder: bool = False) -> Callable[[], None]:
    """Le bouton « Choisir… » d'un champ de chemin : la boîte native, puis le champ."""

    def choose() -> None:
        chosen = filedialog.askdirectory(title=title) if folder else (
            filedialog.askopenfilename(title=title)
        )
        if chosen:
            var.set(chosen)

    return choose
