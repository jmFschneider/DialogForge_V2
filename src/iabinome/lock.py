"""Verrou de collaboration : PID, date UTC, commande.

Un détenteur vivant refuse l'acquisition. Un verrou mort — PID qui n'existe
plus — est récupéré. **Jamais** la suppression du verrou d'un autre : la
libération relit le fichier et vérifie que le PID est le nôtre avant
d'effacer (CONCEPTION_FINALE.md §5, §10).
"""

from __future__ import annotations

import ctypes
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import storage

_LOCK_KEYS = {"pid", "acquired_at", "command"}
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class LockError(RuntimeError):
    """Verrou illisible, ou suppression refusée car détenu par un autre PID."""


class LockHeld(LockError):
    """Le verrou est détenu par un processus vivant."""


@dataclass(frozen=True)
class LockHolder:
    pid: int
    acquired_at: str
    command: str


@contextmanager
def acquire(path: Path, command: str) -> Iterator[None]:
    """Acquiert le verrou, récupérant un verrou mort au besoin. Le libère à
    la sortie normale — jamais garanti après un arrêt brutal, ce que la
    récupération de verrou mort existe pour couvrir au prochain lancement."""
    _try_acquire(path, command)
    try:
        yield
    finally:
        _release(path)


def _try_acquire(path: Path, command: str) -> None:
    if path.exists():
        holder = _read(path)
        if _is_pid_alive(holder.pid):
            raise LockHeld(
                f"verrou détenu par le PID {holder.pid} depuis {holder.acquired_at}"
            )
    payload = {
        "pid": os.getpid(),
        "acquired_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
    }
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False) + "\n")


def _release(path: Path) -> None:
    if not path.exists():
        return
    holder = _read(path)
    if holder.pid != os.getpid():
        raise LockError("refus de supprimer le verrou d'un autre détenteur")
    path.unlink()


def _read(path: Path) -> LockHolder:
    text, _ = storage.read_text(path)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LockError(f"verrou illisible : {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != _LOCK_KEYS:
        raise LockError("verrou.json : schéma inattendu")
    pid, acquired_at, command = raw["pid"], raw["acquired_at"], raw["command"]
    if not isinstance(pid, int) or isinstance(pid, bool):
        raise LockError("verrou.json : pid entier attendu")
    if not isinstance(acquired_at, str) or not isinstance(command, str):
        raise LockError("verrou.json : champs chaîne attendus")
    return LockHolder(pid=pid, acquired_at=acquired_at, command=command)


def _is_pid_alive(pid: int) -> bool:
    if os.name == "nt":
        handle = ctypes.windll.kernel32.OpenProcess(
            _PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if handle == 0:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
