"""Adaptateur Codex CLI — outil-2.

Formes mesurées le 2026-09-03 (`conception/CARACTERISATION_CLI.md`), jamais une
attestation durable (CONCEPTION_FINALE.md §8). Le prompt arrive par stdin via
`-` (point 1) ; `extract()` lit `stdout` seul, outil-2 écrivant sa bannière sur
`stderr` en sortant proprement (point 4). `-c features.shell_tool=false` sert
le profil `CONTEXT_ONLY` de B — équivalent mesuré à `--disable shell_tool`
(point 2) ; réserve non mesurée : les autres capacités listées en §12.3.
"""

from __future__ import annotations

import shutil

from ..models import ReviewerAccess, Role
from .base import AdapterError, CallSpec, Capabilities, ObservedCli, probe_version

_EXECUTABLE = "codex"
_DEFAULT_MODEL = "gpt-5.6-sol"


class CodexAdapter:
    adapter_id = "codex"
    capabilities = Capabilities(
        supports_context_only=True,
        supports_model_override=True,
        enforces_read_only=True,
        fresh_session=True,
    )

    def default_model(self, role: Role) -> str:
        """CLAUDE.md §6 ne fixe de rôle que pour Claude : Codex garde son
        propre défaut, mesuré dans `~/.codex/config.toml`, pour les deux rôles."""
        return _DEFAULT_MODEL

    def probe(self) -> ObservedCli:
        exe = shutil.which(_EXECUTABLE)
        if exe is None:
            return ObservedCli(present=False, version="")
        return ObservedCli(present=True, version=probe_version(exe))

    def command(self, call: CallSpec) -> list[str]:
        exe = _resolve()
        # 2.2 : session éphémère, ni configuration ni règles de l'utilisateur (`auth`
        # reste lue). Formes lues dans `codex exec --help` 0.155.0, **non éprouvées
        # sur un appel réel** avant le lot 3.
        cmd = [
            exe, "exec", "-m", call.model, "--sandbox", "read-only", "--skip-git-repo-check",
            "--ephemeral", "--ignore-user-config", "--ignore-rules",
        ]
        if call.reviewer_access is ReviewerAccess.CONTEXT_ONLY:
            cmd += ["-c", "features.shell_tool=false"]
        cmd.append("-")
        return cmd

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        return stdout.decode("utf-8")


def _resolve() -> str:
    exe = shutil.which(_EXECUTABLE)
    if exe is None:
        raise AdapterError(f"{_EXECUTABLE} : introuvable sur le PATH")
    return exe
