"""Instantané de corpus : manifeste, copie, règles de chemin.

Refusés avant copie : chemin absolu, `..`, lien sortant, fichier non
régulier, empreinte qui change pendant la copie. Le manifeste reçoit des
fichiers exacts, un par ligne — ni glob, ni découverte (CONCEPTION_FINALE.md §3).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import storage

SCHEMA_VERSION = 1


class CorpusError(ValueError):
    """Un fichier du corpus est refusé avant toute publication."""


@dataclass(frozen=True)
class ManifestEntry:
    logical_path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    captured_at: str
    origin_label: str
    entries: tuple[ManifestEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "captured_at": self.captured_at,
            "origin_label": self.origin_label,
            "files": [
                {"chemin": e.logical_path, "taille": e.size, "sha256": e.sha256}
                for e in self.entries
            ],
        }


_MANIFEST_KEYS = {"schema_version", "captured_at", "origin_label", "files"}
_ENTRY_KEYS = {"chemin", "taille", "sha256"}


def read_manifest(path: Path) -> Manifest:
    """Lecture **stricte**, symétrique de `Manifest.to_dict`.

    Clés exactes, types exacts, version connue, chemins logiques soumis aux
    mêmes refus qu'à la copie. Un manifeste au schéma cassé est un refus, jamais
    une lecture partielle : c'est lui qui sert de référence pour dire si le
    corpus a bougé, et une référence à moitié lue ne prouve rien.
    """
    text, _ = storage.read_text(path)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CorpusError(f"manifeste illisible : {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != _MANIFEST_KEYS:
        raise CorpusError("manifeste : schéma inattendu")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise CorpusError(f"manifeste : version {raw['schema_version']!r} inconnue")
    for key in ("captured_at", "origin_label"):
        if not isinstance(raw[key], str):
            raise CorpusError(f"manifeste : {key} chaîne attendue")
    if not isinstance(raw["files"], list):
        raise CorpusError("manifeste : files liste attendue")
    return Manifest(
        schema_version=SCHEMA_VERSION,
        captured_at=raw["captured_at"],
        origin_label=raw["origin_label"],
        entries=tuple(_read_entry(item) for item in raw["files"]),
    )


def _read_entry(raw: Any) -> ManifestEntry:
    if not isinstance(raw, dict) or set(raw) != _ENTRY_KEYS:
        raise CorpusError("manifeste : entrée au schéma inattendu")
    logical_path, size, digest = raw["chemin"], raw["taille"], raw["sha256"]
    if not isinstance(logical_path, str) or not isinstance(digest, str):
        raise CorpusError("manifeste : chemin et sha256 chaînes attendues")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise CorpusError("manifeste : taille entier positif attendu")
    # Mêmes refus qu'à la copie : un manifeste fabriqué ne doit pas pouvoir
    # faire lire un fichier hors du dossier de corpus.
    _check_logical_path(logical_path)
    return ManifestEntry(logical_path=logical_path, size=size, sha256=digest)


def build(
    source_root: Path, source_list: Path, destination: Path, origin_label: str
) -> Manifest:
    """Copie vers `destination/fichiers/...` chaque chemin listé dans
    `source_list` (un par ligne, relatif à `source_root`), écrit
    `destination/manifeste.json`, et retourne le manifeste."""
    try:
        root = source_root.resolve(strict=True)
    except OSError as exc:
        raise CorpusError(f"racine introuvable : {source_root} ({exc})") from exc
    fichiers_dir = destination / "fichiers"
    entries = [_copy_one(root, p, fichiers_dir) for p in _read_list(source_list)]
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        captured_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        origin_label=origin_label,
        entries=tuple(entries),
    )
    payload = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n"
    storage.write_atomic_text(destination / "manifeste.json", payload)
    return manifest


def _copy_one(root: Path, logical_path: str, fichiers_dir: Path) -> ManifestEntry:
    _check_logical_path(logical_path)
    source = root / logical_path
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        raise CorpusError(f"{logical_path}: introuvable ({exc})") from exc
    if not resolved.is_relative_to(root):
        raise CorpusError(f"{logical_path}: lien sortant hors de la racine")
    if not resolved.is_file():
        raise CorpusError(f"{logical_path}: fichier non régulier")
    data = resolved.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    dest_path = fichiers_dir / logical_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_bytes(dest_path, data)
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != digest:
        dest_path.unlink(missing_ok=True)
        raise CorpusError(f"{logical_path}: empreinte changeante pendant la copie")
    return ManifestEntry(logical_path=logical_path, size=len(data), sha256=digest)


def _check_logical_path(logical_path: str) -> None:
    p = Path(logical_path)
    if p.is_absolute():
        raise CorpusError(f"{logical_path}: chemin absolu refusé")
    if ".." in p.parts:
        raise CorpusError(f"{logical_path}: '..' refusé")


def _read_list(source_list: Path) -> list[str]:
    text, _ = storage.read_text(source_list)
    return [line.strip() for line in text.splitlines() if line.strip()]
