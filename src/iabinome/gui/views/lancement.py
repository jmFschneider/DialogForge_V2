"""Réglages du prochain lancement (`conception/GUI_V1.md` §6.4) : fichier de réglages et
délai. Ils valent pour ce lancement seulement, jamais écrits dans `configuration.json` (AC-10)."""

from __future__ import annotations

from pathlib import Path
from tkinter import Misc, StringVar, ttk

from ... import settings
from .. import widgets


class LaunchPanel(ttk.Frame):
    def __init__(self, master: Misc, dossier: StringVar) -> None:
        super().__init__(master)
        self._dossier = dossier
        self.config_path = StringVar()
        self.timeout_override = StringVar()
        row = ttk.Frame(self)
        row.pack(fill="x")
        ttk.Label(row, text="Fichier de réglages").pack(side="left")
        ttk.Entry(row, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(
            row, text="Choisir…", command=widgets.browse(self.config_path, "Fichier de réglages"),
        ).pack(side="left")
        timeout_row = ttk.Frame(self)
        timeout_row.pack(fill="x", pady=(4, 0))
        ttk.Label(timeout_row, text="Délai (secondes, surcharge)").pack(side="left")
        ttk.Entry(timeout_row, textvariable=self.timeout_override, width=10).pack(
            side="left", padx=(4, 0)
        )
        self._origin = ttk.Label(self, text="")
        self._origin.pack(anchor="w", pady=(4, 0))
        ttk.Button(self, text="Résoudre", command=self._show).pack(anchor="w")

    def resolved(self, collab: Path) -> settings.Timeout:
        override = self.timeout_override.get()
        return settings.resolve_timeout(
            self.config_path.get() or None, float(override) if override else None,
            base=collab.parent,
        )

    def _show(self) -> None:
        dest = Path(self._dossier.get()) if self._dossier.get() else Path.cwd()
        try:
            resolved = self.resolved(dest)
        except (settings.SettingsError, ValueError) as exc:
            self._origin.configure(text=f"Délai : refusé — {exc}")
            return
        self._origin.configure(
            text=f"Délai effectif : {resolved.seconds:g} s — origine : {resolved.origin}"
        )
