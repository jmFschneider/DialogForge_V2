"""Cadrer avec un agent, dans la GUI (`conception/CADRAGE_AGENT.md` §4).

L'écran de création garde la main sur la demande : ce module rassemble le mode
agent (§4.1), mène la conversation dans une modale (§4.2), et rend le brouillon
de F à l'éditeur existant (§4.4). Chaque tour de F passe par l'unique fil moteur
du contrôleur (§4.3) ; le fil Tk n'appelle jamais l'adaptateur, il sonde la fin du
tour par `after()`. Les règles du cadrage (compteur, balises, relance explicite)
sont celles de `framing.Framing`, que la CLI emploie aussi : rien n'est redécidé ici.
"""

from __future__ import annotations

from collections.abc import Callable
from tkinter import Misc, StringVar, Toplevel, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING

from ... import facade, framing, model_catalog
from ...adapters.base import FramingSessionSpec
from ...demande import validate_framed
from ...framing import DRAFT, QUESTION, READY, Turn
from ...registry import ADAPTERS
from .. import dialogs

if TYPE_CHECKING:
    from ..controller import Controller

_NON_SPECIFIE = "(non spécifié)"
_POLL_MS = 200
_BUSY = "F travaille — un appel fournisseur est en cours."


class FramingPanel(ttk.Frame):
    """§4.1 : adaptateur F, modèle et effort, idée de départ. Les sources facultatives
    sont celles du corpus de l'écran de création ; A et B restent réglés à part."""

    def __init__(
        self, master: Misc, *, catalog: dict[str, tuple[str, ...]],
        on_start: Callable[[], None], on_resume: Callable[[], None],
        anchor: Misc, editor: ttk.Frame, import_button: ttk.Button,
    ) -> None:
        super().__init__(master)
        self._catalog = catalog
        self._anchor, self._editor, self._import_button = anchor, editor, import_button
        self._revealed = False
        self._draft_title = ttk.Label(
            master, text="Demande rédigée par F — à relire et corriger avant de créer",
            font=("", 10, "bold"),
        )
        self.agent = StringVar(value=sorted(ADAPTERS)[0])
        self.model = StringVar(value=model_catalog.DEFAULT)
        self.effort = StringVar(value=_NON_SPECIFIE)
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(4, 0))
        ttk.Label(row, text="Agent de cadrage").pack(side="left")
        agent_selector = ttk.Combobox(
            row, textvariable=self.agent, values=sorted(ADAPTERS), state="readonly", width=10,
        )
        agent_selector.pack(side="left", padx=(4, 12))
        agent_selector.bind("<<ComboboxSelected>>", lambda _event: self._sync_model())
        ttk.Label(row, text="Modèle").pack(side="left")
        self._model_selector = ttk.Combobox(
            row, textvariable=self.model,
            values=model_catalog.choices(catalog, self.agent.get()), state="readonly", width=16,
        )
        self._model_selector.pack(side="left", padx=(4, 12))
        ttk.Label(row, text="Effort").pack(side="left")
        efforts = ttk.Combobox(row, textvariable=self.effort, state="readonly", width=14)
        efforts.configure(postcommand=lambda: efforts.configure(values=self._efforts()))
        efforts.pack(side="left", padx=(4, 0))
        ttk.Label(self, text="Idée de départ, même incomplète").pack(anchor="w", pady=(4, 0))
        self.idea = ScrolledText(self, height=4, wrap="word")
        self.idea.pack(fill="x")
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(4, 0))
        ttk.Button(buttons, text="Commencer le cadrage", command=on_start).pack(side="left")
        ttk.Button(buttons, text="Reprendre le cadrage", command=on_resume).pack(
            side="left", padx=(8, 0)
        )

    def enter(self) -> None:
        """Retour d'usage du 2026-09-28 : en mode agent, l'idée est la seule saisie. La
        demande éditable n'apparaît qu'avec le brouillon de F, juste sous le cadrage."""
        self.pack(fill="x", after=self._anchor)
        self._import_button.state(["disabled"])
        if not self._revealed:
            self._editor.pack_forget()

    def reveal(self) -> None:
        self._revealed = True
        self._draft_title.pack(anchor="w", pady=(12, 0), after=self)
        self._editor.pack(fill="x", after=self._draft_title)

    def leave(self) -> None:
        self._revealed = False
        self.pack_forget()
        self._draft_title.pack_forget()
        self._import_button.state(["!disabled"])
        self._editor.pack(fill="x", after=self._anchor)

    def chosen_effort(self) -> str | None:
        value = self.effort.get()
        return None if value in ("", _NON_SPECIFIE) else value

    def chosen_model(self) -> str | None:
        return model_catalog.selected(self._catalog, self.agent.get(), self.model.get())

    def _sync_model(self) -> None:
        options = model_catalog.choices(self._catalog, self.agent.get())
        self._model_selector.configure(values=options)
        if self.model.get() not in options:
            self.model.set(model_catalog.DEFAULT)

    def _efforts(self) -> tuple[str, ...]:
        adapter = ADAPTERS.get(self.agent.get())
        return (_NON_SPECIFIE, *(() if adapter is None else adapter.capabilities.effort_levels))


def begin(
    controller: Controller, base: facade.CreationRequest, panel: FramingPanel, timeout: float,
) -> framing.Framing:
    """Tous les refus déterministes avant la session et le premier appel (§3.2) : fil
    moteur libre, idée, création, prévol de F, sources copiées. Lève `CreationError` ou
    `FramingError` ; rien n'est ouvert dans ce cas."""
    idea = panel.idea.get("1.0", "end-1c").strip()
    if controller.has_active_run():
        raise framing.FramingError("une exécution est active dans cette fenêtre")
    if not idea:
        raise framing.FramingError("décrivez votre idée, même incomplète")
    facade.check_creation(base, adapters=ADAPTERS)
    agent, effort = panel.agent.get(), panel.chosen_effort()
    try:
        chosen_model = panel.chosen_model()
    except model_catalog.ModelCatalogError as exc:
        raise framing.FramingError(str(exc)) from exc
    model, _ = framing.check_adapter(agent, ADAPTERS, chosen_model, effort)
    root = framing.prepare(
        base.kind, base.source_root, base.source_list, base.source_label, base.web_access,
    )
    spec = FramingSessionSpec(model, timeout, root / "travail", effort)
    return controller.open_framing(ADAPTERS[agent], spec, root, idea)


def reviewed(
    controller: Controller, text: str,
) -> tuple[str | None, framing.FramingArtifacts | None]:
    """Le texte relu dans l'éditeur devient `demande.md` ; les sources sont celles que F a
    lues, jamais relues depuis le projet (§2.2, §2.6). Rend le refus, ou les artefacts."""
    f = controller.framing
    if f is None or f.draft is None:
        return "Terminez le cadrage : aucun brouillon à créer.", None
    problems = validate_framed(text)
    if problems:
        return "Brouillon refusé : " + " ; ".join(problems), None
    try:
        return None, f.artifacts()
    except framing.FramingError as exc:
        return str(exc), None


def resume(parent: Misc, controller: Controller, on_draft: Callable[[str], None]) -> str | None:
    """Revenir au cadrage après le brouillon : même session, nouveau groupe (test 45)."""
    f = controller.framing
    if f is None or f.draft is None:
        return "Aucun brouillon de cadrage à reprendre."
    text = (dialogs.prompt_text(parent, "Reprendre le cadrage", "Ce qu'il faut encore cadrer")
            or "").strip()
    if text:
        FramingDialog(parent, controller, ("Vous", text),
                      lambda: f.reopen(text, correction=False), on_draft)
    return None


class FramingDialog(Toplevel):
    """§4.2 : transcription, réponse, Envoyer, Clore maintenant, Annuler — plus les
    choix d'une proposition (continuer, corriger un point, rédiger) et la relance
    explicite d'un incident. Contrôles désactivés pendant chaque tour (test 68)."""

    def __init__(
        self, parent: Misc, controller: Controller, opening: tuple[str, str],
        first: Callable[[], Turn], on_draft: Callable[[str], None],
    ) -> None:
        super().__init__(parent.winfo_toplevel())
        assert controller.framing is not None
        self._controller, self._f, self._on_draft = controller, controller.framing, on_draft
        self._turn: Turn | None = None
        self._cancelling = False
        self.title("Cadrage avec un agent")
        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._transcript = ScrolledText(self, width=80, height=18, wrap="word", state="disabled")
        self._transcript.pack(fill="both", expand=True, padx=16, pady=(16, 4))
        self._status = ttk.Label(self, wraplength=560, justify="left")
        self._status.pack(anchor="w", padx=16)
        self._reply = ScrolledText(self, width=80, height=5, wrap="word")
        self._reply.pack(fill="x", padx=16, pady=4)
        row = ttk.Frame(self, padding=(16, 0, 16, 16))
        row.pack(fill="x")
        self._buttons = {
            name: ttk.Button(row, text=name, command=command) for name, command in (
                ("Envoyer", self._send), ("Corriger un point", self._correct),
                ("Clore maintenant", self._close), ("Relancer", self._retry),
            )
        }
        for button in self._buttons.values():
            button.pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Annuler", command=self._cancel).pack(side="right")
        self._append(*opening)
        self.grab_set()
        self._run(first)

    # -- Un tour à la fois, dans le fil moteur du contrôleur --

    def _run(self, step: Callable[[], Turn]) -> None:
        if not self._controller.framing_step(step):
            self._status.configure(text="Le fil moteur est occupé : réessayez après.")
            return
        self._enable(None, busy=True)
        self._status.configure(text=_BUSY)
        self.after(_POLL_MS, self._poll)

    def _poll(self) -> None:
        if self._controller.has_active_run():
            self.after(_POLL_MS, self._poll)
            return
        outcome = self._controller.take_framing_outcome()
        if self._cancelling:
            self._controller.discard_framing()
            self.destroy()
            return
        if isinstance(outcome, Turn):
            self._show(outcome)
        else:
            self._turn = None
            self._append("Incident", str(outcome))
            self._enable(None)

    def _show(self, turn: Turn) -> None:
        self._turn = turn
        kind = self._kind()
        if kind == DRAFT and self._f.draft is not None:
            self.destroy()
            self._on_draft(self._f.draft)
            return
        self._append("F", framing.shown(turn))
        self._enable(kind)

    def _kind(self) -> str | None:
        turn = self._turn
        return None if turn is None or turn.problem or turn.reply is None else turn.reply.kind

    def _enable(self, kind: str | None, *, busy: bool = False) -> None:
        """Pendant un tour, tout est désactivé sauf Annuler."""
        idle, open_ = not busy, not self._f.session.closed
        allowed = {
            "Envoyer": idle and kind in (QUESTION, READY),
            "Corriger un point": idle and kind == READY,
            "Clore maintenant": idle and open_,
            "Relancer": idle and open_ and kind is None and self._turn is not None,
        }
        for name, button in self._buttons.items():
            button.state(["!disabled"] if allowed[name] else ["disabled"])
        self._buttons["Envoyer"].configure(text="Continuer" if kind == READY else "Envoyer")
        self._buttons["Clore maintenant"].configure(
            text="Rédiger le brouillon" if kind == READY else "Clore maintenant"
        )
        if idle:
            self._status.configure(text="" if open_ else "Session fermée : annulez le cadrage.")

    # -- Actions humaines --

    def _send(self, *, correction: bool = False) -> None:
        text = self._reply.get("1.0", "end-1c").strip()
        if not text:
            self._status.configure(text="La réponse est vide.")
            return
        self._reply.delete("1.0", "end")
        self._append("Vous", text)
        if self._kind() == QUESTION:
            self._run(lambda: self._f.answer(text))
        else:
            self._run(lambda: self._f.reopen(text, correction=correction))

    def _correct(self) -> None:
        self._send(correction=True)

    def _close(self) -> None:
        if self._kind() == READY:
            self._f.note("Décision", "proposition de clôture acceptée")
        elif dialogs.confirm(
            self, "Clore le cadrage ?", "F rédigera la demande dans la même session : un appel.",
            ok_label="Clore et rédiger",
        ):
            self._f.note("Décision", "clôture demandée par l'utilisateur")
        else:
            return
        self._run(self._f.write_draft)

    def _retry(self) -> None:
        self._run(self._f.retry)

    def _cancel(self) -> None:
        """Fermer la modale = demander l'annulation, confirmée (§4.2). Un tour en cours
        est interrompu ; le dossier jetable disparaît quand le fil s'est arrêté."""
        busy = self._controller.has_active_run()
        body = "Rien ne sera créé." + (
            " L'appel en cours sera interrompu : il a pu être payé." if busy else ""
        )
        if not dialogs.confirm(self, "Annuler le cadrage ?", body, ok_label="Annuler le cadrage",
                               cancel_label="Continuer le cadrage"):
            return
        if busy:
            self._cancelling = True
            self._controller.interrupt_active_run()
            return
        self._controller.discard_framing()
        self.destroy()

    def _append(self, who: str, text: str) -> None:
        self._transcript.configure(state="normal")
        self._transcript.insert("end", f"{who}\n{text.strip()}\n\n")
        self._transcript.configure(state="disabled")
        self._transcript.see("end")
