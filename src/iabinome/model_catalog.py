"""Catalogue éditable des identifiants de modèles proposés par la GUI."""

from __future__ import annotations

import tomllib
from pathlib import Path


class ModelCatalogError(ValueError):
    """Le fichier de modèles doit être corrigé avant une création."""


DEFAULT = "(par défaut)"


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
    return value
