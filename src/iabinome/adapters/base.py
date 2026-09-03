"""Le protocole d'adaptateur — capacités communes aux deux outils, rien de plus.

`CallSpec` ne porte **ni fournisseur, ni budget, ni session, ni rôle métier** : le
rôle n'intervient que dans le prompt et le nom logique de l'appel. Ce qui est
propre à un outil — sortie structurée native, session persistante, erreur de quota
typée — est un bonus, jamais un prérequis (CONCEPTION_FINALE.md §8).

**Aucun nom de fournisseur hors de ce paquet.** Le noyau ne manipule que des
`adapter_id` opaques.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..models import ReviewerAccess, Role


@dataclass(frozen=True)
class Capabilities:
    supports_context_only: bool
    supports_model_override: bool


@dataclass(frozen=True)
class ObservedCli:
    """Sondée à chaque `run`, inscrite dans `intention.json` comme preuve
    factuelle de **cet** appel — jamais comme autorité pour le suivant."""

    present: bool
    version: str


@dataclass(frozen=True)
class CallSpec:
    prompt: str
    model: str
    timeout_seconds: float
    work_root: Path
    reviewer_access: ReviewerAccess | None


class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities

    def default_model(self, role: Role) -> str:
        """Le défaut est une propriété de l'adaptateur pour un rôle, jamais une
        constante du noyau : « Opus 5 pour A » n'a aucun sens si A est Codex."""

    def probe(self) -> ObservedCli: ...

    def command(self, call: CallSpec) -> list[str]: ...

    def extract(self, stdout: bytes, stderr: bytes) -> str: ...
