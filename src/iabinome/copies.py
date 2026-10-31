"""Copies complètes des missions locales aux pauses humaines et à la clôture.

La copie est un envoi de confort vers un dossier synchronisé. Le dossier local
reste la seule source de travail ; une erreur d'envoi ne change jamais la
décision ou l'état de la collaboration.
"""

from __future__ import annotations

import shutil
import tomllib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import mission
from .models import State, Status

CONFIG_PATH = Path.home() / ".dialogforge" / "copies.toml"
_HUMAN_PAUSES = {Status.WAITING_HUMAN, Status.AWAITING_APPROVAL}


class CopyError(RuntimeError):
    """La copie a échoué ; la mission locale reste utilisable."""


@dataclass(frozen=True)
class CopyConfig:
    local_root: Path
    nextcloud_root: Path


def load_config(path: Path | None = None) -> CopyConfig | None:
    """Configuration opérationnelle commune à la CLI et à la GUI."""
    path = path or CONFIG_PATH
    if not path.is_file():
        return None
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
        if set(raw) != {"local_root", "nextcloud_root"}:
            raise ValueError("clés attendues : local_root et nextcloud_root")
        local, cloud = (Path(raw[key]).expanduser() for key in ("local_root", "nextcloud_root"))
        if not local.is_absolute() or not cloud.is_absolute():
            raise ValueError("les deux chemins doivent être absolus")
        local, cloud = local.resolve(), cloud.resolve()
        if local == cloud or local.is_relative_to(cloud) or cloud.is_relative_to(local):
            raise ValueError("les dossiers local et Nextcloud doivent être séparés")
        return CopyConfig(local, cloud)
    except (OSError, ValueError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise CopyError(f"configuration des copies {path} : {exc}") from exc


def after_run(path: Path, state: State) -> Path | None:
    """Envoie la mission entière lorsqu'une question ou validation attend l'humain."""
    if state.status not in _HUMAN_PAUSES:
        return None
    return send(path, state.status.value.lower(), outside_is_skip=True)


def after_decision(path: Path) -> Path | None:
    """Envoie de nouveau toute la mission, décision finale incluse."""
    return send(path, "final", outside_is_skip=True)


def send(path: Path, moment: str, *, outside_is_skip: bool = False) -> Path | None:
    config = load_config()
    if config is None:
        return None
    try:
        source = (mission.root_of(path) or path).resolve()
    except mission.MissionError as exc:
        raise CopyError(f"mission illisible : {exc}") from exc
    if not source.is_relative_to(config.local_root):
        if outside_is_skip:
            return None
        raise CopyError(f"mission hors du dossier local configuré : {source}")
    if not source.is_dir():
        raise CopyError(f"mission introuvable : {source}")
    name = f"{source.name}__{moment}__{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
    target = config.nextcloud_root / name
    try:
        config.nextcloud_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        (target / "COPIE_TERMINEE.txt").write_text(
            f"Copie complète de {source} le {datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}.\n",
            encoding="utf-8",
        )
    except (OSError, shutil.Error) as exc:
        raise CopyError(f"copie Nextcloud échouée ({target}) : {exc}") from exc
    return target
