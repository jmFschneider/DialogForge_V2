"""Passage d'une conception acceptée au développement dans Ubuntu WSL2.

L'écran reprend ce que la référence d'exécution a enregistré : après une fermeture ou un incident,
il relit le dossier Runner (sans rien relancer) et ne propose que le départ qui convient.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import Misc, StringVar, filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING, Any

from ... import decisions, delivery, executions
from ...models import positive_seconds
from .. import dialogs
from ..runner_session import RunnerRequest, RunnerSession

if TYPE_CHECKING:
    from ..controller import Controller

_POLL_MS = 500
_LABELS = {
    "start": "Préparer et lancer", "launch": "Lancer A", "continue": "Continuer avec A",
    "correct": "Demander une correction",
}


class RunnerView(ttk.Frame):
    def __init__(self, master: Misc, controller: Controller, collaboration: Path) -> None:
        super().__init__(master)
        self._controller = controller
        self._collaboration = collaboration
        self._session: RunnerSession | None = None
        self._after_id: str | None = None
        self._primary_action: str | None = None
        self._note = ""
        self._editable: list[ttk.Widget] = []
        self._unlocked = True
        self._pairs: list[tuple[StringVar, StringVar]] = []
        self._found: executions.Found | None = None
        self._runner_state: dict[str, Any] | None = None
        self._find()
        shown = executions.parameters(collaboration, self._found)
        self._mode, self._repo, self._base = (
            StringVar(value=shown.mode), StringVar(value=shown.repo), StringVar(value=shown.base),
        )
        self._run = StringVar(value=shown.run)
        self._timeout = StringVar(value=str(shown.agent_timeout))
        self._validation_timeout = StringVar(value=str(shown.validation_timeout))
        self._token = StringVar()
        self._build(shown.validations)
        self._refresh()

    def destroy(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        super().destroy()

    def _find(self) -> None:
        """Relit l'export et la référence de la version acceptée actuelle."""
        try:
            self._found = executions.find(self._collaboration)
        except (ValueError, RuntimeError, OSError) as exc:
            self._found, self._note = None, f"Version acceptée illisible : {exc}"

    def _field(
        self, parent: ttk.Frame, label: str, value: StringVar, *, lock: bool = True,
    ) -> ttk.Entry:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=25).pack(side="left")
        entry = ttk.Entry(row, textvariable=value)
        entry.pack(side="left", fill="x", expand=True)
        if lock:
            self._editable.append(entry)
        return entry

    def _button(self, parent: Misc, text: str, command: Any) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=command)
        self._editable.append(button)
        return button

    def _build(self, saved: list[list[str]]) -> None:
        ttk.Label(self, text="Développer avec le Runner", font=("", 13, "bold")).pack(
            anchor="w", padx=16, pady=(16, 4),
        )
        ttk.Label(
            self, text=f"Conception acceptée : {self._collaboration}", wraplength=650,
        ).pack(anchor="w", padx=16)
        ttk.Label(
            self, text="A, seul agent, réalise toute la conception dans un clone isolé sous "
            "Ubuntu, jamais dans votre dossier ; il poursuit ou corrige un échec de validation "
            "dans la durée indiquée, et s'arrête s'il a besoin de vous. Les validations réussies, "
            "le commit est remis dans code/ pour l'essayer ; votre branche n'avance que si vous "
            "acceptez cette version.",
            wraplength=650,
        ).pack(anchor="w", padx=16, pady=(4, 8))
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=16)
        modes = ttk.Frame(body)
        modes.pack(fill="x")
        for value, label in (("nouveau", "Nouveau projet (dépôt créé pour vous)"),
                             ("existant", "Dépôt existant")):
            choice = ttk.Radiobutton(
                modes, text=label, value=value, variable=self._mode, command=self._mode_changed,
            )
            choice.pack(side="left", padx=(0, 16))
            self._editable.append(choice)
        self._repo_entry = self._field(body, "Dossier du projet", self._repo)
        self._button(self._repo_entry.master, "Choisir…", self._choose_repo).pack(side="left")
        self._base_entry = self._field(body, "Commit de départ", self._base)
        self._field(body, "Dossier Runner dans Ubuntu", self._run)
        self._field(body, "Durée maximale agent (s)", self._timeout, lock=False)
        self._field(body, "Délai par validation (s)", self._validation_timeout)
        ttk.Label(
            body, text="Validations finales — exécutable et arguments, lancés à la racine du "
            "dépôt, sans shell (ex. : node  --test)",
        ).pack(anchor="w", pady=(8, 0))
        self._rows = ttk.Frame(body)
        self._rows.pack(fill="x")
        for executable, arguments in executions.rows_from_validations(saved) or [("", "")]:
            self._add_row(executable, arguments)
        self._button(body, "Ajouter une validation", self._add_row).pack(anchor="w", pady=2)
        ttk.Label(body, text="Conception acceptée — les validations à recopier ci-dessus :").pack(
            anchor="w", pady=(6, 0),
        )
        conception = ScrolledText(body, height=6, wrap="word")
        try:
            conception.insert("1.0", (self._collaboration / decisions.DELIVERED).read_text("utf-8"))
        except OSError as exc:
            conception.insert("1.0", f"Conception illisible : {exc}")
        conception.configure(state="disabled")
        conception.pack(fill="x")
        ttk.Label(body, text="Message pour A — correction précise ou réponse à sa question :"
                  ).pack(anchor="w", pady=(6, 0))
        self._correction = ScrolledText(body, height=3, wrap="word", state="disabled")
        self._correction.pack(fill="x")
        ttk.Label(body, text="Bilan de A (instructions, vérifications, limites) et validations :"
                  ).pack(anchor="w", pady=(6, 0))
        self._report = ScrolledText(body, height=7, wrap="word", state="disabled")
        self._report.pack(fill="x")
        token_row = ttk.Frame(body)
        token_row.pack(fill="x", pady=(8, 0))
        ttk.Label(token_row, text="Jeton Claude (en mémoire)", width=25).pack(side="left")
        ttk.Entry(token_row, textvariable=self._token, show="•").pack(
            side="left", fill="x", expand=True,
        )
        self._forget = ttk.Button(token_row, text="Oublier le jeton", command=self._forget_token)
        self._forget.pack(side="left", padx=(4, 0))
        self._status = ttk.Label(body, text="Prêt", wraplength=650, justify="left")
        self._status.pack(anchor="w", pady=(10, 0))
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=16, pady=16)
        self._back_button = ttk.Button(actions, text="Retour au suivi", command=self._back)
        self._back_button.pack(side="left")
        self._accept_button = ttk.Button(
            actions, text="Accepter cette version", state="disabled", command=self._accept,
        )
        self._accept_button.pack(side="right")
        self._deliver_button = ttk.Button(
            actions, text="Remettre dans code/", state="disabled", command=self._deliver,
        )
        self._deliver_button.pack(side="right", padx=(0, 8))
        self._primary = ttk.Button(
            actions, text=_LABELS["start"], state="disabled",
            command=lambda: self._begin(self._primary_action),
        )
        self._primary.pack(side="right")
        self._collect = ttk.Button(
            actions, text="Refaire les validations", state="disabled",
            command=lambda: self._begin("collect"),
        )
        self._collect.pack(side="right", padx=(0, 8))
        self._mode_changed()

    def _add_row(self, executable: str = "", arguments: str = "") -> None:
        row = ttk.Frame(self._rows)
        row.pack(fill="x", pady=1)
        pair = (StringVar(value=executable), StringVar(value=arguments))
        self._pairs.append(pair)
        first = ttk.Entry(row, textvariable=pair[0], width=16)
        first.pack(side="left")
        second = ttk.Entry(row, textvariable=pair[1])
        second.pack(side="left", fill="x", expand=True, padx=4)
        self._button(row, "Retirer", lambda: self._drop(row, pair)).pack(side="left")
        self._editable.extend((first, second))

    def _drop(self, row: ttk.Frame, pair: tuple[StringVar, StringVar]) -> None:
        self._pairs.remove(pair)
        row.destroy()

    def _mode_changed(self) -> None:
        code = str(executions.default_code(self._collaboration))
        existing = self._mode.get() == "existant"
        if existing and self._repo.get() == code:
            self._repo.set("")
        elif not existing and not self._repo.get():
            self._repo.set(code)
        self._sync_base()

    def _sync_base(self) -> None:
        self._base_entry.state(
            ["!disabled"] if self._unlocked and self._mode.get() == "existant" else ["disabled"]
        )

    def _choose_repo(self) -> None:
        chosen = filedialog.askdirectory(title="Dossier du projet")
        if chosen:
            self._repo.set(chosen)

    def _back(self) -> None:
        self._controller.show_suivi(self._collaboration)

    def _local(self, label: str, work: Any) -> None:
        """Une opération locale, sans agent ni jeton : remise ou acceptation."""
        state = self._runner_state
        self._deliver_button.configure(state="disabled")
        self._accept_button.configure(state="disabled")
        self._status.configure(text=label)
        self.update_idletasks()
        try:
            work()
            self._note = ""
        except (OSError, ValueError, RuntimeError) as exc:
            self._note = f"Opération arrêtée, rien n'est écrasé : {exc}"
        self._find()
        self._apply(state)

    def _deliver(self) -> None:
        if self._found is not None and self._runner_state is not None:
            found, state = self._found, self._runner_state
            self._local("Remise du candidat dans code/…",
                        lambda: delivery.deliver(self._collaboration, found, state))

    def _accept(self) -> None:
        shown = self._delivered()
        if shown is None or not dialogs.confirm(
            self, "Accepter cette version ?",
            f"Commit essayé : {shown.head}\nDossier d'essai : {shown.code}\n"
            f"Branche cible : {shown.target_branch} de {shown.target}\n\n"
            "La branche cible avance uniquement en fast-forward.",
            ok_label="Accepter cette version",
        ):
            return
        found = self._found
        assert found is not None
        self._local("Acceptation…", lambda: delivery.accept(self._collaboration, found))

    def _forget_token(self) -> None:
        self._controller.runner_token = ""
        self._token.set("")
        self._forget.configure(state="disabled")

    def _delivered(self) -> delivery.Delivered | None:
        return None if self._found is None else delivery.current(self._collaboration, self._found)

    def _request(self, action: str) -> RunnerRequest:
        if self._found is None:
            raise ValueError("la version acceptée n'est pas lisible")
        if action == "start":
            if not self._run.get().strip() or not self._repo.get().strip():
                raise ValueError("indiquer le dossier du projet et le dossier Runner")
            mode = self._mode.get()
            shown = executions.Parameters(
                mode, self._repo.get().strip(),
                self._base.get().strip() if mode == "existant" else "HEAD", self._run.get().strip(),
                executions.validations_from_rows([(a.get(), b.get()) for a, b in self._pairs]),
                0.0, positive_seconds(float(self._validation_timeout.get())),
                self._found.data["wsl"]["distribution"] if self._found.data else None,
            )
        else:
            shown = executions.parameters(self._collaboration, self._found)
        calls = action in _LABELS
        message = self._correction.get("1.0", "end").strip()
        correction = message if action in {"correct", "continue"} else ""
        if action == "correct" and not correction:
            raise ValueError("décrire la correction attendue avant un nouvel appel")
        token = self._token.get() or self._controller.runner_token
        if calls and not token:
            raise ValueError("saisir le jeton Claude pour l'appel agent")
        return RunnerRequest(
            action=action, collaboration=self._collaboration, found=self._found, mode=shown.mode,
            repo=Path(shown.repo), base=shown.base, validations=shown.validations, run=shown.run,
            token=token if calls else "",
            timeout=positive_seconds(float(self._timeout.get())),
            validation_timeout=shown.validation_timeout, distro=shown.distro,
            correction=correction,
        )

    def _refresh(self) -> None:
        """Relit la référence puis le dossier Linux ; sans référence : préparation neuve."""
        if self._found is None:
            self._apply(None, locked=True)
        elif self._found.data is None:
            self._apply(None)
        else:
            self._begin("inspect")

    def _begin(self, action: str | None) -> None:
        assert action is not None
        try:
            request = self._request(action)
        except (ValueError, TypeError) as exc:
            self._status.configure(text=f"À corriger : {exc}")
            return
        token = request.token  # la session l'efface du lancement ; la fenêtre le garde
        session = self._controller.start_runner(request)
        if session is None:
            self._status.configure(text="Une autre exécution est encore active.")
            return
        self._controller.runner_token = token or self._controller.runner_token
        self._token.set("")
        self._session = session
        if action != "inspect":
            self._note = ""
            self._correction.configure(state="normal")
            self._correction.delete("1.0", "end")
        for button in (self._primary, self._collect, self._back_button, self._deliver_button,
                       self._accept_button):
            button.configure(state="disabled")
        self._poll()

    def _apply(self, state: dict[str, Any] | None, *, locked: bool = False) -> None:
        self._runner_state = state
        allowed = () if locked else executions.actions(state)
        self._primary_action = next((a for a in _LABELS if a in allowed), None)
        self._primary.configure(
            text=_LABELS.get(self._primary_action or "", _LABELS["start"]),
            state="normal" if self._primary_action else "disabled",
        )
        self._collect.configure(state="normal" if "collect" in allowed else "disabled")
        shown = self._delivered()
        self._deliver_button.configure(
            state="normal" if state and state.get("package") and not state.get("locked")
            else "disabled",
        )
        self._accept_button.configure(
            state="normal" if shown is not None and not shown.accepted else "disabled",
        )
        self._back_button.configure(state="normal")
        self._forget.configure(state="normal" if self._controller.runner_token else "disabled")
        self._unlocked = not locked and (state is None or state["stage"] == "absent")
        for widget in self._editable:
            if widget.winfo_exists():
                widget.state(["!disabled"] if self._unlocked else ["disabled"])
        self._sync_base()
        self._correction.configure(
            state="normal" if {"correct", "continue"} & set(allowed) else "disabled",
        )
        report = state.get("report", "") if state else ""
        checks = state.get("checks", []) if state else []
        results = "\n".join(
            f"{' '.join(check['command'])} : {check['outcome']}"
            for check in checks if isinstance(check, dict)
            and isinstance(check.get("command"), list) and "outcome" in check
        )
        self._report.configure(state="normal")
        self._report.delete("1.0", "end")
        self._report.insert("1.0", "\n\n".join(filter(None, (results, report))))
        self._report.configure(state="disabled")
        described = "" if locked else executions.describe(state)
        trial = "" if shown is None else (
            f"{'Version acceptée' if shown.accepted else 'Prêt à essayer'} : {shown.code} — "
            f"branche {shown.branch}, commit {shown.head[:12]} (validé sous Ubuntu)."
        )
        self._status.configure(text="\n".join(filter(None, (self._note, trial, described))))

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
        elif session.request.action != "inspect":
            self._find()
            self._note = "\n".join(filter(None, (text, self._note)))
            self._refresh()
        else:
            self._apply(session.state if session.error is None else {
                "stage": "invalide", "detail": session.error,
            })
