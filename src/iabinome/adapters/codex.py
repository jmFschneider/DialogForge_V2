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
from .base import (
    AdapterError,
    CallSpec,
    Capabilities,
    EnvPolicy,
    ObservedCli,
    probe_version,
)

_EXECUTABLE = "codex"
_DEFAULT_MODEL = "gpt-5.6-sol"


class CodexAdapter:
    adapter_id = "codex"
    capabilities = Capabilities(
        supports_context_only=True,
        supports_model_override=True,
        enforces_read_only=True,
        fresh_session=True,
        effort_levels=("minimal", "low", "medium", "high", "xhigh"),
        controls_web_access=True,
    )
    env = EnvPolicy(
        owned_prefixes=("CODEX_", "OPENAI_"),
        host_refused=frozenset({"CODEX_PERMISSION_PROFILE", "CODEX_SESSION_ID", "CODEX_THREAD_ID"}),
        kept={
            "CODEX_HOME": "où Codex lit son authentification — `--ignore-user-config` ne "
            "l'ignore pas, sa propre aide dit « auth still uses CODEX_HOME »",
            "CODEX_MANAGED_PACKAGE_ROOT": "posée par le lanceur npm de Codex, qui la réécrit "
            "pour son enfant (lu dans `bin/codex.js`) : elle décrit le paquet installé",
            "OPENAI_API_KEY": "authentification par clé d'API, quand c'est celle de "
            "l'utilisateur",
        },
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
        # Toujours explicite, dans les deux sens : `disabled` par défaut, `live` si la
        # collaboration le demande — et `disabled` quoi qu'il arrive en `CONTEXT_ONLY`.
        # La clé est celle du PO ; **non éprouvée en réel** (lot 3).
        live = call.web_access and call.reviewer_access is not ReviewerAccess.CONTEXT_ONLY
        cmd += ["-c", f"web_search={'live' if live else 'disabled'}"]
        if call.effort is not None:
            # Valeur TOML ; si elle n'en est pas une, Codex la prend comme chaîne littérale
            # (`codex exec --help`) : pas de guillemets, que le lanceur `.CMD` abîmerait.
            cmd += ["-c", f"model_reasoning_effort={call.effort}"]
        cmd.append("-")
        return cmd

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        return stdout.decode("utf-8")


def _resolve() -> str:
    exe = shutil.which(_EXECUTABLE)
    if exe is None:
        raise AdapterError(f"{_EXECUTABLE} : introuvable sur le PATH")
    return exe
