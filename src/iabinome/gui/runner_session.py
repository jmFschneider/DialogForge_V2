"""Exécution du Runner depuis Tk, sans bloquer le fil de la fenêtre."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import development, facade


@dataclass
class RunnerRequest:
    action: str
    collaboration: Path
    export: Path
    repo: Path
    base: str
    validations: list[list[str]]
    run: str
    token: str
    timeout: float
    validation_timeout: float


def _bridge_command() -> list[str]:
    script = Path(__file__).resolve().parents[2] / "dialogforge_runner" / "gui_bridge.py"
    if os.name != "nt":
        return [sys.executable, str(script)]
    wsl = shutil.which("wsl")
    if wsl is None:
        raise ValueError("WSL introuvable ; installer Ubuntu WSL2")
    result = subprocess.run(
        [wsl, "--exec", "wslpath", "-u", str(script)],
        capture_output=True, text=True, check=True, timeout=15,
    )
    return [wsl, "--exec", "python3", result.stdout.strip()]


class RunnerSession:
    def __init__(self, request: RunnerRequest) -> None:
        self.request = request
        self.stage = "En attente"
        self.run_path = request.run
        self.package: str | None = None
        self.error: str | None = None
        self._process: subprocess.Popen[str] | None = None
        self._pending: str | None = None
        self._guard = threading.Lock()
        self.thread = threading.Thread(target=self._work, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def signal(self, action: str) -> None:
        with self._guard:
            if self._process is None or self._process.stdin is None:
                self._pending = action
                return
            try:
                self._process.stdin.write(action + "\n")
                self._process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def _work(self) -> None:
        try:
            if self.request.action == "start":
                snapshot = facade.inspect_collaboration(self.request.collaboration)
                if not snapshot.presentation.can_start_runner:
                    raise ValueError(
                        "seule une conception acceptée sur sa version actuelle peut partir"
                    )
                self.stage = "Export de la conception"
                development.export_conception(self.request.collaboration, self.request.export)
            self.stage = "Préparation dans Ubuntu" if self.request.action == "start" else (
                "Collecte" if self.request.action == "collect" else "Continuation"
            )
            command = _bridge_command()
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=flags,
            )
            assert process.stdin is not None and process.stdout is not None
            payload: dict[str, Any] = {
                "action": self.request.action, "run": self.request.run,
                "export": str(self.request.export), "repo": str(self.request.repo),
                "base": self.request.base, "validations": self.request.validations,
                "timeout": self.request.timeout,
                "validation_timeout": self.request.validation_timeout,
                "token": self.request.token,
            }
            process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            process.stdin.flush()
            payload["token"] = ""
            self.request.token = ""
            with self._guard:
                self._process = process
                pending = self._pending
                self._pending = None
            if pending:
                self.signal(pending)
            diagnostic = ""
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    diagnostic = line.strip()
                    continue
                if event.get("event") == "prepared":
                    self.run_path = str(event["run"])
                    self.stage = "Agent Claude au travail"
                elif event.get("event") == "completed":
                    self.package = str(event["package"])
                    self.stage = "Paquet prêt"
                elif event.get("event") == "error":
                    self.error = str(event["message"])
            code = process.wait()
            if code and self.error is None:
                self.error = diagnostic or "Le pont WSL s'est arrêté ; voir le dossier d'exécution."
            if not code and self.package is None and self.error is None:
                self.error = "Le pont WSL n'a pas rendu de paquet."
            if self.error is not None:
                self.stage = "Arrêté"
        except (OSError, ValueError, subprocess.SubprocessError, facade.InspectionError) as exc:
            self.error = str(exc)
            self.stage = "Arrêté"
        finally:
            self.request.token = ""
