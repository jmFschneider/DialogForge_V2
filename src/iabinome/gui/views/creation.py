"""Écran de création (`conception/GUI_V1.md` §6) : saisir ou importer une
demande, configurer la collaboration, la créer seule ou la créer et démarrer.

La validation autoritaire est celle de `facade.create_collaboration` — la
**même** que `new` en CLI (§6.5) : ce module ne revalide rien, il rassemble
une `CreationRequest` et affiche le refus tel quel si la façade en rend un.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import BooleanVar, Misc, StringVar, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from ... import facade, framing, settings, storage
from ...models import MissionKind, ReviewerAccess
from ...registry import ADAPTERS
from .. import dialogs
from . import cadrage

if TYPE_CHECKING:
    from ..controller import Controller

_KIND = {"Conception": MissionKind.CONCEPTION, "Recherche": MissionKind.RECHERCHE}
_ACCESS = {"Consultation": ReviewerAccess.CONSULT, "Contexte seul": ReviewerAccess.CONTEXT_ONLY}
_NON_SPECIFIE = "(non spécifié)"


class CreationView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller) -> None:
        super().__init__(master)
        self._controller = controller
        self._imported_path: str | None = None
        self._imported_text: str | None = None
        self._mode = StringVar(value="saisir")
        self._kind = StringVar(value="Conception")
        self._agent_a = StringVar(value=sorted(ADAPTERS)[0])
        self._agent_b = StringVar(value=sorted(ADAPTERS)[-1])
        self._revisions = StringVar(value="2")
        self._source_root = StringVar()
        self._source_list = StringVar()
        self._source_label = StringVar()
        self._model_a = StringVar()
        self._model_b = StringVar()
        self._effort_a = StringVar(value=_NON_SPECIFIE)
        self._effort_b = StringVar(value=_NON_SPECIFIE)
        self._web_access = BooleanVar(value=False)
        self._reviewer = StringVar(value="Consultation")
        self._config_path = StringVar()
        self._timeout_override = StringVar()
        self._build()

    # -- Construction --

    def _build(self) -> None:
        ttk.Label(self, text="Nouvelle collaboration", font=("", 13, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16)

        folder_row = ttk.Frame(body)
        folder_row.pack(fill="x")
        ttk.Label(folder_row, text="Dossier").pack(anchor="w")
        self._dossier = StringVar()
        entry_row = ttk.Frame(folder_row)
        entry_row.pack(fill="x")
        ttk.Entry(entry_row, textvariable=self._dossier).pack(side="left", fill="x", expand=True)
        ttk.Button(entry_row, text="Choisir…", command=self._choose_folder).pack(side="left")

        self._build_demande(body)
        self._build_type_and_agents(body)
        self._corpus_frame = ttk.Frame(body)
        self._build_corpus(self._corpus_frame)
        self._toggle_kind()

        self._build_disclosure(body, "Réglages avancés de la collaboration", self._build_advanced)
        self._build_disclosure(body, "Réglages du prochain lancement", self._build_launch)

        self._error = ttk.Label(self, foreground="#a33", wraplength=560, justify="left")
        self._error.pack(anchor="w", padx=16, pady=(4, 0))

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=16, pady=16)
        ttk.Button(footer, text="Annuler", command=self._controller.show_accueil).pack(side="left")
        ttk.Button(
            footer, text="Créer et démarrer", command=self._create_and_start,
        ).pack(side="right")
        ttk.Button(footer, text="Créer seulement", command=self._create_only).pack(
            side="right", padx=(0, 8)
        )

    def _build_demande(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Demande").pack(anchor="w", pady=(12, 0))
        modes = ttk.Frame(parent)
        modes.pack(fill="x")
        for text, value in (
            ("Saisir", "saisir"), ("Importer un fichier", "importer"),
            ("Cadrer avec un agent", "agent"),
        ):
            ttk.Radiobutton(
                modes, text=text, value=value, variable=self._mode, command=self._on_mode,
            ).pack(side="left")
        self._demande_text = ScrolledText(parent, height=8, wrap="word")
        self._demande_text.pack(fill="x", pady=(4, 0))
        import_row = ttk.Frame(parent)
        import_row.pack(fill="x", pady=(4, 0))
        ttk.Button(import_row, text="Importer…", command=self._import_file).pack(side="left")
        self._source_label_text = ttk.Label(import_row, text="Source affichée : saisie directe")
        self._source_label_text.pack(side="left", padx=(8, 0))
        self._demande_text.bind("<<Modified>>", self._on_demande_changed)
        self._import_row = import_row
        self._framing_panel = cadrage.FramingPanel(
            parent, on_start=self._start_framing, on_resume=self._resume_framing,
        )

    def _build_type_and_agents(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(12, 0))
        ttk.Label(row, text="Type").pack(side="left")
        for label in _KIND:
            ttk.Radiobutton(
                row, text=label, value=label, variable=self._kind, command=self._toggle_kind,
            ).pack(side="left", padx=(8, 0))
        agents = ttk.Frame(parent)
        agents.pack(fill="x", pady=(8, 0))
        ttk.Label(agents, text="Agent A").pack(side="left")
        ttk.Combobox(
            agents, textvariable=self._agent_a, values=sorted(ADAPTERS), state="readonly", width=10,
        ).pack(side="left", padx=(4, 12))
        ttk.Label(agents, text="Agent B").pack(side="left")
        ttk.Combobox(
            agents, textvariable=self._agent_b, values=sorted(ADAPTERS), state="readonly", width=10,
        ).pack(side="left", padx=(4, 12))
        ttk.Label(agents, text="Révisions maximales").pack(side="left")
        ttk.Entry(agents, textvariable=self._revisions, width=4).pack(side="left", padx=(4, 0))

    def _build_corpus(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Corpus de recherche").pack(anchor="w", pady=(12, 0))
        for label, var, browse in (
            ("Racine", self._source_root, self._choose_source_root),
            ("Liste", self._source_list, self._choose_source_list),
        ):
            row = ttk.Frame(parent)
            row.pack(fill="x")
            ttk.Label(row, text=label, width=8).pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Choisir…", command=browse).pack(side="left")
        row = ttk.Frame(parent)
        row.pack(fill="x")
        ttk.Label(row, text="Nom", width=8).pack(side="left")
        ttk.Entry(row, textvariable=self._source_label).pack(side="left", fill="x", expand=True)

    def _build_advanced(self, parent: ttk.Frame) -> None:
        for label, model, effort in (
            ("A", self._model_a, self._effort_a), ("B", self._model_b, self._effort_b),
        ):
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"Modèle {label}", width=12).pack(side="left")
            ttk.Entry(row, textvariable=model).pack(side="left", fill="x", expand=True)
            ttk.Label(row, text=f"Effort {label}", width=10).pack(side="left", padx=(8, 0))
            ttk.Combobox(
                row, textvariable=effort, values=self._effort_values(label), state="readonly",
                width=14,
            ).pack(side="left")
        ttk.Checkbutton(
            parent, text="Accès web : autoriser pour A et B", variable=self._web_access,
        ).pack(anchor="w", pady=(4, 0))
        access_row = ttk.Frame(parent)
        access_row.pack(fill="x")
        ttk.Label(access_row, text="Accès du critique").pack(side="left")
        for label in _ACCESS:
            ttk.Radiobutton(
                access_row, text=label, value=label, variable=self._reviewer,
            ).pack(side="left", padx=(8, 0))

    def _build_launch(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x")
        ttk.Label(row, text="Fichier de réglages").pack(side="left")
        ttk.Entry(row, textvariable=self._config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Choisir…", command=self._choose_config).pack(side="left")
        timeout_row = ttk.Frame(parent)
        timeout_row.pack(fill="x", pady=(4, 0))
        ttk.Label(timeout_row, text="Délai (secondes, surcharge)").pack(side="left")
        ttk.Entry(timeout_row, textvariable=self._timeout_override, width=10).pack(
            side="left", padx=(4, 0)
        )
        self._launch_origin = ttk.Label(parent, text="")
        self._launch_origin.pack(anchor="w", pady=(4, 0))
        ttk.Button(parent, text="Résoudre", command=self._show_resolved_timeout).pack(anchor="w")

    def _build_disclosure(
        self, parent: ttk.Frame, title: str, fill: Callable[[ttk.Frame], None],
    ) -> None:
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

    # -- Provenance et lecture de la demande (§6.2) --

    def _reset_import(self) -> None:
        self._imported_path = None
        self._imported_text = None
        self._source_label_text.configure(text="Source affichée : saisie directe")

    def _import_file(self) -> None:
        chosen = filedialog.askopenfilename(title="Importer une demande")
        if not chosen:
            return
        try:
            text, _ = storage.read_text(Path(chosen))
        except OSError as exc:
            messagebox.showerror("Import impossible", str(exc))
            return
        self._demande_text.delete("1.0", "end")
        self._demande_text.insert("1.0", text)
        self._demande_text.edit_modified(False)
        self._mode.set("importer")
        self._imported_path, self._imported_text = chosen, text
        self._source_label_text.configure(text=f"Source affichée : fichier importé ({chosen})")

    def _on_demande_changed(self, _event: object) -> None:
        if not self._demande_text.edit_modified():
            return
        self._demande_text.edit_modified(False)
        if self._imported_path is not None and self._current_text() != self._imported_text:
            self._source_label_text.configure(
                text=f"Source affichée : fichier importé, modifié depuis ({self._imported_path})"
            )

    def _current_text(self) -> str:
        return self._demande_text.get("1.0", "end-1c")

    def _demande_source(self) -> facade.DemandeSource:
        text = self._current_text()
        unchanged = self._imported_path is not None and text == self._imported_text
        if self._mode.get() == "importer" and unchanged:
            return facade.DemandeSource(text, "fichier", self._imported_path)
        return facade.DemandeSource(text, "cadrage", None)

    def _effort_values(self, role: str) -> tuple[str, ...]:
        agent_id = (self._agent_a if role == "A" else self._agent_b).get()
        adapter = ADAPTERS.get(agent_id)
        levels = () if adapter is None else adapter.capabilities.effort_levels
        return (_NON_SPECIFIE, *levels)

    def _on_mode(self) -> None:
        """Quitter le mode agent termine le cadrage ; son brouillon reste dans l'éditeur."""
        if self._mode.get() == "agent":
            self._framing_panel.pack(fill="x", after=self._import_row)
        else:
            self._controller.discard_framing()
            self._framing_panel.pack_forget()
        if self._mode.get() == "saisir":
            self._reset_import()
        self._toggle_kind()

    def _toggle_kind(self) -> None:
        # Sources obligatoires en recherche, facultatives pour un cadrage (§2.2).
        if self._kind.get() == "Recherche" or self._mode.get() == "agent":
            self._corpus_frame.pack(fill="x")
        else:
            self._corpus_frame.pack_forget()

    # -- Choix de fichiers/dossiers --

    def _choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Dossier de la collaboration")
        if chosen:
            self._dossier.set(chosen)

    def _choose_source_root(self) -> None:
        chosen = filedialog.askdirectory(title="Racine du corpus")
        if chosen:
            self._source_root.set(chosen)

    def _choose_source_list(self) -> None:
        chosen = filedialog.askopenfilename(title="Liste du corpus")
        if chosen:
            self._source_list.set(chosen)

    def _choose_config(self) -> None:
        chosen = filedialog.askopenfilename(title="Fichier de réglages")
        if chosen:
            self._config_path.set(chosen)

    # -- Validation locale et résolution du délai (§6.4, §6.5 niveau 1) --

    def _show_resolved_timeout(self) -> None:
        dest = Path(self._dossier.get()) if self._dossier.get() else Path.cwd()
        try:
            resolved = settings.resolve_timeout(
                self._config_path.get() or None,
                float(self._timeout_override.get()) if self._timeout_override.get() else None,
                base=dest.parent,
            )
        except (settings.SettingsError, ValueError) as exc:
            self._launch_origin.configure(text=f"Délai : refusé — {exc}")
            return
        self._launch_origin.configure(
            text=f"Délai effectif : {resolved.seconds:g} s — origine : {resolved.origin}"
        )

    def _local_errors(self, *, framing_start: bool) -> str | None:
        if not self._dossier.get().strip():
            return "Le dossier est requis."
        if not framing_start and not self._current_text().strip():
            return "La demande ne peut pas être vide."
        if not self._revisions.get().strip().lstrip("-").isdigit():
            return "Révisions maximales : un entier attendu."
        return None

    def _build_request(self, *, framing_start: bool = False) -> facade.CreationRequest | None:
        local_error = self._local_errors(framing_start=framing_start)
        framed = None
        if local_error is None and self._mode.get() == "agent" and not framing_start:
            local_error, framed = cadrage.reviewed(self._controller, self._current_text())
        if local_error is not None:
            self._error.configure(text=local_error)
            return None
        sources = framed is None
        return facade.CreationRequest(
            collab=Path(self._dossier.get()), demande=self._demande_source(),
            kind=_KIND[self._kind.get()], reviewer_access=_ACCESS[self._reviewer.get()],
            agent_a=self._agent_a.get(), agent_b=self._agent_b.get(),
            max_revisions=int(self._revisions.get()),
            model_a=self._model_a.get() or None, model_b=self._model_b.get() or None,
            effort_a=self._effort(self._effort_a), effort_b=self._effort(self._effort_b),
            web_access=self._web_access.get(),
            source_root=Path(self._source_root.get()) if sources and self._source_root.get()
            else None,
            source_list=Path(self._source_list.get()) if sources and self._source_list.get()
            else None,
            source_label=(self._source_label.get() or None) if sources else None,
            framing=framed,
        )

    def _effort(self, var: StringVar) -> str | None:
        value = var.get()
        return None if value in ("", _NON_SPECIFIE) else value

    # -- Créer seulement / créer et démarrer (§6.6, §6.7) --

    def _create_only(self) -> None:
        request = self._build_request()
        if request is None:
            return
        try:
            result = facade.create_collaboration(request, adapters=ADAPTERS)
        except facade.CreationError as exc:
            self._error.configure(text=str(exc))
            return
        messagebox.showinfo(
            "Collaboration créée", "Collaboration créée — aucun appel fournisseur effectué.",
        )
        self._controller.show_suivi(result.path)

    def _create_and_start(self) -> None:
        request = self._build_request()
        if request is None:
            return
        resolved = self._resolved_timeout(request.collab)
        body = (
            ("Vous avez relu le texte qui deviendra demande.md. La création figera son "
             "empreinte. La poursuite lancera ensuite A.\n\n" if request.framing else "")
            + "La création du dossier est locale et ne consomme aucun quota.\n"
            "La poursuite lancera ensuite le premier appel fournisseur.\n\n"
            f"Agent : {request.agent_a}, rôle A\n"
            "Phase : proposition initiale\n"
            f"Délai effectif : {resolved.seconds:g} s\n"
            f"Origine : {resolved.origin}"
        )
        if not dialogs.confirm(
            self, "Créer et démarrer ?", body, ok_label="Créer et lancer le premier appel",
        ):
            return
        try:
            result = facade.create_collaboration(request, adapters=ADAPTERS)
        except facade.CreationError as exc:
            self._error.configure(text=str(exc))
            return
        self._controller.show_suivi(result.path)
        self._controller.start_run(result.path, timeout_seconds=resolved.seconds)

    # -- Cadrer avec un agent (`CADRAGE_AGENT.md` §4) --

    def _resolved_timeout(self, collab: Path) -> settings.Timeout:
        return settings.resolve_timeout(
            self._config_path.get() or None,
            float(self._timeout_override.get()) if self._timeout_override.get() else None,
            base=collab.parent,
        )

    def _start_framing(self) -> None:
        base = self._build_request(framing_start=True)
        if base is None:
            return
        try:
            timeout = self._resolved_timeout(base.collab).seconds
            f = cadrage.begin(self._controller, base, self._framing_panel, timeout)
        except (facade.CreationError, framing.FramingError, settings.SettingsError,
                ValueError) as exc:
            self._error.configure(text=str(exc))
            return
        self._error.configure(text="")
        cadrage.FramingDialog(self, self._controller, ("Idée", f.idea), f.start, self._on_draft)

    def _resume_framing(self) -> None:
        error = cadrage.resume(self, self._controller, self._on_draft)
        if error is not None:
            self._error.configure(text=error)

    def _on_draft(self, draft: str) -> None:
        """§4.4 : le brouillon remplace le contenu de l'éditeur ; on le corrige normalement."""
        self._demande_text.delete("1.0", "end")
        self._demande_text.insert("1.0", draft)
        self._demande_text.edit_modified(False)
        self._source_label_text.configure(
            text="Source affichée : brouillon du cadrage, à relire avant de créer"
        )
