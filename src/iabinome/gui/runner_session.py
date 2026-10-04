"""Exécution du Runner depuis Tk, sans bloquer le fil de la fenêtre.

Une session mène une action : `start` (prérequis, export, référence, dépôt initial d'un projet
neuf, clone, puis premier appel), `launch` (premier appel sur un clone préparé), `continue`
(appel suivant, explicite), `collect` (sans agent) ou `inspect` (lecture du dossier Linux).
Rien ne relance un agent de soi-même ; le jeton ne part que par l'entrée standard du pont.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dialogforge_runner import core

from .. import executions, facade

_STAGES = {
    "launch": "Agent Claude au travail", "continue": "Continuation",
    "correct": "Correction demandée", "collect": "Collecte",
    "inspect": "Lecture du dossier Runner",
}
MAX_AGENT_CALLS = 3


@dataclass
class RunnerRequest:
    action: str
    collaboration: Path
    found: executions.Found
    mode: str
    repo: Path
    base: str
    validations: list[list[str]]
    run: str
    token: str
    timeout: float
    validation_timeout: float
    distro: str | None = None
    correction: str = ""
    max_calls: int = MAX_AGENT_CALLS


def _bridge_command(distro: str | None = None) -> list[str]:
    script = Path(__file__).resolve().parents[2] / "dialogforge_runner" / "gui_bridge.py"
    if os.name != "nt":
        return [sys.executable, str(script)]
    wsl = shutil.which("wsl")
    if wsl is None:
        raise ValueError("WSL introuvable ; installer Ubuntu WSL2")
    launcher = [wsl, "-d", distro] if distro else [wsl]
    result = subprocess.run(
        [*launcher, "--exec", "wslpath", "-u", str(script)],
        capture_output=True, text=True, check=True, timeout=15,
    )
    return [*launcher, "--exec", "python3", result.stdout.strip()]


class RunnerSession:
    def __init__(self, request: RunnerRequest) -> None:
        self.request = request
        self.stage = "En attente"
        self.run_path = request.run
        self.distro = request.distro
        self.reference = request.found.reference
        self.package: str | None = None
        self.state: dict[str, Any] | None = None
        self.error: str | None = None
        self.error_code: str | None = None
        self._process: subprocess.Popen[str] | None = None
        self._requested: list[str] = []
        self._guard = threading.Lock()
        self.thread = threading.Thread(target=self._work, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def signal(self, action: str) -> None:
        with self._guard:
            self._requested.append(action)
            if self._process is not None:
                self._write(self._process, action)

    @staticmethod
    def _write(process: subprocess.Popen[str], action: str) -> None:
        try:
            assert process.stdin is not None
            process.stdin.write(action + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _work(self) -> None:
        request = self.request
        try:
            if request.action == "start":
                self._prepare()
                if self._requested:
                    raise ValueError("clone préparé ; lancement arrêté avant l'appel agent")
                self._guard_current()
                self._run_calls("launch")
            else:
                if request.action in {"launch", "continue", "correct"}:
                    self._guard_current()
                    self._run_calls(request.action)
                else:
                    self._bridge(request.action)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            self.error = str(exc)
        finally:
            request.token = ""
        if self.error is not None:
            self.stage = "Arrêté"
        elif self.package:
            self.stage = "Paquet prêt"

    def _run_calls(self, action: str) -> None:
        """Une seule autorisation couvre au plus trois appels, uniquement si les tests échouent."""
        deadline = time.monotonic() + self.request.timeout
        if not 1 <= self.request.max_calls <= MAX_AGENT_CALLS:
            raise ValueError("nombre d'appels agent hors limites")
        for attempt in range(self.request.max_calls):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("durée totale des appels agent atteinte")
            self.error = self.error_code = None
            try:
                self._bridge(action, timeout=remaining)
                return  # paquet réussi : aucune continuation automatique
            except ValueError:
                if (self.error_code != "validation_failed" or attempt + 1 == self.request.max_calls
                        or self._requested):
                    raise
                self.stage = (f"Validation échouée ; correction {attempt + 1}/"
                              f"{self.request.max_calls - 1}")
                self._guard_current()
                action = "continue"

    def _guard_current(self) -> None:
        if self.reference is not None:
            executions.check_current(self.request.collaboration, self.reference)

    def _prepare(self) -> None:
        request = self.request
        if not facade.inspect_collaboration(request.collaboration).presentation.can_start_runner:
            raise ValueError("seule une conception acceptée sur sa version actuelle peut partir")
        found, new = request.found, request.mode == "nouveau"
        recorded = found.data["projet"] if found.data and new else None
        initial = recorded["base_oid"] if recorded and recorded["mode"] == "nouveau" else None
        self.stage = "Vérification des prérequis"
        if new and initial:
            core.reuse_initial_base(request.repo, initial, str(recorded and recorded["identite"]))
        elif new:
            core.check_new_project(request.repo)
        if new:
            self._bridge("check")
        self.stage = "Export de la conception"
        export = executions.ensure_export(request.collaboration, found)
        self.reference = executions.save(
            found, export, mode=request.mode, repo=request.repo, base=request.base,
            validations=request.validations, run=request.run,
            agent_timeout=request.timeout, validation_timeout=request.validation_timeout,
        )
        executions.update(self.reference, wsl={"distribution": self.distro})
        base = request.base
        if new:
            if not initial:
                self.stage = "Création du dépôt initial"
                initial, author = core.init_project(request.repo)
                executions.update(self.reference, projet={"base_oid": initial, "identite": author})
            base = initial
        self.stage = "Préparation dans Ubuntu"
        self._bridge("prepare", export=str(export), base=base)

    def _payload(self, action: str, extra: dict[str, Any]) -> dict[str, Any]:
        request = self.request
        payload: dict[str, Any] = {
            "action": action, "run": self.run_path, "repo": str(request.repo),
            "validations": request.validations, "timeout": request.timeout,
            "validation_timeout": request.validation_timeout,
            "identity": core.git_identity(request.repo) if action == "prepare" else None,
            "token": "", **extra,
        }
        if action in {"launch", "continue", "correct"}:
            payload["token"] = request.token
            if request.correction:
                payload["correction"] = request.correction
        return payload

    def _bridge(self, action: str, **extra: Any) -> None:
        if action in _STAGES:
            self.stage = _STAGES[action]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        process = subprocess.Popen(
            _bridge_command(self.distro), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            bufsize=1, creationflags=flags,
        )
        assert process.stdin is not None and process.stdout is not None
        payload = self._payload(action, extra)
        process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        process.stdin.flush()
        payload["token"] = ""
        with self._guard:
            self._process = process
            for pending in self._requested:
                self._write(process, pending)
        diagnostic, failure = "", None
        for line in process.stdout:
            try:
                event = json.loads(line)
                self._event(event)
            except json.JSONDecodeError:
                diagnostic = line.strip()
            except (OSError, ValueError) as exc:  # référence illisible : lire jusqu'au bout
                failure = failure or exc
        code = process.wait()
        with self._guard:
            self._process = None
        if failure is not None:
            raise failure
        if self.error is not None:
            raise ValueError(self.error)
        if code:
            raise ValueError(diagnostic or "Le pont WSL s'est arrêté ; voir le dossier Runner.")

    def _event(self, event: dict[str, Any]) -> None:
        kind = event.get("event")
        self.distro = event.get("distro") or self.distro
        if kind == "prepared":
            self.run_path = str(event["run"])
            if self.reference is not None:
                executions.update(
                    self.reference, run=self.run_path, wsl={"distribution": self.distro},
                    projet={"base_oid": str(event["base_oid"])},
                )
        elif kind == "completed":
            self.package = str(event["package"])
            if self.reference is not None:
                executions.update(self.reference, paquets=[self.package])
        elif kind == "state":
            self.state = event
        elif kind == "error":
            self.error = str(event["message"])
            self.error_code = str(event.get("code", "error"))
