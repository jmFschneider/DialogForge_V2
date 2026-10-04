"""Contrôleur GUI (`conception/GUI_V1.md` §10.4) : navigation dans une seule
fenêtre, préférences non métier, **au plus un fil moteur** (§3.1 : une
collaboration et une exécution au maximum). Il ne construit ni `etat.json`,
ni incident, ni décision — seule la façade lit et écrit le dossier ; le
contrôleur ne fait que lancer `workflow.run` dans un fil et se souvenir,
le temps d'un rafraîchissement, si ce fil a échoué avant tout appel.

Il possède aussi la session de l'agent de cadrage F entre deux tours
(`conception/CADRAGE_AGENT.md` §4.3) : chaque tour passe par le **même** fil,
jamais en même temps qu'une exécution A/B.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from tkinter import Tk, messagebox, ttk

from .. import facade, framing, mission, workflow
from ..adapters.base import AgentAdapter, FramingSessionSpec
from ..models import MissionKind
from ..registry import ADAPTERS
from ..transport import ExecutionControl
from . import recents
from .runner_session import RunnerRequest, RunnerSession


class Controller:
    def __init__(self, root: Tk, *, recents_path: Path = recents.DEFAULT_PATH) -> None:
        self.root = root
        self.recents_path = recents_path
        self._frame: ttk.Frame | None = None
        self._run_path: Path | None = None
        self._run_thread: threading.Thread | None = None
        self._run_control: ExecutionControl | None = None
        self._run_error: str | None = None
        self._runner_session: RunnerSession | None = None
        self.runner_token = ""  # en mémoire seulement : jamais écrit, oublié à la fermeture
        self.framing: framing.Framing | None = None
        self._framing_control: ExecutionControl | None = None
        self._framing_outcome: framing.Turn | Exception | None = None

    # -- Navigation : les vues remplacent le contenu de la même fenêtre (§4) --

    def _swap(self, build: Callable[[], ttk.Frame]) -> None:
        # Quitter l'écran de création termine le cadrage : la session ne lui survit pas.
        self.discard_framing()
        if self._frame is not None:
            self._frame.destroy()
        self._frame = build()
        self._frame.pack(fill="both", expand=True)

    def show_accueil(self) -> None:
        from .views.accueil import AccueilView

        self._swap(lambda: AccueilView(self.root, self))

    def show_suivi(self, path: Path) -> None:
        from .views.suivi import SuiviView

        self._swap(lambda: SuiviView(self.root, self, path))

    def show_creation(
        self, *, from_research: Path | None = None, new_version: bool = False,
    ) -> None:
        from .views.creation import CreationView

        self._swap(lambda: CreationView(
            self.root, self, from_research=from_research, new_version=new_version,
        ))

    def show_runner(self, path: Path) -> None:
        from .views.runner import RunnerView

        self._swap(lambda: RunnerView(self.root, self, path))

    def collaborations_root(self) -> Path | None:
        return recents.load_root(self.recents_path)

    def set_collaborations_root(self, path: Path) -> None:
        try:
            recents.save_root(path, self.recents_path)
        except OSError as exc:
            messagebox.showerror("Répertoire non mémorisé", str(exc))
            return
        self.show_accueil()

    def record_created(self, path: Path) -> None:
        if self.collaborations_root() is None:
            try:
                recents.save_root(path.parent, self.recents_path)
            except OSError:
                pass  # Une préférence inaccessible ne doit pas annuler la création.
        try:
            target = mission.resolve(path)
        except mission.MissionError:
            target = mission.Target(None, None, path)
        recents.record_opened(target.root or path, self.recents_path, last_step=target.step)

    # -- Ouverture, strictement en lecture (§5.1, AC-02) --

    def open_collaboration(self, path: Path, step: str | None = None) -> None:
        """Un dossier de mission ouvre son étape préférée (la dernière consultée) ; la mission
        et ses étapes se naviguent depuis l'écran de suivi. Une collaboration indépendante
        s'ouvre telle quelle."""
        try:
            remembered = next((r.last_step for r in recents.load(self.recents_path)
                               if r.path == path.resolve()), None)
            target = mission.resolve(path, step or remembered, opening=step is None)
            self.inspect(target.collab)
        except (facade.InspectionError, mission.MissionError) as exc:
            messagebox.showerror("Dossier introuvable ou invalide", str(exc))
            return
        recents.record_opened(target.root or path, self.recents_path, last_step=target.step)
        self.show_suivi(target.collab)

    def inspect(
        self, path: Path, *, owned_by_this_gui: bool = False,
    ) -> facade.CollaborationSnapshot:
        return facade.inspect_collaboration(path, owned_by_this_gui=owned_by_this_gui)

    def recent_entries(self) -> tuple[recents.Recent, ...]:
        entries: dict[Path, recents.Recent] = {}
        for entry in recents.load(self.recents_path):  # une entrée par mission
            (top,) = mission.fold([entry.path])
            entries.setdefault(top, replace(entry, path=top))
        root = self.collaborations_root()
        if root is not None and root.is_dir():
            try:
                for folder in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
                    if folder.is_dir() and folder.resolve() not in entries and (
                        (folder / "etat.json").is_file() or (folder / mission.REGISTRY).is_file()
                    ):
                        entries[folder.resolve()] = recents.Recent(folder.resolve(), "")
            except OSError:
                pass
        return tuple(entries.values())

    # -- Exécution : un fil au plus (§3.1, §10.4) --

    def is_running(self, path: Path) -> bool:
        return (
            self._run_path == path
            and self._run_thread is not None
            and self._run_thread.is_alive()
        )

    def run_error(self, path: Path) -> str | None:
        """Ce que le fil a rapporté s'il s'est arrêté **avant tout appel**
        (adaptateur absent, effort refusé…) — jamais un incident de cycle, que
        `etat.json` porte déjà et que la façade lit normalement."""
        if self._run_path != path or self.is_running(path):
            return None
        return self._run_error

    def start_run(
        self, path: Path, *, timeout_seconds: float,
        intervention: workflow.Intervention | None = None,
    ) -> None:
        """Lance le cycle dans son propre fil (§9.1, comme `tests/test_control.py`
        le fait déjà côté tests). Sans effet si le fil moteur est occupé, par
        une exécution ou un tour de F — jamais une seconde reprise concurrente
        (§8.2), jamais A pendant F (`CADRAGE_AGENT.md` §4.4).

        `intervention` transmet une réponse, une correction, une relance ou un
        retraitement (§8.3-8.6) — le moteur l'applique sous le verrou, comme
        `resume`/`decide --correct` en CLI ; ce fil ne fait qu'appeler
        `workflow.run`, exactement comme pour « créer et démarrer »."""
        if self.has_active_run():
            return
        self._runner_session = None
        control = ExecutionControl()
        self._run_error = None

        def worker() -> None:
            try:
                workflow.run(
                    path, adapters=ADAPTERS, timeout_seconds=timeout_seconds,
                    intervention=intervention, control=control,
                )
            except workflow.Stopped:
                pass  # rien n'est parti (§9.1) : rien à signaler comme échec
            except Exception as exc:
                self._run_error = str(exc)

        thread = threading.Thread(target=worker, daemon=True)
        self._run_path, self._run_thread, self._run_control = path, thread, control
        thread.start()

    def has_active_run(self) -> bool:
        return self._run_thread is not None and self._run_thread.is_alive()

    def has_active_runner(self) -> bool:
        return self._runner_session is not None and self.has_active_run()

    def interrupt_active_run(self) -> None:
        """§9.3, branche « Interrompre maintenant » : l'appel en cours a pu être
        payé — c'est le transport, pas ce contrôleur, qui termine l'arbre."""
        if self._runner_session is not None and self.has_active_run():
            self._runner_session.signal("interrupt")
        elif self._run_control is not None:
            self._run_control.interrupt_requested.set()

    # -- Cadrage avec agent F : la session et ses tours (`CADRAGE_AGENT.md` §4.2, §4.3) --

    def open_framing(
        self, adapter: AgentAdapter, spec: FramingSessionSpec, root: Path, idea: str,
        kind: MissionKind | None = None, complement: bool = False,
    ) -> framing.Framing:
        """Le contrôleur possède la session entre deux tours : une seule à la fois,
        jamais une collaboration tant que la création n'a pas eu lieu. Ouvrir ne coûte
        aucun appel ; les tours passent par `framing_step`."""
        self.discard_framing()
        others = [a.env for key, a in ADAPTERS.items() if key != adapter.adapter_id]
        self._framing_control = ExecutionControl()
        session = framing.open_session(
            adapter, spec, others=others, control=self._framing_control,
        )
        self.framing = framing.Framing(session, root, idea, kind=kind, complement=complement)
        return self.framing

    def framing_step(self, step: Callable[[], framing.Turn]) -> bool:
        """Un tour de F dans **l'unique** fil moteur — refusé (`False`) s'il est occupé,
        par une exécution A/B ou par un autre tour. Le fil Tk n'appelle jamais
        l'adaptateur : il sonde `has_active_run()` par `after()`, puis lit le résultat
        par `take_framing_outcome()`."""
        if self.has_active_run():
            return False
        self._runner_session = None
        self._framing_outcome = None

        def worker() -> None:
            try:
                self._framing_outcome = step()
            except Exception as exc:  # session fermée, adaptateur disparu : à afficher
                self._framing_outcome = exc

        thread = threading.Thread(target=worker, daemon=True)
        self._run_path, self._run_thread = None, thread
        self._run_control = self._framing_control
        thread.start()
        return True

    def take_framing_outcome(self) -> framing.Turn | Exception | None:
        outcome, self._framing_outcome = self._framing_outcome, None
        return outcome

    def discard_framing(self) -> None:
        """Annulation, départ de l'écran de création, création réussie ou fermeture de
        la fenêtre : la session se ferme, le dossier jetable disparaît (§3.2). Un tour
        en cours est interrompu d'abord — il a pu être payé."""
        if self.framing is None:
            return
        if self.has_active_run() and self._run_control is self._framing_control:
            self.interrupt_active_run()
        self.framing.discard()
        self.framing = None

    def pause_active_run(self) -> None:
        """§9.3, branche « Terminer l'appel courant, mettre en pause, puis
        fermer » : rien n'est perdu, le moteur s'arrête à la frontière d'appel
        (READY) — à l'appelant d'attendre `has_active_run()` avant de fermer."""
        if self._runner_session is not None and self.has_active_run():
            self._runner_session.signal("pause")
        elif self._run_control is not None:
            self._run_control.pause_requested.set()

    def start_runner(self, request: RunnerRequest) -> RunnerSession | None:
        """Même limite d'un seul fil actif que le cycle A/B et le cadrage."""
        if self.has_active_run():
            return None
        session = RunnerSession(request)
        self._runner_session = session
        self._run_path, self._run_thread, self._run_control = (
            request.collaboration, session.thread, None,
        )
        session.start()
        return session
