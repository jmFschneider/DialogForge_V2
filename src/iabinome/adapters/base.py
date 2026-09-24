"""Le protocole d'adaptateur — capacités communes aux deux outils, rien de plus.

`CallSpec` ne porte **ni fournisseur, ni budget, ni session, ni rôle métier** : le
rôle n'intervient que dans le prompt et le nom logique de l'appel. Ce qui est
propre à un outil — sortie structurée native, session persistante, erreur de quota
typée — est un bonus, jamais un prérequis (CONCEPTION_FINALE.md §8).

**Une exception, écrite** : l'agent de cadrage F exige une session persistante
(`conception/CADRAGE_AGENT.md`, amendement A3 — reprise par identifiant, que les deux
outils offrent). Elle vit dans `FramingSessionSpec` et les deux méthodes `framing_*`,
jamais dans `CallSpec` : A et B n'en dépendent pas.

**Aucun nom de fournisseur hors de ce paquet.** Le noyau ne manipule que des
`adapter_id` opaques.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..models import AgentPurpose, ReviewerAccess

_VERSION_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class Capabilities:
    """Ce que l'adaptateur **impose dans l'argv qu'il construit** — jamais une
    attestation de ce que la CLI fait réellement. Les mesures du lot 3 valent
    point par point, jamais par extension : `docs/LIMITES.md` §2 dit lesquelles.

    `enforces_read_only` : aucun outil d'écriture ni d'exécution n'est offert à
    l'agent. `fresh_session` : rien n'est repris d'une session précédente, rien
    n'est conservé pour la suivante. Le prévol refuse un adaptateur qui ne les
    déclare pas : on ne lance pas un rôle sans sa séparation (plan V2, 2.2).
    """

    supports_context_only: bool
    supports_model_override: bool
    enforces_read_only: bool = False
    fresh_session: bool = False
    # Les niveaux d'effort que la CLI accepte, dans son vocabulaire. Vide = le réglage n'est
    # pas supporté : le prévol refuse alors toute valeur, avant tout appel.
    effort_levels: tuple[str, ...] = ()
    # L'adaptateur **impose** la politique d'accès web dans son argv, dans les deux sens
    # (ouvert comme fermé) : le défaut est « fermé », et il doit être explicite.
    controls_web_access: bool = False
    # Agent de cadrage F seulement : chaque cadrage ouvre une session neuve, tous ses tours
    # la reprennent par son identifiant, et rien ne la reprend après lui (A3). Sans elle,
    # F est refusé avant tout appel — jamais simulé par des sessions éphémères (test 82).
    supports_persistent_framing_session: bool = False


@dataclass(frozen=True)
class EnvPolicy:
    """Ce qu'un fournisseur possède dans l'environnement, et ce qu'il en garde.

    Une CLI reçoit son environnement **et rien de celui de l'autre** : jetons, chemins de
    configuration, clés d'API d'un fournisseur ne vont pas chez l'autre. C'est l'adaptateur
    qui nomme ses variables — le noyau ne connaît que des politiques opaques.

    - `owned_prefixes` : tout ce qui commence ainsi lui appartient, donc est retiré aux autres ;
    - `host_refused` : identifiants de **session** de l'hôte qui l'a lancé, retirés à tous ;
    - `kept` : variables opérationnelles qui restent chez lui, **chacune avec sa raison**.
    """

    owned_prefixes: tuple[str, ...] = ()
    host_refused: frozenset[str] = frozenset()
    kept: Mapping[str, str] = field(default_factory=dict)


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
    effort: str | None = None
    # Même politique pour A et B ; `CONTEXT_ONLY` reste sans aucun outil, web compris.
    web_access: bool = False


@dataclass(frozen=True)
class FramingSessionSpec:
    """Ce qu'un tour de F demande à l'adaptateur. Pas d'accès web : F lit la copie du
    corpus et converse, rien d'autre (§5.2)."""

    model: str
    timeout_seconds: float
    work_root: Path
    effort: str | None = None


class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities
    env: EnvPolicy

    def default_model(self, purpose: AgentPurpose) -> str:
        """Le défaut est une propriété de l'adaptateur pour une finalité, jamais une
        constante du noyau : « Opus 5 pour A » n'a aucun sens si A est Codex."""

    def probe(self) -> ObservedCli: ...

    def command(self, call: CallSpec) -> list[str]: ...

    def extract(self, stdout: bytes, stderr: bytes) -> str: ...

    def framing_command(
        self, spec: FramingSessionSpec, session: str | None, prompt: str
    ) -> list[str]:
        """L'argv d'un tour de F : `session` vaut `None` au premier tour (session
        neuve), puis l'identifiant rendu par `framing_extract`, que l'argv reprend. Le
        prompt passe par stdin ; il n'est donné ici qu'à titre d'information."""

    def framing_extract(self, stdout: bytes, stderr: bytes) -> tuple[str, str | None]:
        """La réponse de F, et l'identifiant de session que l'outil a déclaré.
        Opaque pour le noyau, qui ne l'interprète ni ne le persiste (§6.1)."""


class AdapterError(RuntimeError):
    """L'adaptateur ne peut pas construire son appel — exécutable introuvable.

    Type **nommé**, et non un `RuntimeError` nu : la frontière attrape des types
    un par un, et un `RuntimeError` générique y passait au travers, rendant une
    traceback là où la conception promet un refus lisible.
    """


def probe_version(executable: str) -> str:
    """`<executable> --version`, au mieux : un exécutable trouvé par
    `shutil.which()` reste `present`, même si son bandeau de version échoue."""
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            timeout=_VERSION_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()
