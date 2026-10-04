"""Passage Windows GUI → Runner Linux ; protocole JSON sur stdin/stdout.

Une requête, une action : `check` (prérequis, sans rien écrire), `prepare` (clone isolé),
`launch` (premier appel de l'agent), `continue` (appel suivant, explicite), `collect` (validations
et paquet, sans agent) et `inspect` (état du dossier, en lecture). Seuls `launch` et `continue`
reçoivent le jeton, qui ne passe jamais par un argument ni par un fichier.
"""

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

PROFILE = "claude-wsl"


def _event(kind: str, **details: Any) -> None:
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


def _identity(value: Any) -> tuple[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2 or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError("identité Git invalide")
    return value[0], value[1]


def main() -> int:
    try:
        request = json.loads(sys.stdin.readline())
        if not isinstance(request, dict):
            raise ValueError("requête Runner invalide")
        action = request["action"]
        run = Path(str(request["run"])).expanduser()
        control = ExecutionControl()
        threading.Thread(target=_control_lines, args=(control,), daemon=True).start()
        distro = os.environ.get("WSL_DISTRO_NAME")
        if action in {"launch", "continue", "correct", "collect"} and (
            control.interrupt_requested.is_set() or control.pause_requested.is_set()
        ):
            raise ValueError("lancement arrêté avant l'appel agent")
        if action == "inspect":
            _event("state", distro=distro, **core.inspect_run(run))
        elif action == "bundle":
            bundle = core.bundle_candidate(
                run, Path(str(request["package"])), str(request["package_id"]),
            )
            _event("bundle", path=str(bundle), distro=distro)
        elif action == "check":
            core.preflight(run, _commands(request["validations"]), PROFILE)
            _event("checked", distro=distro)
        elif action == "prepare":
            validations = _commands(request["validations"])
            core.preflight(run, validations, PROFILE)
            identity = _identity(request.get("identity"))
            if identity is None and core.git_identity() is None:
                raise ValueError("identité Git absente : l'agent ne pourrait pas committer")
            oid = core.prepare(
                _linux_path(str(request["export"])), _linux_path(str(request["repo"])),
                str(request["base"]), run, validations=validations,
                validation_timeout=float(request["validation_timeout"]),
                profile=PROFILE, identity=identity,
            )
            _event("prepared", run=str(run), base_oid=oid, distro=distro)
            if control.interrupt_requested.is_set() or control.pause_requested.is_set():
                raise ValueError("clone préparé ; lancement arrêté avant l'appel agent")
        elif action == "collect":
            _event("completed", package=str(core.collect(run, control=control)))
        elif action in {"launch", "continue", "correct"}:
            token = str(request["token"])
            if not token:
                raise ValueError("jeton Claude absent")
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token
            request["token"] = ""
            package = core.run_claude(
                run, timeout_seconds=float(request["timeout"]),
                continue_existing=action != "launch", correction=str(request.get("correction", "")),
                control=control,
            )
            _event("completed", package=str(package))
        else:
            raise ValueError("action Runner inconnue")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        _event("error", message=str(exc),
               code="validation_failed" if isinstance(exc, core.ValidationFailed) else "error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
