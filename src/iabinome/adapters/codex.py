"""Adaptateur Codex CLI — outil-2.

Formes mesurées le 2026-09-03 (`conception/CARACTERISATION_CLI.md`), jamais une
attestation durable (CONCEPTION_FINALE.md §8). Le prompt arrive par stdin via
`-` (point 1) ; `extract()` lit `stdout` seul, outil-2 écrivant sa bannière sur
`stderr` en sortant proprement (point 4). `-c features.shell_tool=false` sert
le profil `CONTEXT_ONLY` de B — équivalent mesuré à `--disable shell_tool`
(point 2) ; réserve non mesurée : les autres capacités listées en §12.3.
"""

from __future__ import annotations

import json
import shutil
import sys

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
        supports_persistent_framing_session=True,
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

    def default_model(self, purpose: AgentPurpose) -> str:
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
        # reste lue). Formes lues dans `codex exec --help` 0.155.0, acceptées sur des
        # appels réels au lot 3 ; leur **effet** n'est acquis que là où il a été
        # mesuré (`docs/LIMITES.md` §2).
        cmd = [
            exe, "exec", "-m", call.model, "--sandbox", "read-only", "--skip-git-repo-check",
            "--ephemeral", "--ignore-user-config", "--ignore-rules",
        ]
        # `--ignore-user-config` écarte le réglage personnel : sélectionner explicitement
        # le backend Windows natif. Les autres plateformes conservent leur argv.
        if sys.platform == "win32":
            cmd += ["-c", "windows.sandbox=elevated"]
        if call.reviewer_access is ReviewerAccess.CONTEXT_ONLY:
            cmd += ["-c", "features.shell_tool=false"]
        # Toujours explicite, dans les deux sens : `disabled` par défaut, `live` si la
        # collaboration le demande — et `disabled` quoi qu'il arrive en `CONTEXT_ONLY`.
        # La clé est celle du PO ; mesurée le 2026-09-20 : `disabled` a bien coupé la
        # recherche (0 ligne `web search:`, contre 4 en `live` sur le même prompt).
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

    def framing_command(
        self, spec: FramingSessionSpec, session: str | None, prompt: str
    ) -> list[str]:
        """Les arguments de A et B, sans `--ephemeral` pour que la session survive au tour,
        avec `--json` qui porte son identifiant, puis `exec resume <id>`. `resume` n'accepte
        pas `--sandbox` : la lecture seule y passe par `-c sandbox_mode=read-only`. Mesuré
        par le PO le 2026-09-25 (`reference/PROTOCOLE_CADRAGE_LOT4.md`, 0.155.0) : même
        identifiant, contexte rappelé, écriture tentée et refusée par le bac à sable."""
        cmd = [_resolve(), "exec"]
        if session is None:
            cmd += ["-m", spec.model, "--sandbox", "read-only"]
        else:
            cmd += ["resume", "-m", spec.model, "-c", "sandbox_mode=read-only"]
        cmd += ["--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "--json"]
        if sys.platform == "win32":
            cmd += ["-c", "windows.sandbox=elevated"]
        cmd += ["-c", "web_search=disabled"]  # F lit la copie du corpus, rien d'autre (§5.2)
        if spec.effort is not None:
            cmd += ["-c", f"model_reasoning_effort={spec.effort}"]
        if session is not None:
            cmd.append(session)
        cmd.append("-")
        return cmd

    def framing_extract(self, stdout: bytes, stderr: bytes) -> tuple[str, str | None]:
        """Un événement JSON par ligne : l'identifiant dans `thread.started`, la réponse
        dans le **dernier** message de l'agent — les précédents annoncent ce qu'il va
        faire. Sans `turn.completed`, le tour n'a pas abouti."""
        text = session = None
        completed = False
        for line in stdout.decode("utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("événement JSON qui n'est pas un objet")
            item = event.get("item")
            if event.get("type") == "thread.started":
                session = event.get("thread_id")
            elif event.get("type") == "turn.completed":
                completed = True
            elif event.get("type") == "item.completed" and isinstance(item, dict) and (
                item.get("type") == "agent_message"
            ):
                text = item.get("text")
        if not completed or not isinstance(text, str):
            raise ValueError("tour sans turn.completed ni message de l'agent")
        return text, session if isinstance(session, str) and session else None


def _resolve() -> str:
    exe = shutil.which(_EXECUTABLE)
    if exe is None:
        raise AdapterError(f"{_EXECUTABLE} : introuvable sur le PATH")
    return exe
