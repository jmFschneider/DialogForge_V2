"""Ce que l'agent voit et hérite, et rien de plus (plan V2, 2.2 puis 3.1).

Deux fuites mesurées le 2026-09-19 avant de coder :

- l'agent tournait **dans le dossier de collaboration** : un reviewer y atteignait
  `appels/`, `echanges/` (le journal du producteur), les anciennes versions de
  `demande.md` — de quoi critiquer autre chose que ce qu'on lui soumet ;
- il héritait de l'**environnement complet** du processus parent : identifiants de
  session, jeton de messagerie et racine de plan de l'hôte qui a lancé l'outil.

Le dossier neutre ne contient qu'une **copie** du corpus (jamais un lien, jamais
un lien dur : écrire dedans ne doit pas atteindre l'original).

**L'environnement dépend de l'adaptateur** (3.1). Ce module ne connaît aucun
fournisseur : chaque adaptateur déclare une `EnvPolicy` — ce qui lui appartient, ce
que son hôte y dépose, ce qu'il garde et pourquoi. Un processus reçoit l'environnement
du parent, moins :

- ce que **tous** refusent : `PLAN_ID` et `PWF_*` (le plan appartient à l'humain) ;
- les identifiants de **session** de n'importe quel hôte (`host_refused`, de chaque
  adaptateur) ;
- tout ce qui **appartient à un autre fournisseur** : jetons, chemins de configuration
  et clés d'API de l'autre outil ne vont pas chez celui-ci.

Ce qu'un adaptateur garde (`kept`) ne lui est jamais retiré au titre des autres — chaque
variable y a sa raison, et un test le prouve. Tout le reste passe : une liste
d'autorisation casserait le `PATH` et l'authentification de la première CLI dont on ignore
les besoins.

Ce n'est **pas** un confinement du système d'exploitation ni du réseau : un agent qui écrit
un chemin absolu n'est arrêté que par l'outil lui-même, et ce que le prompt contient peut
sortir par une requête web si la collaboration l'a ouverte. Le contrôle post-appel du
corpus (`SOURCES_MODIFIED`) constate, il n'empêche pas. Voir `reference/FRONTIERE_ROLES.md`.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from .adapters.base import EnvPolicy

# Le plan appartient à l'humain : aucun rôle n'en a besoin, aucun n'en hérite.
_PLAN_NAMES = frozenset({"PLAN_ID"})
_PLAN_PREFIXES = ("PWF_",)


def _refused(name: str, own: EnvPolicy, others: tuple[EnvPolicy, ...]) -> bool:
    upper = name.upper()  # Windows ne distingue pas la casse des variables
    if upper in _PLAN_NAMES or upper.startswith(_PLAN_PREFIXES):
        return True
    if any(upper in {n.upper() for n in policy.host_refused} for policy in (own, *others)):
        return True
    if upper in {n.upper() for n in own.kept}:
        return False
    if upper.startswith(tuple(p.upper() for p in own.owned_prefixes)):
        return False
    return any(
        upper.startswith(prefix.upper()) for policy in others for prefix in policy.owned_prefixes
    )


def clean_env(
    environ: Mapping[str, str], own: EnvPolicy, others: Iterable[EnvPolicy] = ()
) -> dict[str, str]:
    """L'environnement transmis au processus de l'adaptateur `own` : celui du parent,
    moins le plan, les sessions d'hôte et ce qui appartient aux adaptateurs `others`."""
    rest = tuple(others)
    return {name: value for name, value in environ.items() if not _refused(name, own, rest)}


def refused_names(
    environ: Mapping[str, str], own: EnvPolicy, others: Iterable[EnvPolicy] = ()
) -> list[str]:
    """Les **noms** retirés, jamais leurs valeurs : de quoi le tracer dans
    `intention.json` sans y déposer un secret."""
    rest = tuple(others)
    return sorted(name for name in environ if _refused(name, own, rest))


@contextmanager
def neutral_workdir(collab: Path) -> Iterator[Path]:
    """Un dossier jetable, hors de la collaboration, avec pour seul contenu une
    **copie** de `corpus/fichiers/` — l'emplacement que les prompts nomment.

    Supprimé à la sortie, y compris sur exception : rien n'y survit à l'appel.
    """
    with tempfile.TemporaryDirectory(prefix="iabinome-") as tmp:
        root = Path(tmp)
        source = collab / "corpus" / "fichiers"
        if source.is_dir():
            shutil.copytree(source, root / "corpus" / "fichiers", symlinks=False)
        yield root
