"""Passage d'une conception acceptée au développement dans Ubuntu WSL2."""

from __future__ import annotations

import json
from pathlib import Path
from tkinter import Misc, StringVar, filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from ...models import positive_seconds
from ..runner_session import RunnerRequest, RunnerSession

if TYPE_CHECKING:
    from ..controller import Controller

_POLL_MS = 500


class RunnerView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller, collaboration: Path) -> None:
        super().__init__(master)
        self._controller = controller
        self._collaboration = collaboration
        self._session: RunnerSession | None = None
        self._after_id: str | None = None
        self._repo = StringVar()
        self._base = StringVar(value="HEAD")
        self._export = StringVar(
            value=str(collaboration.parent / f"{collaboration.name}-dev-export")
        )
        self._run = StringVar(value=f"~/dialogforge-runs/{collaboration.name}")
        self._timeout = StringVar(value="3600")
        self._validation_timeout = StringVar(value="300")
        self._token = StringVar()
        self._build()

    def destroy(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        super().destroy()

    def _field(self, parent: ttk.Frame, label: str, value: StringVar) -> ttk.Frame:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=25).pack(side="left")
        ttk.Entry(row, textvariable=value).pack(side="left", fill="x", expand=True)
        return row

    def _build(self) -> None:
        ttk.Label(self, text="Développer avec le Runner", font=("", 13, "bold")).pack(
            anchor="w", padx=16, pady=(16, 4),
        )
        ttk.Label(
            self, text=f"Conception acceptée : {self._collaboration}", wraplength=650,
        ).pack(anchor="w", padx=16)
        ttk.Label(
            self, text="Le Runner crée un clone isolé sous Ubuntu, puis un paquet à relire. "
            "Aucun code n'est intégré automatiquement.", wraplength=650,
        ).pack(anchor="w", padx=16, pady=(4, 8))
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16)
        repo_row = self._field(body, "Dépôt source", self._repo)
        ttk.Button(repo_row, text="Choisir…", command=self._choose_repo).pack(side="left")
        self._field(body, "Commit de départ", self._base)
        self._field(body, "Export de la conception", self._export)
        self._field(body, "Dossier Runner dans Ubuntu", self._run)
        self._field(body, "Durée maximale agent (s)", self._timeout)
        self._field(body, "Délai par validation (s)", self._validation_timeout)
        ttk.Label(body, text="Validations finales — JSON, une liste d'arguments par commande").pack(
            anchor="w", pady=(8, 0),
        )
        self._validations = ScrolledText(body, height=4, wrap="word")
        self._validations.pack(fill="x")
        token_row = ttk.Frame(body)
        token_row.pack(fill="x", pady=(8, 0))
        ttk.Label(token_row, text="Jeton Claude (non conservé)", width=25).pack(side="left")
        ttk.Entry(token_row, textvariable=self._token, show="•").pack(
            side="left", fill="x", expand=True,
        )
        self._status = ttk.Label(body, text="Prêt", wraplength=650, justify="left")
        self._status.pack(anchor="w", pady=(10, 0))
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=16, pady=16)
        self._back_button = ttk.Button(actions, text="Retour au suivi", command=self._back)
        self._back_button.pack(side="left")
        self._start = ttk.Button(
            actions, text="Exporter et lancer", command=lambda: self._launch("start"),
        )
        self._start.pack(side="right")
        self._continue = ttk.Button(
            actions, text="Continuer l'agent", command=lambda: self._launch("continue"),
        )
        self._continue.pack(side="right", padx=(0, 8))
        self._collect = ttk.Button(
            actions, text="Collecter sans appel", command=lambda: self._launch("collect"),
        )
        self._collect.pack(side="right", padx=(0, 8))

    def _choose_repo(self) -> None:
        chosen = filedialog.askdirectory(title="Dépôt source Git")
        if chosen:
            self._repo.set(chosen)

    def _back(self) -> None:
        self._controller.show_suivi(self._collaboration)

    def _request(self, action: str) -> RunnerRequest:
        run = self._run.get().strip()
        if not run or (action == "start" and not self._repo.get().strip()):
            raise ValueError("indiquer le dépôt source et le dossier Runner")
        try:
            commands = json.loads(self._validations.get("1.0", "end-1c") or "[]")
        except json.JSONDecodeError as exc:
            raise ValueError(f"validations JSON invalides : {exc}") from exc
        if action == "start" and (not isinstance(commands, list) or not commands or not all(
            isinstance(command, list) and command and all(
                isinstance(arg, str) and arg for arg in command
            ) for command in commands
        )):
            raise ValueError("indiquer au moins une validation comme liste d'arguments")
        token = self._token.get()
        if action != "collect" and not token:
            raise ValueError("saisir le jeton Claude pour l'appel agent")
        return RunnerRequest(
            action=action, collaboration=self._collaboration,
            export=Path(self._export.get()), repo=Path(self._repo.get()),
            base=self._base.get().strip(), validations=commands,
            run=run, token=token,
            timeout=positive_seconds(float(self._timeout.get())),
            validation_timeout=positive_seconds(float(self._validation_timeout.get())),
        )

    def _launch(self, action: str) -> None:
        try:
            request = self._request(action)
        except (ValueError, TypeError) as exc:
            self._status.configure(text=f"À corriger : {exc}")
            return
        session = self._controller.start_runner(request)
        if session is None:
            self._status.configure(text="Une autre exécution est encore active.")
            return
        self._token.set("")
        self._session = session
        self._start.configure(state="disabled")
        self._continue.configure(state="disabled")
        self._collect.configure(state="disabled")
        self._back_button.configure(state="disabled")
        self._poll()

    def _poll(self) -> None:
        self._after_id = None
        session = self._session
        if session is None:
            return
        text = f"{session.stage}\nDossier Ubuntu : {session.run_path}"
        if session.package:
            text += f"\nPaquet : {session.package}"
        if session.error:
            text += f"\nCause : {session.error}"
        self._status.configure(text=text)
        if session.thread.is_alive():
            self._after_id = self.after(_POLL_MS, self._poll)
        else:
            self._start.configure(state="normal")
            self._continue.configure(state="normal")
            self._collect.configure(state="normal")
            self._back_button.configure(state="normal")
