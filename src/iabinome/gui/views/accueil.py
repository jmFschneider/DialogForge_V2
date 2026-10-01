"""Écran d'accueil (`conception/GUI_V1.md` §5) : créer, ouvrir, ou retrouver une
collaboration récente. `Ouvrir` est strictement en lecture (AC-02) — le statut
des récents est relu du disque à chaque affichage, jamais mis en cache (AC-04).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from tkinter import Misc, filedialog, ttk
from typing import TYPE_CHECKING

from ... import facade

if TYPE_CHECKING:
    from ..controller import Controller

_PITCH = (
    "Partez d'une idée. Une recherche l'éclaire avec des sources, une conception en tire un plan"
    " prêt à coder, puis le code passe à son tour en revue. À chaque étape, A produit, B critique,"
    " et c'est vous qui décidez."
)
_COLUMNS = ("nom", "situation", "mise_a_jour")
_HEADINGS = ("Nom", "Situation", "Mise à jour")
_MONTHS = (
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
)


def _relative(now: datetime, at: str) -> str:
    """Une date ISO en un repère court — un fait relu, jamais une estimation."""
    try:
        moment = datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return at
    seconds = (now - moment).total_seconds()
    if seconds < 60:
        return "à l'instant"
    if seconds < 3600:
        return f"il y a {int(seconds // 60)} min"
    if seconds < 86400:
        return f"il y a {int(seconds // 3600)} h"
    if seconds < 2 * 86400:
        return "hier"
    return f"{moment.day} {_MONTHS[moment.month - 1]}"


class AccueilView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller) -> None:
        super().__init__(master)
        self._controller = controller
        self._rows: dict[str, Path] = {}
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="DialogForge", font=("", 14, "bold")).pack(
            anchor="w", padx=16, pady=(16, 0)
        )
        # Le rappel de la chaîne (`conception/TYPES_DE_MISSION.md` D6).
        ttk.Label(self, text="Recherche → Conception → Développement", font=("", 11, "bold")).pack(
            anchor="w", padx=16, pady=(4, 0)
        )
        ttk.Label(self, text=_PITCH, wraplength=640, justify="left").pack(
            anchor="w", padx=16, pady=(2, 8)
        )

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=16, pady=8)
        new_button = ttk.Button(
            actions, text="Nouvelle collaboration", command=self._controller.show_creation,
            underline=0,
        )
        new_button.pack(side="left")
        ttk.Button(
            actions, text="Ouvrir une collaboration…", command=self._ask_open, underline=0,
        ).pack(side="left", padx=(8, 0))
        new_button.focus_set()

        root_row = ttk.Frame(self)
        root_row.pack(fill="x", padx=16, pady=(0, 4))
        root = self._controller.collaborations_root()
        ttk.Label(
            root_row, text=f"Répertoire des collaborations : {root or '(non défini)'}",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(root_row, text="Choisir le répertoire…", command=self._choose_root).pack(
            side="right"
        )

        ttk.Label(self, text="Collaborations récentes et du répertoire choisi").pack(
            anchor="w", padx=16, pady=(8, 0)
        )
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=16, pady=8)
        self._table = ttk.Treeview(
            table_frame, columns=_COLUMNS, show="headings", selectmode="browse", height=8,
        )
        for key, title in zip(_COLUMNS, _HEADINGS, strict=True):
            self._table.heading(key, text=title)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._table.yview)
        self._table.configure(yscrollcommand=scroll.set)
        self._table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._fill_recents()

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(footer, text="Ouvrir", command=self._open_selected).pack(side="left")
        ttk.Button(
            footer, text="Afficher dans le dossier", command=self._reveal_selected,
        ).pack(side="left", padx=(8, 0))

        self.bind_all("<Control-n>", lambda _event: self._controller.show_creation())
        self.bind_all("<Control-o>", lambda _event: self._ask_open())

    def _fill_recents(self) -> None:
        now = datetime.now(UTC)
        for recent in self._controller.recent_entries():
            situation, updated_at = self._situation(recent.path)
            row = self._table.insert("", "end", values=(
                recent.path.name, situation, _relative(now, updated_at or recent.last_opened_at),
            ))
            self._rows[row] = recent.path

    def _situation(self, path: Path) -> tuple[str, str | None]:
        """AC-03/AC-04 : un dossier absent ou illisible est nommé, sans jamais
        être réparé, ni écarté de la liste."""
        if not path.is_dir():
            return "Dossier introuvable", None
        try:
            snapshot = self._controller.inspect(path)
        except facade.InspectionError as exc:
            return f"Dossier illisible : {exc}", None
        return snapshot.presentation.status_label, snapshot.state.updated_at

    def _selected_path(self) -> Path | None:
        selection = self._table.selection()
        return self._rows.get(selection[0]) if selection else None

    def _ask_open(self) -> None:
        chosen = filedialog.askdirectory(title="Ouvrir une collaboration")
        if chosen:
            self._controller.open_collaboration(Path(chosen))

    def _choose_root(self) -> None:
        current = self._controller.collaborations_root()
        chosen = filedialog.askdirectory(
            title="Répertoire des collaborations",
            initialdir=str(current) if current is not None else str(Path.home()),
        )
        if chosen:
            self._controller.set_collaborations_root(Path(chosen))

    def _open_selected(self) -> None:
        path = self._selected_path()
        if path is not None:
            self._controller.open_collaboration(path)

    def _reveal_selected(self) -> None:
        """Intégration native (§5.1) : sans effet si le dossier n'existe plus."""
        path = self._selected_path()
        if path is not None and path.is_dir() and hasattr(os, "startfile"):
            os.startfile(path)
