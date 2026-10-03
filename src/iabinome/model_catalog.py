"""Catalogue éditable des identifiants de modèles proposés par la GUI."""

from __future__ import annotations

import tomllib
from pathlib import Path


class ModelCatalogError(ValueError):
    """Le fichier de modèles doit être corrigé avant une création."""


DEFAULT = "(par défaut)"
INHERITED = " (hérité de la recherche)"


def load(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    source = path or Path(__file__).with_name("modeles.toml")
    try:
        data = tomllib.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ModelCatalogError(f"Catalogue des modèles illisible ({source}) : {exc}") from exc
    if set(data) != {"models"} or not isinstance(data["models"], dict):
        raise ModelCatalogError("Catalogue des modèles : section [models] attendue")
    result: dict[str, tuple[str, ...]] = {}
    for agent, names in data["models"].items():
        if not isinstance(names, list) or not names or any(
            not isinstance(name, str) or not name or name.strip() != name for name in names
        ) or len(set(names)) != len(names):
            raise ModelCatalogError(f"Catalogue des modèles : liste invalide pour {agent}")
        result[agent] = tuple(names)
    return result


def choices(catalog: dict[str, tuple[str, ...]], agent: str) -> tuple[str, ...]:
    return (DEFAULT, *catalog.get(agent, ()))


def selected(catalog: dict[str, tuple[str, ...]], agent: str, value: str) -> str | None:
    if value == DEFAULT:
        return None
    if value not in catalog.get(agent, ()):
        raise ModelCatalogError(f"Modèle {value!r} absent de la liste de {agent}")
    return value.removesuffix(INHERITED)


def inherit(
    catalog: dict[str, tuple[str, ...]], agent: str, model: str,
) -> tuple[dict[str, tuple[str, ...]], str]:
    """Le modèle d'une recherche, valide pour la CLI, peut manquer au catalogue de la GUI : il
    y est ajouté, étiqueté, plutôt que remplacé en silence. Rend le catalogue et la valeur
    à afficher."""
    known, label = catalog.get(agent, ()), model + INHERITED
    if model in known or label in known:
        return catalog, model if model in known else label
    return {**catalog, agent: (*known, label)}, label
