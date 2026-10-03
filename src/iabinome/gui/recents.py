"""Collaborations récentes de la GUI — un fichier de préférences **non métier**
(`conception/GUI_V1.md` §5.2), jamais lu par une commande de la CLI.

`list <racine>` énumère un dossier ; les récents retrouvent des dossiers ouverts
à des emplacements différents, ordonnés par usage. Une racine choisie par la GUI
est aussi gardée ici. Seuls des chemins et une date d'ouverture y sont gardés —
jamais un statut ni une phase, relus à chaque affichage depuis le dossier lui-même.

Ce fichier se supprime sans effet sur aucune collaboration (AC-05) : il vaut
alors une liste vide.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .. import storage

DEFAULT_PATH = Path.home() / ".dialogforge" / "recents.json"
_MAX_ENTRIES = 10
_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Recent:
    path: Path
    last_opened_at: str
    last_step: str | None = None  # préférence d'affichage d'une mission, jamais une autorité


def load(prefs_path: Path = DEFAULT_PATH) -> tuple[Recent, ...]:
    """Une liste vide si le fichier est absent, illisible ou invalide : un
    repère de confort, jamais une source dont l'absence bloque quoi que ce
    soit."""
    if not prefs_path.is_file():
        return ()
    try:
        text, _ = storage.read_text(prefs_path)
        raw = json.loads(text)
        entries = raw["recents"]
        return tuple(
            Recent(Path(e["path"]), str(e["last_opened_at"]), e.get("last_step")) for e in entries
        )
    except (OSError, ValueError, KeyError, TypeError):
        return ()


def load_root(prefs_path: Path = DEFAULT_PATH) -> Path | None:
    """Répertoire parent choisi dans la GUI, indépendant des collaborations."""
    try:
        text, _ = storage.read_text(prefs_path)
        raw = json.loads(text)
        value = raw.get("root_path")
        return Path(value) if isinstance(value, str) and Path(value).is_absolute() else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def save_root(root: Path, prefs_path: Path = DEFAULT_PATH) -> None:
    """Mémorise la racine sans perdre la liste des dossiers ouverts."""
    resolved = root.resolve()
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_text(prefs_path, _dump(load(prefs_path), resolved))


def record_opened(
    path: Path, prefs_path: Path = DEFAULT_PATH, *, max_entries: int = _MAX_ENTRIES,
    last_step: str | None = None,
) -> tuple[Recent, ...]:
    """Place `path` en tête, sans doublon, borné à `max_entries`. Écrit
    atomiquement ; une écriture refusée (dossier absent, permissions) reste
    silencieuse pour l'ouverture qu'elle accompagne — les récents sont un
    confort, pas une condition d'ouverture. Sans `last_step`, celui déjà retenu
    pour ce dossier est conservé."""
    resolved = path.resolve()
    kept = [r for r in load(prefs_path) if r.path != resolved]
    old = next((r.last_step for r in load(prefs_path) if r.path == resolved), None)
    updated = (Recent(resolved, _now(), last_step or old), *kept)[:max_entries]
    try:
        prefs_path.parent.mkdir(parents=True, exist_ok=True)
        storage.write_atomic_text(prefs_path, _dump(updated, load_root(prefs_path)))
    except OSError:
        pass
    return updated


def _dump(entries: tuple[Recent, ...], root: Path | None = None) -> str:
    payload: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "recents": [
            {"path": str(r.path), "last_opened_at": r.last_opened_at,
             **({"last_step": r.last_step} if r.last_step else {})} for r in entries
        ],
    }
    if root is not None:
        payload["root_path"] = str(root)
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
