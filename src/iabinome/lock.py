"""Verrou de collaboration : identifiant, PID, date UTC, commande.

**L'acquisition est une création exclusive** — `O_CREAT | O_EXCL` —, jamais un
test d'existence suivi d'une écriture : deux processus franchiraient le test
avant que l'un publie, et entreraient tous les deux.

Un détenteur vivant refuse l'acquisition. Un verrou mort — PID qui n'existe
plus — est récupéré, mais **sous jeton de récupération** : le droit d'effacer
s'obtient en créant exclusivement un fichier voisin, jamais en effaçant
directement. Sans ce jeton, deux candidats qui lisent le même verrou mort
pourraient effacer, pour le second, le verrou tout neuf du premier.

**Jamais la suppression du verrou d'un autre** : la libération relit le fichier
et compare le `lock_id`, pas seulement le PID — une seconde acquisition du même
processus ou un verrou remplacé ne doivent pas autoriser la suppression
(CONCEPTION_FINALE.md §5, §10).
"""

from __future__ import annotations

import ctypes
import json
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import storage

_LOCK_KEYS = {"lock_id", "pid", "acquired_at", "command"}
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
# Absent de POSIX : le nommer en clair ferait échouer mypy hors Windows, et la
# plateforme testée est Windows (RULES.md).
_BINARY = getattr(os, "O_BINARY", 0)

_A_LA_MAIN = (
    "supprimer {nom} à la main si aucune commande ne tourne sur cette collaboration"
)


class LockError(RuntimeError):
    """Verrou illisible, ou suppression refusée car détenu par un autre."""


class LockHeld(LockError):
    """Le verrou est détenu par un processus vivant, ou sa récupération l'est."""


@dataclass(frozen=True)
class LockHolder:
    lock_id: str
    pid: int
    acquired_at: str
    command: str


@contextmanager
def acquire(path: Path, command: str) -> Iterator[None]:
    """Acquiert le verrou, récupérant un verrou mort au besoin. Le libère à la
    sortie normale — jamais garanti après un arrêt brutal, ce que la
    récupération de verrou mort couvre au prochain lancement.

    **Une exception, et une seule** : un arrêt survenu entre la création
    exclusive du fichier et l'écriture de son contenu laisse un verrou illisible,
    qu'aucune récupération automatique ne reprend. Le refuser est délibéré —
    récupérer un verrou illisible reviendrait à effacer celui d'un détenteur
    vivant surpris dans cette même fenêtre, échangeant un blocage visible contre
    deux détenteurs simultanés. Le message d'erreur nomme le fichier à
    supprimer.
    """
    holder = _acquire(path, command)
    try:
        yield
    except BaseException as cause:
        # La cause première prime : un échec de libération y est **annoté**,
        # jamais substitué — sinon l'erreur rendue à l'humain serait le
        # symptôme, et la panne d'origine disparaîtrait.
        try:
            _release(path, holder)
        except LockError as exc:
            cause.add_note(f"verrou non libéré : {exc}")
        raise
    _release(path, holder)


def _acquire(path: Path, command: str) -> LockHolder:
    holder = LockHolder(
        lock_id=uuid.uuid4().hex,
        pid=os.getpid(),
        acquired_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        command=command,
    )
    payload = (json.dumps(asdict(holder), ensure_ascii=False) + "\n").encode("utf-8")
    if _create_exclusive(path, payload):
        return holder
    dead = _read(path)
    if _is_pid_alive(dead.pid):
        raise LockHeld(f"verrou détenu par le PID {dead.pid} depuis {dead.acquired_at}")
    _reclaim(path, dead)
    if _create_exclusive(path, payload):
        return holder
    raise LockHeld(f"verrou repris par le PID {_read(path).pid} pendant la récupération")


def _create_exclusive(path: Path, payload: bytes) -> bool:
    """`O_EXCL` est la seule opération qui décide « créer si absent » sans
    fenêtre entre le test et l'écriture. Rend `False` si le fichier existe."""
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | _BINARY, 0o644)
    except FileExistsError:
        return False
    with os.fdopen(fd, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    return True


def _reclaim(path: Path, dead: LockHolder) -> None:
    """Efface un verrou mort, sous jeton et après relecture.

    Le jeton — création exclusive d'un fichier voisin — désigne un seul
    récupérateur ; la relecture garantit qu'on efface bien le verrou mort qu'on
    avait lu, et pas celui qu'un autre vient de publier entre-temps. Aucune
    autre voie ne supprime `verrou.json`, donc aucun verrou vivant ne peut
    disparaître ici.
    """
    claim = path.with_name(f"{path.name}.recuperation")
    token = json.dumps(
        {"pid": os.getpid(), "recupere": dead.lock_id}, ensure_ascii=False
    ) + "\n"
    if not _create_exclusive(claim, token.encode("utf-8")):
        raise LockHeld(
            f"récupération du verrou mort déjà en cours ({claim.name}) ;"
            " supprimer ce fichier à la main si aucune commande ne tourne"
        )
    try:
        try:
            current = _read(path)
        except OSError:
            return  # déjà disparu : plus rien à récupérer
        if current.lock_id == dead.lock_id:
            path.unlink(missing_ok=True)
    finally:
        claim.unlink(missing_ok=True)


def _release(path: Path, holder: LockHolder) -> None:
    if not path.exists():
        return
    if _read(path).lock_id != holder.lock_id:
        raise LockError("refus de supprimer le verrou d'un autre détenteur")
    path.unlink()


def _read(path: Path) -> LockHolder:
    text, _ = storage.read_text(path)
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        # Cas connu et non récupérable automatiquement : un arrêt entre la
        # création exclusive et l'écriture du porteur. Le message doit donc
        # dire quoi faire, faute de quoi la collaboration paraît perdue.
        raise LockError(
            f"{path.name} illisible ({exc}) — {_A_LA_MAIN.format(nom=path.name)}"
        ) from exc
    if not isinstance(raw, dict) or set(raw) != _LOCK_KEYS:
        raise LockError(f"{path.name} : schéma inattendu — {_A_LA_MAIN.format(nom=path.name)}")
    pid = raw["pid"]
    if not isinstance(pid, int) or isinstance(pid, bool):
        raise LockError("verrou.json : pid entier attendu")
    for key in ("lock_id", "acquired_at", "command"):
        if not isinstance(raw[key], str):
            raise LockError(f"verrou.json : {key} chaîne attendue")
    return LockHolder(
        lock_id=raw["lock_id"], pid=pid,
        acquired_at=raw["acquired_at"], command=raw["command"],
    )


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
