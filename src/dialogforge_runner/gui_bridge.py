"""Passage Windows GUI → Runner Linux ; protocole JSON sur stdin/stdout."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

# Exécutable par son chemin depuis le paquet Windows, sans installation WSL séparée.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dialogforge_runner import core  # noqa: E402
from iabinome.transport import ExecutionControl  # noqa: E402


def _event(kind: str, **details: str) -> None:
    print(json.dumps({"event": kind, **details}, ensure_ascii=False), flush=True)


def _linux_path(value: str) -> Path:
    if os.name != "posix":
        raise ValueError("le pont Runner exige Linux")
    if value.startswith("/"):
        return Path(value).expanduser()
    result = subprocess.run(
        ["wslpath", "-u", value], capture_output=True, text=True, check=True, timeout=15,
    )
    return Path(result.stdout.strip())


def _commands(value: Any) -> list[list[str]]:
    if not isinstance(value, list) or not value or not all(
        isinstance(command, list) and command
        and all(isinstance(arg, str) and arg for arg in command)
        for command in value
    ):
        raise ValueError("validations : liste non vide de commandes complètes attendue")
    return value


def _control_lines(control: ExecutionControl) -> None:
    for line in sys.stdin:
        if line.strip() == "interrupt":
            control.interrupt_requested.set()
        elif line.strip() == "pause":
            control.pause_requested.set()


def main() -> int:
    try:
        request = json.loads(sys.stdin.readline())
        if not isinstance(request, dict):
            raise ValueError("requête Runner invalide")
        action = request["action"]
        run = Path(str(request["run"])).expanduser()
        control = ExecutionControl()
        threading.Thread(target=_control_lines, args=(control,), daemon=True).start()
        if action == "start":
            export = _linux_path(str(request["export"]))
            repo = _linux_path(str(request["repo"]))
            core.prepare(
                export, repo, str(request["base"]), run,
                validations=_commands(request["validations"]),
                validation_timeout=float(request["validation_timeout"]),
                profile="claude-wsl",
            )
            _event("prepared", run=str(run))
        elif action not in {"continue", "collect"}:
            raise ValueError("action Runner inconnue")
        if control.interrupt_requested.is_set() or control.pause_requested.is_set():
            raise ValueError("lancement arrêté avant l'appel agent")
        if action == "collect":
            package = core.collect(run, control=control)
        else:
            token = str(request["token"])
            if not token:
                raise ValueError("jeton Claude absent")
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token
            request["token"] = ""
            package = core.run_claude(
                run, timeout_seconds=float(request["timeout"]),
                continue_existing=action == "continue", control=control,
            )
        _event("completed", package=str(package))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        _event("error", message=str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
