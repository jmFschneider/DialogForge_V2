"""Fichier de configuration — des valeurs par défaut, jamais un état.

Cherché dans l'ordre : `--config <chemin>`, puis `./iabinome.toml`, puis
`~/.iabinome.toml`. **Le premier trouvé gagne, et les autres sont ignorés** :
fusionner deux fichiers rendrait indevinable d'où vient une valeur, et la
commande annonce sur `stderr` celui qui a servi.

**Il ne touche jamais une collaboration existante.** Il fournit des défauts au
moment du `new`, et `--timeout` à `run`/`resume`. Une fois la collaboration
créée, `configuration.json` est la seule vérité : éditer ce fichier-ci ne change
rien à ce qui tourne déjà. Sans quoi une modification globale déplacerait en
silence le comportement d'un cycle en cours — exactement l'état caché que
`etat.json` existe pour rendre visible.

**Aucun chemin ne s'y règle** — ni corpus, ni demande. Un chemin dans un fichier
global rendrait une collaboration non reproductible d'une machine à l'autre,
alors que le manifeste de corpus existe pour figer cela explicitement.

Clé inconnue, type inattendu ou fichier illisible sont un **refus**, jamais un
défaut permissif (`C2b`) : un réglage silencieusement ignoré est pire qu'un
réglage absent, parce qu'on croit l'avoir posé.

TOML parce que `tomllib` est dans la bibliothèque standard depuis 3.11 — la
lecture suffit, rien n'écrit ce fichier — et parce qu'un fichier édité à la main
mérite des commentaires, que JSON ne permet pas.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Attribut de module, comme `cli.ADAPTERS` : **tout test de la CLI doit le
# neutraliser**, sans quoi un `iabinome.toml` du dépôt ou du dossier personnel
# rendrait la suite dépendante de la machine.
SEARCH_PATHS: tuple[Path, ...] = (Path("iabinome.toml"), Path.home() / ".iabinome.toml")

# Type attendu par clé. `float` accepte aussi un entier TOML — `timeout = 600`
# est la forme qu'on écrit naturellement.
_SPEC: dict[str, type] = {
    "agent_a": str,
    "agent_b": str,
    "model_a": str,
    "model_b": str,
    "kind": str,
    "reviewer_access": str,
    "max_revisions": int,
    "timeout": float,
}


class SettingsError(ValueError):
    """Le fichier de configuration est illisible, ou porte une clé ou une
    valeur refusée. La collaboration n'est pas créée."""


@dataclass(frozen=True)
class Settings:
    """`path` est `None` quand aucun fichier n'a été trouvé — cas normal."""

    path: Path | None
    values: dict[str, Any]


def load(explicit: str | None = None) -> Settings:
    """`--config` **exige** que le fichier existe : le demander et ne pas
    l'avoir est une erreur, pas un silence. Les emplacements implicites, eux,
    sont absents sans conséquence."""
    if explicit is not None:
        path = Path(explicit)
        if not path.is_file():
            raise SettingsError(f"--config : fichier introuvable : {path}")
        return Settings(path=path, values=_parse(path))
    for candidate in SEARCH_PATHS:
        if candidate.is_file():
            return Settings(path=candidate, values=_parse(candidate))
    return Settings(path=None, values={})


def _parse(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SettingsError(f"{path} : {exc}") from exc
    unknown = sorted(set(raw) - set(_SPEC))
    if unknown:
        raise SettingsError(
            f"{path} : cle(s) inconnue(s) {unknown} ;"
            f" attendues : {sorted(_SPEC)}"
        )
    return {key: _checked(path, key, value) for key, value in raw.items()}


def _checked(path: Path, key: str, value: Any) -> Any:
    """`bool` est un `int` en Python : sans ce refus explicite,
    `max_revisions = true` passerait pour `1`.

    Un entier est accepté là où un `float` est attendu — `timeout = 600` est la
    forme qu'on écrit naturellement — mais jamais l'inverse : `max_revisions`
    reste un entier.
    """
    expected = _SPEC[key]
    accepted: tuple[type, ...] = (int, float) if expected is float else (expected,)
    if isinstance(value, bool) or not isinstance(value, accepted):
        raise SettingsError(f"{path} : {key} = {value!r} — {expected.__name__} attendu")
    return value
