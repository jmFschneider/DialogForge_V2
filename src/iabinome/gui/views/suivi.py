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

from ... import facade, mission, storage
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
        self._steps = ttk.Frame(header)  # l'en-tête de la mission, quand il y en a une
        self._steps.pack(fill="x", pady=(4, 0))
        # Le dossier se voit dès l'ouverture, incident compris (retour d'usage du 2026-09-28).
        folder = ttk.Frame(header)
        folder.pack(fill="x", pady=(4, 0))
        ttk.Label(folder, text="Dossier :").pack(side="left")
        path_field = ttk.Entry(folder)
        path_field.insert(0, str(self._path))
        path_field.configure(state="readonly")
        path_field.pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(folder, text="Ouvrir le dossier", command=self._reveal).pack(side="left")
        self._trace_button = ttk.Button(
            folder, text="Ouvrir la trace de l'appel", command=self._reveal_trace,
        )
        self._trace: str | None = None

        self._now = ttk.Label(self, font=("", 11, "bold"), justify="left", wraplength=560)
        self._now.pack(anchor="w", padx=16, pady=(8, 0))
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
        ttk.Button(footer, text="Actualiser", command=self._refresh).pack(side="left")
        self._follow_up = ttk.Frame(footer)  # poursuivre, ou rouvrir, la conception
        self._follow_up.pack(side="left")
        self._runner = ttk.Button(
            footer, text="Développer avec le Runner",
            command=lambda: self._controller.show_runner(self._path),
        )
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
        self._show_progress(snapshot.presentation.progress)
        self._trace = snapshot.presentation.trace_dir
        if self._trace:
            self._trace_button.pack(side="left", padx=(4, 0))
        else:
            self._trace_button.pack_forget()
        self._activity.configure(text=self._activity_text(snapshot))
        if not running:
            self._show_mission()
        self._show_follow_up(snapshot.presentation.can_follow_up)
        if snapshot.presentation.can_start_runner:
            self._runner.pack(side="left", padx=(8, 0))
        else:
            self._runner.pack_forget()
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
            name = Path(document).name
            ttk.Button(
                self._documents_row,
                text=f"{name} de l'appel" if document.startswith("appels/") else name,
                command=self._document_handler(document),
            ).pack(side="left", padx=(0, 4))
        if running:
            self._after_id = self.after(_POLL_MS, self._refresh)

    def _show_mission(self) -> None:
        """La mission et ses étapes, lues du registre et des dossiers : naviguer ne change aucun
        état, et n'indique jamais quelle étape peut tourner."""
        for child in self._steps.winfo_children():
            child.destroy()
        try:
            summary = mission.overview(self._path)
        except mission.MissionError as exc:
            ttk.Label(self._steps, text=f"Mission illisible : {exc}").pack(side="left")
            return
        if summary is None:
            return
        ttk.Label(self._steps, text=f"Mission {summary.mission.name} :").pack(side="left")
        for view in summary.steps:
            ttk.Button(
                self._steps, text=f"{view.step.role.capitalize()} — {view.label}",
                state="disabled" if view.path.resolve() == self._path.resolve() else "normal",
                command=self._step_handler(summary.mission.root, view.step.path),
            ).pack(side="left", padx=(4, 0))

    def _step_handler(self, root: Path, step: str) -> Callable[[], None]:
        """Un objet par étape, comme `_document_handler` : jamais la variable de boucle."""
        return lambda: self._controller.open_collaboration(root, step)

    def _show_follow_up(self, allowed: bool) -> None:
        """Une conception déjà créée se rouvre ; une nouvelle version est une action à part."""
        for child in self._follow_up.winfo_children():
            child.destroy()
        if not allowed:
            return
        controller, research = self._controller, self._path
        done = mission.continuations(research)
        if done:
            choices: list[tuple[str, Callable[[], None]]] = [
                ("Reprendre la conception", lambda: controller.open_collaboration(done[-1])),
                ("Nouvelle version de conception",
                 lambda: controller.show_creation(from_research=research, new_version=True)),
            ]
        else:
            choices = [("Poursuivre en conception",
                        lambda: controller.show_creation(from_research=research))]
        for text, command in choices:
            ttk.Button(self._follow_up, text=text, command=command).pack(side="left", padx=(8, 0))

    def _show_progress(self, progress: facade.Progress) -> None:
        """Une grille : un tour par ligne, A puis B, puis la décision humaine.
        L'étape courante est en gras ; le texte vient de la façade (§15.1)."""
        grid = self._progression
        for child in grid.winfo_children():
            child.destroy()
        self._now.configure(text=progress.now)
        ttk.Label(grid, text=progress.agent_a).grid(row=0, column=1, sticky="w", padx=(0, 24))
        ttk.Label(grid, text=progress.agent_b).grid(row=0, column=2, sticky="w")
        for row, steps in enumerate(progress.rounds, start=1):
            tour = ttk.Label(grid, text=f"Tour {row - 1}")
            tour.grid(row=row, column=0, sticky="w", padx=(0, 12))
            for column, step in enumerate(steps, start=1):
                self._step_label(step).grid(row=row, column=column, sticky="w", padx=(0, 24))
        last = len(progress.rounds) + 1
        ttk.Label(grid, text="Vous").grid(row=last, column=0, sticky="w", padx=(0, 12))
        self._step_label(progress.human).grid(row=last, column=1, columnspan=2, sticky="w")

    def _step_label(self, step: facade.Step) -> ttk.Label:
        label = ttk.Label(self._progression, text=f"{step.symbol} {step.label}")
        if step.symbol in ("●", "!"):
            label.configure(font=("", 10, "bold"))
        return label

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
        found = decision.discrepancies
        changed = f" — porte sur une version antérieure : {' ; '.join(found)}" if found else ""
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
        if relative.startswith("appels/"):
            self._viewer.see("end")  # la cause est en fin de sortie, après la bannière

    def _reveal_trace(self) -> None:
        if self._trace and hasattr(os, "startfile"):
            os.startfile(self._path / self._trace)

    def _set_viewer(self, text: str) -> None:
        self._viewer.configure(state="normal")
        self._viewer.delete("1.0", "end")
        self._viewer.insert("1.0", text)
        self._viewer.configure(state="disabled")

    def _reveal(self) -> None:
        if self._path.is_dir() and hasattr(os, "startfile"):
            os.startfile(self._path)
