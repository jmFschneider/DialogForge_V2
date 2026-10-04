"""Pont de test : le vrai protocole de `gui_bridge`, en profil local et avec un faux agent.

Lancé comme sous-processus par la session GUI (`_bridge_command` remplacé). Les chemins sont déjà
natifs, la validation ne passe pas par `srt`, et l'agent est le script de `RUNNER_TEST_AGENT`.
Le jeton arrive, comme en production, par l'entrée standard seulement.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dialogforge_runner import core, gui_bridge
from iabinome import transport


def _run_claude(
    run: Path, *, timeout_seconds: float, continue_existing: bool = False,
    correction: str = "",
    control: transport.ExecutionControl | None = None,
) -> Path:
    assert os.environ["CLAUDE_CODE_OAUTH_TOKEN"], "le pont doit avoir reçu le jeton"
    return core.run_agent(
        run, [sys.executable, os.environ["RUNNER_TEST_AGENT"]], timeout_seconds=timeout_seconds,
        continue_existing=continue_existing, correction=correction, control=control,
    )


def _detached_stdin(run: Callable[..., Any]) -> Callable[..., Any]:
    """Sous Windows, un enfant qui hérite du tube d'entrée pendant que le fil de contrôle y lit
    se bloque (E/S synchrone sur le même tube). Sous Linux, le pont n'a pas ce défaut."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("stdin", subprocess.DEVNULL)
        return run(*args, **kwargs)
    return wrapper


if __name__ == "__main__":
    subprocess.run = _detached_stdin(subprocess.run)
    gui_bridge.PROFILE = "local"
    gui_bridge._linux_path = Path
    setattr(core, "run_claude", _run_claude)  # noqa: B010
    raise SystemExit(gui_bridge.main())
