"""Contrôleur GUI (`conception/GUI_V1.md` §10.4) : navigation dans une seule
fenêtre, préférences non métier, **au plus un fil moteur** (§3.1 : une
collaboration et une exécution au maximum). Il ne construit ni `etat.json`,
ni incident, ni décision — seule la façade lit et écrit le dossier ; le
contrôleur ne fait que lancer `workflow.run` dans un fil et se souvenir,
le temps d'un rafraîchissement, si ce fil a échoué avant tout appel.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import Tk, messagebox, ttk

from .. import facade, workflow
from ..registry import ADAPTERS
from ..transport import ExecutionControl
from . import recents


class Controller:
    def __init__(self, root: Tk, *, recents_path: Path = recents.DEFAULT_PATH) -> None:
        self.root = root
        self.recents_path = recents_path
        self._frame: ttk.Frame | None = None
        self._run_path: Path | None = None
        self._run_thread: threading.Thread | None = None
        self._run_control: ExecutionControl | None = None
        self._run_error: str | None = None

    # -- Navigation : les vues remplacent le contenu de la même fenêtre (§4) --

    def _swap(self, build: Callable[[], ttk.Frame]) -> None:
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

    def show_creation(self) -> None:
        from .views.creation import CreationView

        self._swap(lambda: CreationView(self.root, self))

    # -- Ouverture, strictement en lecture (§5.1, AC-02) --

    def open_collaboration(self, path: Path) -> None:
        try:
            self.inspect(path)
        except facade.InspectionError as exc:
            messagebox.showerror("Dossier introuvable ou invalide", str(exc))
            return
        recents.record_opened(path, self.recents_path)
        self.show_suivi(path)

    def inspect(
        self, path: Path, *, owned_by_this_gui: bool = False,
    ) -> facade.CollaborationSnapshot:
        return facade.inspect_collaboration(path, owned_by_this_gui=owned_by_this_gui)

    def recent_entries(self) -> tuple[recents.Recent, ...]:
        return recents.load(self.recents_path)

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
        le fait déjà côté tests). Sans effet si une exécution est déjà active
        sur ce dossier — jamais une seconde reprise concurrente (§8.2).

        `intervention` transmet une réponse, une correction, une relance ou un
        retraitement (§8.3-8.6) — le moteur l'applique sous le verrou, comme
        `resume`/`decide --correct` en CLI ; ce fil ne fait qu'appeler
        `workflow.run`, exactement comme pour « créer et démarrer »."""
        if self.is_running(path):
            return
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

    def interrupt_active_run(self) -> None:
        """§9.3, branche « Interrompre maintenant » : l'appel en cours a pu être
        payé — c'est le transport, pas ce contrôleur, qui termine l'arbre."""
        if self._run_control is not None:
            self._run_control.interrupt_requested.set()

    def pause_active_run(self) -> None:
        """§9.3, branche « Terminer l'appel courant, mettre en pause, puis
        fermer » : rien n'est perdu, le moteur s'arrête à la frontière d'appel
        (READY) — à l'appelant d'attendre `has_active_run()` avant de fermer."""
        if self._run_control is not None:
            self._run_control.pause_requested.set()
