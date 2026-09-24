"""Fichier de configuration — des valeurs par défaut, jamais un état.

Cherché dans l'ordre : `--config <chemin>`, puis `./dialogforge.toml`, puis
`~/.dialogforge/reglages.toml`. **Le premier trouvé gagne, et les autres sont
ignorés** : fusionner deux fichiers rendrait indevinable d'où vient une valeur,
et la commande annonce sur `stderr` celui qui a servi.

Le nom du dossier courant porte celui du produit, jamais une généralité comme
`reglages.toml` : le fichier est cherché **là où vous lancez la commande**, et
une clé inconnue est un refus (plus bas) — un fichier homonyme d'un autre outil
ferait donc échouer `new` et `run` au lieu d'être ignoré. Dans le dossier
personnel, c'est `~/.dialogforge/` qui porte le nom, et le fichier sa fonction.

Les anciens noms (`iabinome.toml`, `~/.iabinome.toml`) sont **encore lus**, en
dernier recours et **en le disant** : cesser de les lire en silence ferait
chercher la panne ailleurs.

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

from .models import positive_seconds

# Attribut de module, comme `cli.ADAPTERS` : **tout test de la CLI doit le
# neutraliser**, sans quoi un `dialogforge.toml` du dépôt ou du dossier personnel
# rendrait la suite dépendante de la machine. Les anciens noms sont dans la même
# liste, après les nouveaux : un seul attribut à neutraliser, et l'ordre dit la
# précédence — le nouveau nom gagne toujours sur l'ancien.
SEARCH_PATHS: tuple[Path, ...] = (
    Path("dialogforge.toml"),
    Path.home() / ".dialogforge" / "reglages.toml",
    Path("iabinome.toml"),
    Path.home() / ".iabinome.toml",
)

# Ancien nom → ce qu'il faut écrire désormais. Sert le message, jamais la
# lecture : le fichier est lu tel qu'il est, personne ne le renomme à votre place.
_RENAMED: dict[str, str] = {
    "iabinome.toml": "dialogforge.toml",
    ".iabinome.toml": "~/.dialogforge/reglages.toml",
}

# Type attendu par clé. `float` accepte aussi un entier TOML — `timeout = 600`
# est la forme qu'on écrit naturellement.
_SPEC: dict[str, type] = {
    "agent_a": str,
    "agent_b": str,
    "model_a": str,
    "model_b": str,
    "effort_a": str,
    "effort_b": str,
    "agent_cadrage": str,
    "model_cadrage": str,
    "effort_cadrage": str,
    "web_access": bool,
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
    """`path` est `None` quand aucun fichier n'a été trouvé — cas normal.

    `legacy_note` porte la phrase à afficher quand le fichier trouvé porte un
    ancien nom : le réglage s'applique, et l'utilisateur sait quoi renommer.
    """

    path: Path | None
    values: dict[str, Any]
    legacy_note: str | None = None


def load(explicit: str | None = None, base: Path | None = None) -> Settings:
    """`--config` **exige** que le fichier existe : le demander et ne pas
    l'avoir est une erreur, pas un silence. Les emplacements implicites, eux,
    sont absents sans conséquence.

    `base` fixe le dossier où chercher les noms relatifs : sans lui, c'est le
    dossier courant, comme en ligne de commande. Une interface qui ne se lance
    pas depuis un terminal le fixe elle-même, et le montre."""
    if explicit is not None:
        path = Path(explicit)
        if not path.is_file():
            raise SettingsError(f"--config : fichier introuvable : {path}")
        return Settings(path=path, values=_parse(path))
    for candidate in SEARCH_PATHS:
        if base is not None:
            candidate = base / candidate  # un chemin absolu reste lui-même
        if candidate.is_file():
            return Settings(
                path=candidate, values=_parse(candidate), legacy_note=_legacy_note(candidate)
            )
    return Settings(path=None, values={})


DEFAULT_TIMEOUT = 1800.0
FROM_COMMAND = "option de la commande"
FROM_PROGRAM = "défaut du programme"


@dataclass(frozen=True)
class Timeout:
    """Le délai d'un lancement et **d'où il vient** : l'option de la commande, le
    chemin du fichier retenu (ancien nom compris), ou le défaut du programme.
    Résolu à chaque lancement, jamais écrit dans la collaboration."""

    seconds: float
    origin: str
    settings: Settings


def resolve_timeout(
    explicit: str | None, override: float | None, base: Path | None = None
) -> Timeout:
    """Option > fichier > défaut du programme. Le fichier est chargé même quand
    l'option tranche : un fichier invalide reste un refus, quelle que soit la
    valeur retenue."""
    found = load(explicit, base)
    if override is not None:
        return Timeout(positive_seconds(override, "--timeout"), FROM_COMMAND, found)
    if "timeout" in found.values:
        try:
            seconds = positive_seconds(float(found.values["timeout"]), "timeout")
        except ValueError as exc:
            raise SettingsError(f"{found.path} : {exc}") from exc
        return Timeout(seconds, str(found.path), found)
    return Timeout(DEFAULT_TIMEOUT, FROM_PROGRAM, found)


def _legacy_note(path: Path) -> str | None:
    """Rien à dire pour un nom courant ; sinon, le nom à écrire désormais."""
    renamed = _RENAMED.get(path.name)
    if renamed is None:
        return None
    return f"{path} : ancien nom de fichier, lu quand même — renommez-le en {renamed}"


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
    if (isinstance(value, bool) and expected is not bool) or not isinstance(value, accepted):
        raise SettingsError(f"{path} : {key} = {value!r} — {expected.__name__} attendu")
    return value
