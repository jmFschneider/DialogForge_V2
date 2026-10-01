"""Écran de création (`conception/GUI_V1.md` §6) : saisir ou importer une
demande, configurer la collaboration, la créer seule ou la créer et démarrer.

La validation autoritaire est celle de `facade.create_collaboration` — la
**même** que `new` en CLI (§6.5) : ce module ne revalide rien, il rassemble
une `CreationRequest` et affiche le refus tel quel si la façade en rend un.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import BooleanVar, Misc, StringVar, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from ... import facade, framing, model_catalog, settings, storage
from ...models import MissionKind, ReviewerAccess
from ...registry import ADAPTERS
from .. import dialogs, widgets
from . import cadrage, lancement

if TYPE_CHECKING:
    from ..controller import Controller

_KIND = {"Recherche": MissionKind.RECHERCHE, "Conception": MissionKind.CONCEPTION}
_ACCESS = {"Consultation": ReviewerAccess.CONSULT, "Contexte seul": ReviewerAccess.CONTEXT_ONLY}
_NON_SPECIFIE = "(non spécifié)"
_KIND_HINT = {
    "Recherche": "Établir un dossier sourcé à partir d'une idée — une source : web ou corpus.",
    "Conception": "Tirer d'un dossier le plan et les solutions, avant le code — corpus exigé.",
}


class CreationView(ttk.Frame):
    def __init__(
        self, master: Misc, controller: Controller, *, from_research: Path | None = None,
    ) -> None:
        super().__init__(master)
        self._controller = controller
        self._from_research = from_research
        self._catalog_error: str | None = None
        try:
            self._model_catalog = model_catalog.load()
        except model_catalog.ModelCatalogError as exc:
            self._model_catalog = {}
            self._catalog_error = str(exc)
        self._imported_path: str | None = None
        self._imported_text: str | None = None
        self._mode = StringVar(value="saisir")
        self._kind = StringVar(value="Recherche")
        self._agent_a = StringVar(value=sorted(ADAPTERS)[0])
        self._agent_b = StringVar(value=sorted(ADAPTERS)[-1])
        self._revisions = StringVar(value="2")
        self._source_root = StringVar()
        self._source_list = StringVar()
        self._source_label = StringVar()
        self._model_a = StringVar(value=model_catalog.DEFAULT)
        self._model_b = StringVar(value=model_catalog.DEFAULT)
        self._effort_a = StringVar(value=_NON_SPECIFIE)
        self._effort_b = StringVar(value=_NON_SPECIFIE)
        self._web_access = BooleanVar(value=False)
        self._reviewer = StringVar(value="Consultation")
        self._build()
        if from_research is not None:
            self._follow_up(from_research)

    def _follow_up(self, research: Path) -> None:
        """`TYPES_DE_MISSION.md` D4 : la recherche acceptée remplace le corpus à déclarer."""
        dest, text = facade.follow_up_defaults(research)
        self._dossier.set(str(dest))
        self._kind.set("Conception")
        self._demande_text.insert("1.0", text)
        for child in self._corpus_frame.winfo_children():
            child.destroy()
        ttk.Label(self._corpus_frame, text=facade.follow_up_label(research)).pack(anchor="w")

    # -- Construction --

    def _build(self) -> None:
        ttk.Label(self, text="Nouvelle collaboration", font=("", 13, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16)

        folder_row = ttk.Frame(body)
        folder_row.pack(fill="x")
        ttk.Label(folder_row, text="Dossier de la nouvelle collaboration").pack(anchor="w")
        root = self._controller.collaborations_root()
        self._dossier = StringVar(value=str(root / "nouvelle-collaboration") if root else "")
        entry_row = ttk.Frame(folder_row)
        entry_row.pack(fill="x")
        ttk.Entry(entry_row, textvariable=self._dossier).pack(side="left", fill="x", expand=True)
        ttk.Button(entry_row, text="Choisir…", command=self._choose_folder).pack(side="left")

        self._build_demande(body)
        self._build_type_and_agents(body)
        self._corpus_frame = ttk.Frame(body)
        self._build_corpus(self._corpus_frame)
        self._corpus_frame.pack(fill="x")

        widgets.disclosure(body, "Réglages avancés de la collaboration", self._build_advanced)
        widgets.disclosure(body, "Réglages du prochain lancement", self._build_launch)

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
            ("Cadrer avec un agent (une idée suffit)", "agent"),
        ):
            ttk.Radiobutton(
                modes, text=text, value=value, variable=self._mode, command=self._on_mode,
            ).pack(side="left")
        editor = ttk.Frame(parent)
        editor.pack(fill="x")
        self._demande_text = ScrolledText(editor, height=8, wrap="word")
        self._demande_text.pack(fill="x", pady=(4, 0))
        import_row = ttk.Frame(editor)
        import_row.pack(fill="x", pady=(4, 0))
        import_button = ttk.Button(import_row, text="Importer…", command=self._import_file)
        import_button.pack(side="left")
        self._source_label_text = ttk.Label(import_row, text="Source affichée : saisie directe")
        self._source_label_text.pack(side="left", padx=(8, 0))
        self._demande_text.bind("<<Modified>>", self._on_demande_changed)
        self._framing_panel = cadrage.FramingPanel(
            parent, catalog=self._model_catalog, on_start=self._start_framing,
            on_resume=self._resume_framing, anchor=modes, editor=editor,
            import_button=import_button,
        )

    def _build_type_and_agents(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(12, 0))
        ttk.Label(row, text="Type").pack(side="left")
        for label in _KIND:
            ttk.Radiobutton(row, text=label, value=label, variable=self._kind).pack(
                side="left", padx=(8, 0)
            )
        ttk.Checkbutton(
            row, text="Accès web pour A et B", variable=self._web_access,
        ).pack(side="left", padx=(16, 0))
        hint = ttk.Label(parent, text=_KIND_HINT[self._kind.get()], foreground="#555")
        hint.pack(anchor="w")
        self._kind.trace_add("write", lambda *_: hint.configure(text=_KIND_HINT[self._kind.get()]))
        agents = ttk.Frame(parent)
        agents.pack(fill="x", pady=(8, 0))
        ttk.Label(agents, text="Agent A").pack(side="left")
        agent_a = ttk.Combobox(
            agents, textvariable=self._agent_a, values=sorted(ADAPTERS), state="readonly", width=10,
        )
        agent_a.pack(side="left", padx=(4, 12))
        agent_a.bind("<<ComboboxSelected>>", lambda _event: self._sync_model("A"))
        ttk.Label(agents, text="Agent B").pack(side="left")
        agent_b = ttk.Combobox(
            agents, textvariable=self._agent_b, values=sorted(ADAPTERS), state="readonly", width=10,
        )
        agent_b.pack(side="left", padx=(4, 12))
        agent_b.bind("<<ComboboxSelected>>", lambda _event: self._sync_model("B"))
        ttk.Label(agents, text="Révisions maximales").pack(side="left")
        ttk.Entry(agents, textvariable=self._revisions, width=4).pack(side="left", padx=(4, 0))

    def _build_corpus(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent, text="Corpus local — exigé en conception ; en recherche, si le web est fermé",
        ).pack(anchor="w", pady=(12, 0))
        for label, var, browse in (
            ("Racine", self._source_root,
             widgets.browse(self._source_root, "Racine du corpus", folder=True)),
            ("Liste", self._source_list, widgets.browse(self._source_list, "Liste du corpus")),
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
            agent = self._agent_a.get() if label == "A" else self._agent_b.get()
            selector = ttk.Combobox(
                row, textvariable=model, values=model_catalog.choices(self._model_catalog, agent),
                state="readonly",
            )
            selector.pack(side="left", fill="x", expand=True)
            if label == "A":
                self._model_selector_a = selector
            else:
                self._model_selector_b = selector
            ttk.Label(row, text=f"Effort {label}", width=10).pack(side="left", padx=(8, 0))
            ttk.Combobox(
                row, textvariable=effort, values=self._effort_values(label), state="readonly",
                width=14,
            ).pack(side="left")
        access_row = ttk.Frame(parent)
        access_row.pack(fill="x")
        ttk.Label(access_row, text="Accès du critique").pack(side="left")
        for label in _ACCESS:
            ttk.Radiobutton(
                access_row, text=label, value=label, variable=self._reviewer,
            ).pack(side="left", padx=(8, 0))

    def _build_launch(self, parent: ttk.Frame) -> None:
        self._launch = lancement.LaunchPanel(parent, self._dossier)
        self._launch.pack(fill="x")

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

    def _sync_model(self, role: str) -> None:
        agent = (self._agent_a if role == "A" else self._agent_b).get()
        model = self._model_a if role == "A" else self._model_b
        selector = self._model_selector_a if role == "A" else self._model_selector_b
        options = model_catalog.choices(self._model_catalog, agent)
        selector.configure(values=options)
        if model.get() not in options:
            model.set(model_catalog.DEFAULT)

    def _chosen_model(self, role: str) -> str | None:
        agent = (self._agent_a if role == "A" else self._agent_b).get()
        model = (self._model_a if role == "A" else self._model_b).get()
        return model_catalog.selected(self._model_catalog, agent, model)

    def _on_mode(self) -> None:
        """Quitter le mode agent termine le cadrage ; son brouillon reste dans l'éditeur."""
        if self._mode.get() == "agent":
            self._framing_panel.enter()
        else:
            self._controller.discard_framing()
            self._framing_panel.leave()
        if self._mode.get() == "saisir":
            self._reset_import()

    # -- Choix de fichiers/dossiers --

    def _choose_folder(self) -> None:
        current = Path(self._dossier.get()) if self._dossier.get() else None
        chosen = filedialog.askdirectory(
            title="Répertoire parent de la nouvelle collaboration",
            initialdir=str(current.parent) if current else str(Path.home()),
        )
        if chosen:
            name = current.name if current else "nouvelle-collaboration"
            self._dossier.set(str(Path(chosen) / name))

    # -- Validation locale et résolution du délai (§6.4, §6.5 niveau 1) --

    def _local_errors(self, *, framing_start: bool) -> str | None:
        if self._catalog_error is not None:
            return self._catalog_error
        if not self._dossier.get().strip():
            return "Le dossier est requis."
        if not framing_start and not self._current_text().strip():
            return "La demande ne peut pas être vide."
        if not self._revisions.get().strip().lstrip("-").isdigit():
            return "Révisions maximales : un entier attendu."
        try:
            self._chosen_model("A")
            self._chosen_model("B")
        except model_catalog.ModelCatalogError as exc:
            return str(exc)
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
            model_a=self._chosen_model("A"), model_b=self._chosen_model("B"),
            effort_a=self._effort(self._effort_a), effort_b=self._effort(self._effort_b),
            web_access=self._web_access.get(),
            source_root=Path(self._source_root.get()) if sources and self._source_root.get()
            else None,
            source_list=Path(self._source_list.get()) if sources and self._source_list.get()
            else None,
            source_label=(self._source_label.get() or None) if sources else None,
            framing=framed, from_research=self._from_research,
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
        self._controller.record_created(result.path)
        messagebox.showinfo(
            "Collaboration créée",
            "Collaboration créée — aucun appel fournisseur effectué.\n\n"
            f"Dossier : {result.path}",
        )
        self._controller.show_suivi(result.path)

    def _create_and_start(self) -> None:
        request = self._build_request()
        if request is None:
            return
        resolved = self._launch.resolved(request.collab)
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
        self._controller.record_created(result.path)
        self._controller.show_suivi(result.path)
        self._controller.start_run(result.path, timeout_seconds=resolved.seconds)

    # -- Cadrer avec un agent (`CADRAGE_AGENT.md` §4) --

    def _start_framing(self) -> None:
        base = self._build_request(framing_start=True)
        if base is None:
            return
        try:
            timeout = self._launch.resolved(base.collab).seconds
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
        self._framing_panel.reveal()
