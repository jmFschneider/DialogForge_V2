"""Lancement d'un sous-processus d'agent : flux bornés, délai dur, arbre terminé.

Un fil par flux : les lire l'un après l'autre bloquerait sur le premier pendant
que le tube du second se remplit, et l'enfant cesserait d'écrire. Chaque flux est
borné à `OUTPUT_LIMIT_BYTES` — constante nommée, sans option (§0.1).

Dépassement, délai ou interruption : terminaison de **l'arbre** de processus,
flux conservés comme preuve partielle, et **aucun `resultat.json`**. Sa présence
est la seule preuve que les flux sont complets, et c'est sur elle que la reprise
conclut sans repayer un appel (CONCEPTION_FINALE.md §5).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import IO, Any

from . import storage

SCHEMA_VERSION = 1
OUTPUT_LIMIT_BYTES = 8 * 1024 * 1024

_CHUNK = 65536
_POLL_SECONDS = 0.02
_GRACE_SECONDS = 5.0


class TransportError(RuntimeError):
    """Le sous-processus n'a pas pu être lancé."""


class Outcome(Enum):
    """Vocabulaire propre au transport ; les trois derniers nomment l'incident."""

    COMPLETED = "COMPLETED"
    OUTPUT_LIMIT = "OUTPUT_LIMIT"
    TIMEOUT = "TIMEOUT"
    INTERRUPTED_BY_USER = "INTERRUPTED_BY_USER"


@dataclass(frozen=True)
class CallResult:
    outcome: Outcome
    return_code: int
    stdout_bytes: int
    stdout_sha256: str
    stderr_bytes: int
    stderr_sha256: str
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """`outcome` n'y figure pas : `resultat.json` n'existe que pour une
        sortie propre, et le nommer y ferait croire à d'autres valeurs."""
        written = {k: v for k, v in asdict(self).items() if k != "outcome"}
        return {"schema_version": SCHEMA_VERSION, **written}


_RESULT_TYPES: dict[str, type | tuple[type, ...]] = {
    "schema_version": int,
    "return_code": int,
    "stdout_bytes": int,
    "stdout_sha256": str,
    "stderr_bytes": int,
    "stderr_sha256": str,
    "duration_seconds": (int, float),
}


def run(
    command: Sequence[str],
    *,
    cwd: Path,
    call_dir: Path,
    timeout_seconds: float,
    limit_bytes: int = OUTPUT_LIMIT_BYTES,
) -> CallResult:
    """Lance `command` dans `cwd`, écrit ses flux sous `call_dir`, et n'y écrit
    `resultat.json` que si le processus est sorti de lui-même."""
    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            list(command),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=(os.name != "nt"),
        )
    except OSError as exc:
        raise TransportError(f"lancement impossible : {exc}") from exc
    # Dès le retour de Popen, pour qu'un humain retrouve un orphelin (§5).
    storage.write_atomic_text(call_dir / "pid.txt", f"{proc.pid}\n")
    assert proc.stdout is not None and proc.stderr is not None
    pumps = (
        _Pump(proc.stdout, call_dir / "stdout.txt", limit_bytes),
        _Pump(proc.stderr, call_dir / "stderr.txt", limit_bytes),
    )
    for pump in pumps:
        pump.start()
    try:
        outcome = _wait(proc, pumps, started + timeout_seconds)
    finally:
        for pump in pumps:
            pump.join(_GRACE_SECONDS)
        if any(pump.is_alive() for pump in pumps):
            # Un descendant tient encore les tubes après la sortie de l'enfant.
            # Sans cette terminaison, `resultat.json` affirmerait « flux
            # complets » sur des fichiers qui grossissent encore.
            _terminate_tree(proc)
            for pump in pumps:
                pump.join(_GRACE_SECONDS)
        proc.stdout.close()
        proc.stderr.close()
    # Un flux peut déborder dans ce qu'il restait à vider après la sortie.
    if outcome is Outcome.COMPLETED and any(p.overflowed for p in pumps):
        _terminate_tree(proc)
        outcome = Outcome.OUTPUT_LIMIT
    result = CallResult(
        outcome=outcome,
        return_code=proc.returncode,
        stdout_bytes=pumps[0].written,
        stdout_sha256=pumps[0].digest.hexdigest(),
        stderr_bytes=pumps[1].written,
        stderr_sha256=pumps[1].digest.hexdigest(),
        duration_seconds=round(time.monotonic() - started, 3),
    )
    if outcome is Outcome.COMPLETED:
        storage.write_atomic_text(
            call_dir / "resultat.json",
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )
    return result


def read_result(call_dir: Path) -> CallResult | None:
    """Relit `resultat.json`. `None` s'il est absent, illisible ou invalide : la
    reprise ne conclut « flux complets » que sur un fichier valide (§5)."""
    try:
        text, _ = storage.read_text(call_dir / "resultat.json")
        raw = json.loads(text)
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or set(raw) != set(_RESULT_TYPES):
        return None
    for key, kind in _RESULT_TYPES.items():
        if not isinstance(raw[key], kind) or isinstance(raw[key], bool):
            return None
    if raw["schema_version"] != SCHEMA_VERSION:
        return None
    fields = {k: raw[k] for k in _RESULT_TYPES if k != "schema_version"}
    fields["duration_seconds"] = float(fields["duration_seconds"])
    return CallResult(outcome=Outcome.COMPLETED, **fields)


def _wait(
    proc: subprocess.Popen[bytes], pumps: tuple[_Pump, ...], deadline: float
) -> Outcome:
    try:
        while True:
            if any(p.overflowed for p in pumps):
                _terminate_tree(proc)
                return Outcome.OUTPUT_LIMIT
            if proc.poll() is not None:
                return Outcome.COMPLETED
            if time.monotonic() >= deadline:
                _terminate_tree(proc)
                return Outcome.TIMEOUT
            time.sleep(_POLL_SECONDS)
    except KeyboardInterrupt:
        _terminate_tree(proc)
        return Outcome.INTERRUPTED_BY_USER


def _terminate_tree(proc: subprocess.Popen[bytes]) -> None:
    """Termine l'enfant **et sa descendance** : une CLI d'agent lance ses propres
    processus, et ne tuer que l'enfant laisserait l'arbre vivant."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:  # branche POSIX écrite, non testée en V0.1 (§0.1)
        # PID négatif = groupe entier ; il vaut le PID de l'enfant grâce à
        # `start_new_session`. Signal 9 en clair : `signal.SIGKILL` n'existe pas
        # sous Windows, et le nommer ferait échouer mypy sur le poste de travail.
        try:
            os.kill(-proc.pid, 9)
        except OSError:
            pass
    proc.kill()
    try:
        proc.wait(timeout=_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass


class _Pump(threading.Thread):
    """Copie un flux dans son fichier au fil de l'eau, borné.

    `os.read` plutôt que le tampon de `Popen` : c'est ce qui rend « au fil de
    l'eau » vrai, et le fichier utilisable comme preuve partielle à tout
    instant."""

    def __init__(self, source: IO[bytes], path: Path, limit: int) -> None:
        super().__init__(daemon=True)
        self._source, self._path, self._limit = source, path, limit
        self.written = 0
        self.overflowed = False
        self.digest = hashlib.sha256()

    def run(self) -> None:
        with open(self._path, "wb") as out:
            while not self.overflowed:
                try:
                    chunk = os.read(self._source.fileno(), _CHUNK)
                except (OSError, ValueError):
                    break
                if not chunk:
                    break
                room = self._limit - self.written
                if len(chunk) > room:
                    chunk, self.overflowed = chunk[:room], True
                out.write(chunk)
                out.flush()
                self.digest.update(chunk)
                self.written += len(chunk)
            os.fsync(out.fileno())
