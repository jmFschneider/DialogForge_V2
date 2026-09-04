"""Adaptateur Claude Code — outil-1.

Formes mesurées le 2026-09-03 (`conception/CARACTERISATION_CLI.md`), jamais une
attestation durable : le prévol resonde présence et version à chaque `run`
(CONCEPTION_FINALE.md §8). `--tools ""` désactive tous les outils — documenté
dans `--help` — et sert le profil `CONTEXT_ONLY` de B (point 2 du relevé).
"""

from __future__ import annotations

import shutil

from ..models import ReviewerAccess, Role
from .base import CallSpec, Capabilities, ObservedCli, probe_version

_EXECUTABLE = "claude"
_DEFAULT_MODEL = {Role.A: "opus", Role.B: "fable"}


class ClaudeAdapter:
    adapter_id = "claude"
    capabilities = Capabilities(supports_context_only=True, supports_model_override=True)

    def default_model(self, role: Role) -> str:
        """Opus pour A, Fable pour B (CLAUDE.md §6) — reste surchargeable :
        mesuré le 2026-09-03, ce compte n'a pas les crédits pour Fable."""
        return _DEFAULT_MODEL[role]

    def probe(self) -> ObservedCli:
        exe = shutil.which(_EXECUTABLE)
        if exe is None:
            return ObservedCli(present=False, version="")
        return ObservedCli(present=True, version=probe_version(exe))

    def command(self, call: CallSpec) -> list[str]:
        exe = _resolve()
        cmd = [exe, "-p", "--model", call.model]
        if call.reviewer_access is ReviewerAccess.CONTEXT_ONLY:
            cmd += ["--tools", ""]
        return cmd

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        return stdout.decode("utf-8")


def _resolve() -> str:
    exe = shutil.which(_EXECUTABLE)
    if exe is None:
        raise RuntimeError(f"{_EXECUTABLE} : introuvable sur le PATH")
    return exe
