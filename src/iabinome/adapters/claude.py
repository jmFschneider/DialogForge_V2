"""Adaptateur Claude Code — outil-1.

Formes mesurées le 2026-09-03 (`conception/CARACTERISATION_CLI.md`), jamais une
attestation durable : le prévol resonde présence et version à chaque `run`
(CONCEPTION_FINALE.md §8). `--tools ""` désactive tous les outils — documenté
dans `--help` — et sert le profil `CONTEXT_ONLY` de B (point 2 du relevé).
"""

from __future__ import annotations

import json
import shutil

from ..models import AgentPurpose, ReviewerAccess
from .base import (
    AdapterError,
    CallSpec,
    Capabilities,
    EnvPolicy,
    FramingSessionSpec,
    ObservedCli,
    probe_version,
)

_EXECUTABLE = "claude"
_DEFAULT_MODEL = {
    AgentPurpose.A: "opus", AgentPurpose.B: "fable", AgentPurpose.FRAMING: "opus",
}
# Lecture seule par défaut. Le web (recherche et lecture d'une page, **jamais** une écriture ni
# une exécution) n'entre que si la collaboration le demande : `web_access`, figé à `new`.
_READ_TOOLS = "Read,Grep,Glob"
_WEB_TOOLS = "WebSearch,WebFetch"


class ClaudeAdapter:
    adapter_id = "claude"
    capabilities = Capabilities(
        supports_context_only=True,
        supports_model_override=True,
        enforces_read_only=True,
        fresh_session=True,
        effort_levels=("low", "medium", "high", "xhigh", "max"),
        controls_web_access=True,
        supports_persistent_framing_session=True,
    )
    env = EnvPolicy(
        owned_prefixes=("CLAUDE", "ANTHROPIC_"),
        host_refused=frozenset({
            "CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_ENTRYPOINT",
            "CLAUDE_CODE_EXECPATH", "CLAUDE_CODE_MESSAGING_SOCKET",
            "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_SESSION_ATTENDED",
            "CLAUDE_CODE_SESSION_ID", "CLAUDE_EFFORT", "CLAUDE_ENV_FILE", "CLAUDE_PID",
            "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR",
        }),
        kept={
            "CLAUDE_CONFIG_DIR": "choisit le compte : le dossier de configuration et "
            "d'authentification que la CLI lit — le retirer change de compte sans le dire",
            "CLAUDE_CODE_OAUTH_TOKEN": "authentification de Claude par jeton",
            "CLAUDE_CODE_GIT_BASH_PATH": "Claude Code en a besoin pour démarrer sous Windows",
            "ANTHROPIC_API_KEY": "authentification par clé d'API, quand c'est celle de "
            "l'utilisateur",
        },
    )

    def default_model(self, purpose: AgentPurpose) -> str:
        """Opus pour A, Fable pour B (CLAUDE.md §6) — reste surchargeable :
        mesuré le 2026-09-03, ce compte n'a pas les crédits pour Fable. F, qui
        converse et rédige, prend le défaut du producteur."""
        return _DEFAULT_MODEL[purpose]

    def probe(self) -> ObservedCli:
        exe = shutil.which(_EXECUTABLE)
        if exe is None:
            return ObservedCli(present=False, version="")
        return ObservedCli(present=True, version=probe_version(exe))

    def command(self, call: CallSpec) -> list[str]:
        exe = _resolve()
        # 2.2 : lecture seule, session fraîche, rien de l'utilisateur ni de l'hôte
        # (réglages, hooks, MCP, commandes). Formes lues dans `claude --help`
        # 2.1.278, acceptées sur des appels réels au lot 3 (2026-09-19 et 20) ;
        # leur **effet** n'est acquis que là où il a été mesuré (`LIMITES.md` §2).
        cmd = [
            exe, "-p", "--model", call.model,
            "--restricted", "--strict-mcp-config",
            "--no-session-persistence", "--disable-slash-commands",
        ]
        if call.reviewer_access is ReviewerAccess.CONTEXT_ONLY:
            tools = ""  # aucun outil, web compris
        elif call.web_access:
            tools = f"{_READ_TOOLS},{_WEB_TOOLS}"
        else:
            tools = _READ_TOOLS
        cmd += ["--tools", tools]
        if tools and call.web_access:
            # Sans cette autorisation, l'appel non interactif refuse ces deux outils faute
            # de personne pour approuver. Vérifié le 2026-09-20 : un `WebSearch` réel, des
            # résultats réels, aucun refus de permission.
            cmd += ["--allowedTools", _WEB_TOOLS]
        if call.effort is not None:
            cmd += ["--effort", call.effort]
        return cmd

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        return stdout.decode("utf-8")

    def framing_command(
        self, spec: FramingSessionSpec, session: str | None, prompt: str
    ) -> list[str]:
        """Les arguments de A et B, sauf trois : la session persiste, la sortie JSON porte
        son identifiant, et les tours suivants la reprennent (`--resume`). Mesuré par le PO
        le 2026-09-25 (`reference/PROTOCOLE_CADRAGE_LOT4.md`, 2.1.282) : même identifiant
        en reprise, contexte rappelé, et `--tools` y vaut encore — aucune écriture."""
        cmd = [
            _resolve(), "-p", "--model", spec.model,
            "--restricted", "--strict-mcp-config", "--disable-slash-commands",
            "--tools", _READ_TOOLS, "--output-format", "json",
        ]
        if session is not None:
            cmd += ["--resume", session]
        if spec.effort is not None:
            cmd += ["--effort", spec.effort]
        return cmd

    def framing_extract(self, stdout: bytes, stderr: bytes) -> tuple[str, str | None]:
        """Un seul objet JSON : la réponse dans `result`, l'identifiant dans `session_id`."""
        data = json.loads(stdout.decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("result"), str):
            raise ValueError("sortie JSON sans champ result")
        if data.get("is_error"):
            raise ValueError(f"l'outil signale une erreur : {data.get('subtype')}")
        session = data.get("session_id")
        return data["result"], session if isinstance(session, str) and session else None


def _resolve() -> str:
    exe = shutil.which(_EXECUTABLE)
    if exe is None:
        raise AdapterError(f"{_EXECUTABLE} : introuvable sur le PATH")
    return exe
