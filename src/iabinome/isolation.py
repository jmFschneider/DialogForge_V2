"""Ce que l'agent voit et hérite, et rien de plus (plan V2, 2.2).

Deux fuites mesurées le 2026-09-19 avant de coder :

- l'agent tournait **dans le dossier de collaboration** : un reviewer y atteignait
  `appels/`, `echanges/` (le journal du producteur), les anciennes versions de
  `demande.md` — de quoi critiquer autre chose que ce qu'on lui soumet ;
- il héritait de l'**environnement complet** du processus parent : identifiants de
  session, jeton de messagerie et racine de plan de l'hôte qui a lancé l'outil.

Le dossier neutre ne contient qu'une **copie** du corpus (jamais un lien, jamais
un lien dur : écrire dedans ne doit pas atteindre l'original). L'environnement est
filtré par une liste de refus **nominative** : une liste d'autorisation casserait
l'authentification et le `PATH` de la première CLI dont on ignore les besoins.

Ce n'est **pas** un confinement du système d'exploitation : un agent qui écrit un
chemin absolu n'est arrêté que par l'outil lui-même. Le contrôle post-appel du
corpus (`SOURCES_MODIFIED`) le constate, il ne l'empêche pas. Voir
`reference/FRONTIERE_ROLES.md`.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

# Variables que l'hôte qui lance l'outil y dépose, et qui n'ont rien à faire chez
# l'agent : identifiants de session, jeton de messagerie, racine de plan, profil de
# permission. Des **noms** relevés — ceux de Claude dans un environnement réel, ceux de
# Codex signalés à la validation de 2.2 — et jamais un préfixe (`CODEX_*`, `CLAUDE_*`) :
# il emporterait au passage l'authentification ou le lanceur. Tout nom nouveau se relève,
# se justifie, et s'ajoute ici.
_REFUSED_NAMES = frozenset({
    "CLAUDECODE",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_SESSION_ATTENDED",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_EFFORT",
    "CLAUDE_ENV_FILE",
    "CLAUDE_PID",
    "CLAUDE_PLUGIN_ROOT",
    "CLAUDE_PROJECT_DIR",
    # L'hôte Codex : identifiants de session et de fil, profil de permission.
    "CODEX_PERMISSION_PROFILE",
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "PLAN_ID",
})

# Variables **opérationnelles** qu'un nom proche pourrait faire retirer, et qui restent
# — chacune avec sa raison. Ce n'est pas une liste d'autorisation : tout ce qui n'est
# pas refusé passe ; cette liste ne sert qu'à dire, et à faire prouver par un test, que
# le refus ne les atteint pas.
KEPT_ON_PURPOSE = {
    "CODEX_HOME": "où Codex lit son authentification — `--ignore-user-config` ne l'ignore pas,"
    " sa propre aide dit « auth still uses CODEX_HOME » ; le retirer le déconnecte",
    "CODEX_MANAGED_PACKAGE_ROOT": "posée par le lanceur npm de Codex, qui la réécrit pour son"
    " enfant (lu dans `bin/codex.js`) : elle décrit le paquet installé, pas la session"
    " de l'hôte",
    "CLAUDE_CODE_OAUTH_TOKEN": "authentification de Claude par jeton",
    "CLAUDE_CODE_GIT_BASH_PATH": "Claude Code en a besoin pour démarrer sous Windows",
}
_REFUSED_PREFIXES = ("PWF_",)


def _refused(name: str) -> bool:
    upper = name.upper()  # Windows ne distingue pas la casse des variables
    return upper in _REFUSED_NAMES or upper.startswith(_REFUSED_PREFIXES)


def clean_env(environ: Mapping[str, str]) -> dict[str, str]:
    """L'environnement transmis à l'agent : celui du parent, moins l'hôte."""
    return {name: value for name, value in environ.items() if not _refused(name)}


def refused_names(environ: Mapping[str, str]) -> list[str]:
    """Les **noms** retirés, jamais leurs valeurs : de quoi le tracer dans
    `intention.json` sans y déposer un secret."""
    return sorted(name for name in environ if _refused(name))


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
