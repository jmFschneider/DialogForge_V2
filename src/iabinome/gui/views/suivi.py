"""Écran de suivi (`conception/GUI_V1.md` §7-§8) : observer, actualiser, et
depuis le lot 5, agir — les actions offertes viennent **uniquement** de
`decisions.allowed_actions` (§10.2), câblées via `views.intervention`. Cet
écran ne décide jamais lui-même ce qui est permis.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from tkinter import Misc, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from ... import facade, storage
from ...decisions import AllowedAction
from . import intervention

if TYPE_CHECKING:
    from ..controller import Controller

_PLACEHOLDER = "Sélectionnez un document ci-dessus pour le lire."
_POLL_MS = 500


class SuiviView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller, path: Path) -> None:
        super().__init__(master)
        self._controller = controller
        self._path = path
        self._after_id: str | None = None
        self._build()
        self._set_viewer(_PLACEHOLDER)
        self._refresh()

    def destroy(self) -> None:
        """Une actualisation programmée ne doit jamais s'exécuter contre une
        vue détruite — §9 : fermer n'abandonne aucun fil, mais n'en laisse pas
        non plus un réveiller un widget disparu."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        super().destroy()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(16, 0))
        self._title = ttk.Label(header, font=("", 13, "bold"))
        self._title.pack(anchor="w")
        self._subtitle = ttk.Label(header)
        self._subtitle.pack(anchor="w")

        self._progression = ttk.Frame(self)
        self._progression.pack(fill="x", padx=16, pady=8)

        self._activity = ttk.Label(self, justify="left", wraplength=560)
        self._activity.pack(anchor="w", padx=16, pady=(0, 8))

        self._result = ttk.Label(self, justify="left", wraplength=560)
        self._result.pack(anchor="w", padx=16, pady=(0, 8))

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Label(actions, text="Actions :").pack(side="left")
        self._actions_row = ttk.Frame(actions)
        self._actions_row.pack(side="left", padx=(8, 0))

        documents = ttk.Frame(self)
        documents.pack(fill="x", padx=16)
        ttk.Label(documents, text="Documents :").pack(side="left")
        self._documents_row = ttk.Frame(documents)
        self._documents_row.pack(side="left", padx=(8, 0))

        self._viewer = ScrolledText(self, height=12, wrap="word", state="disabled")
        self._viewer.pack(fill="both", expand=True, padx=16, pady=8)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(
            footer, text="Ouvrir le dossier", command=self._reveal,
        ).pack(side="left")
        ttk.Button(footer, text="Actualiser", command=self._refresh).pack(side="left", padx=(8, 0))
        ttk.Button(
            footer, text="Retour à l'accueil", command=self._controller.show_accueil,
        ).pack(side="right")

    def _refresh(self) -> None:
        """Relit intégralement le dossier (§3.3) : aucune écriture, jamais de
        cache du statut ou de la phase. Tant que cette fenêtre possède une
        exécution sur ce dossier (`iabinome.gui.controller.Controller.
        start_run`), un fil unique la relit périodiquement (§7.3) ; sans lui,
        `Actualiser` reste la seule façon de rafraîchir l'écran."""
        self._after_id = None
        running = self._controller.is_running(self._path)
        try:
            snapshot = self._controller.inspect(self._path, owned_by_this_gui=running)
        except facade.InspectionError as exc:
            self._title.configure(text=self._path.name)
            self._subtitle.configure(text=f"Dossier illisible : {exc}")
            # Sous Windows, `etat.json` est un instant illisible pendant que le moteur le
            # remplace (mesuré le 2026-09-25 : « Permission denied ») : l'exécution continue,
            # le suivi aussi. Le refus reste affiché jusqu'à la lecture suivante.
            if running:
                self._after_id = self.after(_POLL_MS, self._refresh)
            return
        self._title.configure(text=f"{snapshot.name} — {snapshot.presentation.status_label}")
        self._subtitle.configure(
            text=f"{snapshot.presentation.phase_label} · {snapshot.presentation.activity_label}"
        )
        for child in self._progression.winfo_children():
            child.destroy()
        for symbol, label in snapshot.presentation.phase_steps:
            ttk.Label(self._progression, text=f"{symbol} {label}").pack(side="left", padx=(0, 12))
        self._activity.configure(text=self._activity_text(snapshot))
        self._result.configure(text=self._result_text(snapshot))
        for child in self._actions_row.winfo_children():
            child.destroy()
        for action in snapshot.presentation.allowed_actions:
            ttk.Button(
                self._actions_row, text=intervention.label(action.id),
                command=self._action_handler(action),
            ).pack(side="left", padx=(0, 4))
        for child in self._documents_row.winfo_children():
            child.destroy()
        for document in snapshot.presentation.readable_documents:
            ttk.Button(
                self._documents_row, text=Path(document).name,
                command=self._document_handler(document),
            ).pack(side="left", padx=(0, 4))
        if running:
            self._after_id = self.after(_POLL_MS, self._refresh)

    def _activity_text(self, snapshot: facade.CollaborationSnapshot) -> str:
        lines = [f"Dernier état du dossier : {snapshot.state.updated_at}"]
        if snapshot.incident:
            lines.append(snapshot.incident)
        error = self._controller.run_error(self._path)
        if error:
            lines.append(f"Le lancement n'a pas pu partir : {error}")
        return "\n".join(lines)

    def _result_text(self, snapshot: facade.CollaborationSnapshot) -> str:
        decision = snapshot.current_decision
        text = f"Prochaine action : {snapshot.presentation.next_action_text}"
        if decision.kind is None:
            return text
        changed = "" if decision.applies_to_current_version else " — le livrable a changé depuis"
        return f"Décision : {decision.kind} le {decision.at}{changed}\n{text}"

    def _action_handler(self, action: AllowedAction) -> Callable[[], None]:
        """Comme `_document_handler` : un objet par action, jamais une
        fermeture sur la variable de boucle. `_refresh()` après coup montre
        l'effet immédiat — une décision locale, ou une exécution qui démarre
        et que le fil de rafraîchissement (§7.3) prendra ensuite en charge."""

        def handler() -> None:
            intervention.run(self, self._controller, self._path, action)
            self._refresh()

        return handler

    def _document_handler(self, relative: str) -> Callable[[], None]:
        """Un objet par document, jamais une fermeture sur la variable de
        boucle : sans lui, chaque bouton relirait le **dernier** document."""
        return lambda: self._show_document(relative)

    def _show_document(self, relative: str) -> None:
        try:
            text, _ = storage.read_text(self._path / relative)
        except OSError as exc:
            text = f"Lecture impossible : {exc}"
        self._set_viewer(text)

    def _set_viewer(self, text: str) -> None:
        self._viewer.configure(state="normal")
        self._viewer.delete("1.0", "end")
        self._viewer.insert("1.0", text)
        self._viewer.configure(state="disabled")

    def _reveal(self) -> None:
        if self._path.is_dir() and hasattr(os, "startfile"):
            os.startfile(self._path)
