"""Le cadrage avec agent F, avant toute collaboration (`conception/CADRAGE_AGENT.md`).

Ce module possède la session de F — rien d'autre ne la touche : ni A, ni B, ni le
moteur A/B, qui garde son verrou et `current_call` (§8.2). Un cadrage n'est pas une
collaboration : aucun `etat.json`, aucune phase, aucune reprise après la fin du
processus (§6.1).

**Session par reprise d'identifiant** (amendement A3) : chaque tour relance l'outil
sur la même session fournisseur, par le transport commun — délai dur, flux bornés,
arbre terminé, `resultat.json` seulement pour une sortie propre. Le premier tour en
ouvre une neuve ; l'identifiant que l'outil déclare est gardé **en mémoire** pour les
suivants, masqué dans les traces, et oublié à la fermeture.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import contracts, isolation, storage, transport
from .adapters.base import AgentAdapter, EnvPolicy, FramingSessionSpec, ObservedCli
from .models import SCHEMA_VERSION, AgentPurpose

_MASK = "<session>"


class FramingError(RuntimeError):
    """Refus lisible du cadrage — prévol, ou session déjà fermée."""


@dataclass(frozen=True)
class Exchange:
    """Un tour de F. `outcome` vaut `COMPLETED` quand `text` porte sa réponse ;
    sinon, il nomme l'incident, et le tour n'est **jamais relancé tout seul** (§2.4) :
    l'humain relance dans la même session, clôt ou annule."""

    call_dir: Path
    outcome: str
    text: str | None = None
    detail: str = ""


def check_adapter(
    adapter_id: str, adapters: Mapping[str, AgentAdapter], model: str | None,
    effort: str | None,
) -> tuple[str, ObservedCli]:
    """Le prévol de F (§3.2, étapes 3 et 4) : il précède toute ouverture de session et
    tout appel. Rend le modèle effectif et la version observée."""
    adapter = adapters.get(adapter_id)
    if adapter is None:
        raise FramingError(f"adaptateur de cadrage inconnu : {adapter_id!r}")
    caps = adapter.capabilities
    missing = [
        label for label, present in (
            ("lecture seule", caps.enforces_read_only),
            ("session persistante de cadrage", caps.supports_persistent_framing_session),
        ) if not present
    ]
    if missing:
        raise FramingError(f"{adapter_id} : cadrage non supporté ({', '.join(missing)})")
    default = adapter.default_model(AgentPurpose.FRAMING)
    if model is not None and model != default and not caps.supports_model_override:
        raise FramingError(f"{adapter_id} : modèle non remplaçable")
    if effort is not None and effort not in caps.effort_levels:
        accepted = ", ".join(caps.effort_levels) or "aucun : réglage non supporté"
        raise FramingError(f"{adapter_id} : effort {effort!r} refusé — attendu : {accepted}")
    seen = adapter.probe()
    if not seen.present:
        raise FramingError(f"{adapter_id} : CLI absente")
    return model or default, seen


class FramingSession:
    """La session de F : possédée par une seule commande ou un seul contrôleur, un
    `send` à la fois, jamais reprise après `close` (§6.1)."""

    def __init__(
        self, adapter: AgentAdapter, spec: FramingSessionSpec, *,
        others: Iterable[EnvPolicy] = (), control: transport.ExecutionControl | None = None,
    ) -> None:
        self._adapter, self.spec, self._control = adapter, spec, control
        rest = tuple(others)
        self._env = isolation.clean_env(os.environ, adapter.env, rest)
        self._removed = isolation.refused_names(os.environ, adapter.env, rest)
        self._session: str | None = None
        self.exchanges = 0
        self.closed = False

    def send(self, prompt: str, call_dir: Path) -> Exchange:
        """Un tour : le prompt par stdin, les traces sous `call_dir` (§8.1)."""
        if self.closed:
            raise FramingError("session de cadrage fermée : elle ne se reprend pas")
        # Résolu avant le premier octet écrit, comme pour A et B : un exécutable disparu
        # est un refus qui ne laisse aucun dossier d'appel orphelin.
        argv = self._adapter.framing_command(self.spec, self._session, prompt)
        call_dir.mkdir(parents=True)
        storage.write_atomic_text(call_dir / "prompt.txt", prompt)
        _write_json(call_dir / "intention.json", {
            "schema_version": SCHEMA_VERSION, "purpose": AgentPurpose.FRAMING.value,
            "exchange": self.exchanges + 1, "adapter_id": self._adapter.adapter_id,
            "model": self.spec.model, "effort": self.spec.effort,
            "prompt_sha256": contracts.normalize(prompt).sha256,
            # `argv[0]` retiré (aucun chemin absolu persisté) et l'identifiant de session
            # masqué : il reste encapsulé, jamais une autorité (§6.1, §9.2).
            "invocation_args": [self._mask(arg) for arg in argv[1:]],
            "session": "neuve" if self._session is None else "reprise",
            "workdir": "neutre", "env_removed": self._removed,
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        self.exchanges += 1
        try:
            result = transport.run(
                argv, cwd=self.spec.work_root, call_dir=call_dir,
                timeout_seconds=self.spec.timeout_seconds, stdin_text=prompt,
                env=self._env, control=self._control,
            )
        except transport.TransportError as exc:
            return Exchange(call_dir, "LAUNCH_FAILED", detail=str(exc))
        if result.outcome is not transport.Outcome.COMPLETED:
            return Exchange(call_dir, result.outcome.value)
        if result.return_code != 0:
            return Exchange(call_dir, "CLI_FAILED", detail=f"code de retour {result.return_code}")
        try:
            text, session = self._adapter.framing_extract(
                (call_dir / "stdout.txt").read_bytes(), (call_dir / "stderr.txt").read_bytes()
            )
        except (UnicodeDecodeError, ValueError) as exc:
            return Exchange(call_dir, "DECODE_FAILED", detail=str(exc))
        storage.write_atomic_text(call_dir / "reponse_brute.txt", text)
        if session is None or (self._session is not None and session != self._session):
            # Une réponse hors de la session ouverte n'est pas un tour de ce cadrage :
            # la garder ouverte ferait converser F sans le contexte qu'on lui croit.
            self.close()
            return Exchange(call_dir, "SESSION_LOST", text, "l'outil n'a pas repris la session")
        self._session = session
        return Exchange(call_dir, "COMPLETED", text)

    def close(self) -> None:
        """Oublie l'identifiant : plus aucun envoi possible. La trace que l'outil garde
        de sa propre session n'est ni lue ni reprise par DialogForge (A3)."""
        self._session = None
        self.closed = True

    def _mask(self, arg: str) -> str:
        return arg if self._session is None else arg.replace(self._session, _MASK)


def open_session(
    adapter: AgentAdapter, spec: FramingSessionSpec, *,
    others: Iterable[EnvPolicy] = (), control: transport.ExecutionControl | None = None,
) -> FramingSession:
    """Ouvre une session **neuve** : rien n'est repris d'un cadrage antérieur (§5.2).
    L'outil ne la crée qu'au premier `send` — ouvrir ne coûte aucun appel."""
    if not adapter.capabilities.supports_persistent_framing_session:
        raise FramingError(f"{adapter.adapter_id} : session persistante de cadrage non supportée")
    return FramingSession(adapter, spec, others=others, control=control)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
