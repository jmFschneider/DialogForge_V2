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
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import IO, Any

from . import storage
from .models import IntegrityError, positive_seconds

SCHEMA_VERSION = 1
OUTPUT_LIMIT_BYTES = 8 * 1024 * 1024

_CHUNK = 65536
_POLL_SECONDS = 0.02
_GRACE_SECONDS = 5.0
_TERMINATE_WAIT_SECONDS = 2.0

# Borne **tenue** de la phase de nettoyage : deux échéances communes encadrant
# la tentative de terminaison. Elle est annoncée parce qu'elle est mesurée — la
# version précédente accordait `_GRACE_SECONDS` à chaque pompe, deux fois, plus
# l'attente de `_terminate_tree` : un descendant tenant les tubes 22 s faisait
# rendre `run()` après 22,11 s, en annonçant `COMPLETED` (D-7).
CLEANUP_LIMIT_SECONDS = 2 * _GRACE_SECONDS + _TERMINATE_WAIT_SECONDS


class TransportError(RuntimeError):
    """Le sous-processus n'a pas pu être lancé."""


@dataclass(frozen=True)
class ExecutionControl:
    """La commande d'une exécution depuis l'extérieur, **partagée par la CLI et la
    GUI** (`conception/GUI_V1.md` §9.1). Deux demandes, rien d'autre :

    - `pause_requested` : l'appel en cours se termine, le cycle s'arrête à la
      frontière d'appel, en `READY` — rien n'est perdu ;
    - `interrupt_requested` : l'appel en cours est interrompu tout de suite
      (`INTERRUPTED_BY_USER`, possiblement payé), et aucun autre ne part.

    Des `Event` parce qu'une GUI les pose depuis un autre fil que celui du moteur,
    que `KeyboardInterrupt` n'atteint pas. Ni statut, ni preuve, ni règle de
    reprise ne changent : ce sont les mêmes arrêts, commandés explicitement.
    """

    pause_requested: threading.Event = field(default_factory=threading.Event)
    interrupt_requested: threading.Event = field(default_factory=threading.Event)

    def stopping(self) -> bool:
        return self.pause_requested.is_set() or self.interrupt_requested.is_set()


class Outcome(Enum):
    """Vocabulaire propre au transport ; les trois derniers nomment l'incident."""

    COMPLETED = "COMPLETED"
    OUTPUT_LIMIT = "OUTPUT_LIMIT"
    TIMEOUT = "TIMEOUT"
    INTERRUPTED_BY_USER = "INTERRUPTED_BY_USER"
    STREAMS_UNCLOSED = "STREAMS_UNCLOSED"
    STREAM_FAILED = "STREAM_FAILED"


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
    stdin_text: str | None = None,
    limit_bytes: int = OUTPUT_LIMIT_BYTES,
    env: Mapping[str, str] | None = None,
    control: ExecutionControl | None = None,
) -> CallResult:
    """Lance `command` dans `cwd`, écrit ses flux sous `call_dir`, et n'y écrit
    `resultat.json` que si le processus est sorti de lui-même.

    `stdin_text` est le chemin par lequel le prompt arrive. Mesuré le
    2026-09-03 : un prompt en argument de ligne de commande buterait sur la
    limite de 32 767 caractères de `CreateProcess` dès qu'un document réel y
    passe, et une CLI voyant `DEVNULL` sur son entrée la lit comme un flux
    canalisé vide, ce qui dégrade sa réponse.

    `env` remplace l'environnement hérité (2.2) ; absent, le sous-processus hérite
    de celui du parent, comme avant.

    `control.interrupt_requested` est surveillé pendant l'attente, comme le délai :
    posé, il termine l'arbre et rend `INTERRUPTED_BY_USER`.
    """
    # Validé avant `Popen` : avec `nan`, `time.monotonic() >= deadline` reste
    # faux et le délai dur ne se déclencherait jamais (C-08).
    timeout_seconds = positive_seconds(timeout_seconds)
    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=None if env is None else dict(env),
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=(os.name != "nt"),
        )
    except OSError as exc:
        raise TransportError(f"lancement impossible : {exc}") from exc
    if stdin_text is not None:
        assert proc.stdin is not None
        # Dans un fil : un prompt plus gros que le tube bloquerait ici, pendant
        # que personne ne draine encore stdout.
        threading.Thread(
            target=_feed, args=(proc.stdin, stdin_text.encode("utf-8")), daemon=True
        ).start()
    # Dès le retour de Popen, pour qu'un humain retrouve **l'enfant tant qu'il
    # vit**. Ce n'est pas le moyen de retrouver un orphelin : dans ce
    # scénario-là, c'est justement ce PID qui est mort, et sa descendance qui
    # survit (D-7).
    storage.write_atomic_text(call_dir / "pid.txt", f"{proc.pid}\n")
    assert proc.stdout is not None and proc.stderr is not None
    pumps = (
        _Pump(proc.stdout, call_dir / "stdout.txt", limit_bytes),
        _Pump(proc.stderr, call_dir / "stderr.txt", limit_bytes),
    )
    for pump in pumps:
        pump.start()
    unclosed = False
    try:
        outcome = _wait(proc, pumps, started + timeout_seconds, control)
    finally:
        unclosed = _drain(proc, pumps)
    # Un flux peut déborder dans ce qu'il restait à vider après la sortie.
    if outcome is Outcome.COMPLETED and any(p.overflowed for p in pumps):
        _terminate_tree(proc)
        outcome = Outcome.OUTPUT_LIMIT
    if unclosed:
        # On ne sait pas si les flux sont complets, donc on ne l'écrit pas.
        outcome = Outcome.STREAMS_UNCLOSED
    if any(pump.failed for pump in pumps):
        # Une pompe qui a rendu la main sur une erreur ne distingue pas la fin
        # du flux d'une lecture interrompue : ce qu'elle a écrit peut être un
        # préfixe. Publier `resultat.json` en présenterait l'empreinte comme
        # celle d'un flux complet — exactement ce que sa présence promet.
        outcome = Outcome.STREAM_FAILED
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


def _drain(proc: subprocess.Popen[bytes], pumps: tuple[_Pump, ...]) -> bool:
    """Clôt la phase de nettoyage sous une borne tenue, et dit si un flux est
    resté ouvert.

    Deux **échéances absolues communes**, jamais un délai plein par pompe : la
    version précédente accordait `_GRACE_SECONDS` à chacune, deux fois, plus
    l'attente de `_terminate_tree`, et la phase durait bien plus que sa borne
    annoncée — sans changer l'issue.

    Les descripteurs ne sont **pas fermés tant qu'une pompe lit encore** :
    fermer sous un lecteur vivant n'accélère rien, et peut bloquer le
    coordinateur. Le descripteur et le fil démon vivent alors jusqu'à la fin
    réelle du descendant.
    """
    if _joined_before(pumps, time.monotonic() + _GRACE_SECONDS):
        _close(proc)
        return False
    # Un descendant tient encore les tubes après la sortie de l'enfant.
    _terminate_tree(proc)
    if _joined_before(pumps, time.monotonic() + _GRACE_SECONDS):
        _close(proc)
        return False
    return True


def _joined_before(pumps: tuple[_Pump, ...], deadline: float) -> bool:
    for pump in pumps:
        pump.join(max(0.0, deadline - time.monotonic()))
    return not any(pump.is_alive() for pump in pumps)


def _close(proc: subprocess.Popen[bytes]) -> None:
    for stream in (proc.stdout, proc.stderr):
        if stream is not None:
            stream.close()


def read_result(call_dir: Path) -> CallResult | None:
    """Relit `resultat.json` **et le confronte aux flux**.

    `None` s'il est absent, illisible ou invalide : il n'y a alors *pas de
    preuve*, et l'appel est possiblement payé. S'il est valide mais que les flux
    le contredisent — taille ou empreinte différente, fichier disparu —, c'est
    une *preuve contredite* : `IntegrityError`. Les deux rendent la main à
    l'humain, jamais avec le même diagnostic (§5).
    """
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
    result = CallResult(outcome=Outcome.COMPLETED, **fields)
    _check_stream(call_dir / "stdout.txt", result.stdout_bytes, result.stdout_sha256)
    _check_stream(call_dir / "stderr.txt", result.stderr_bytes, result.stderr_sha256)
    return result


def _check_stream(path: Path, size: int, digest: str) -> None:
    """Un flux absent alors que `resultat.json` existe est une **divergence**,
    pas une erreur d'entrée-sortie : le fichier affirmait que ce flux était
    complet."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise IntegrityError(
            f"{path.name} absent alors que resultat.json affirme {size} octets"
        ) from exc
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise IntegrityError(f"{path.name} ne correspond plus a resultat.json")


def _wait(
    proc: subprocess.Popen[bytes], pumps: tuple[_Pump, ...], deadline: float,
    control: ExecutionControl | None,
) -> Outcome:
    try:
        while True:
            if control is not None and control.interrupt_requested.is_set():
                _terminate_tree(proc)
                return Outcome.INTERRUPTED_BY_USER
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
        # Filet, pas un second modèle : un Ctrl+C brut (moteur importé sans la CLI,
        # qui, elle, passe par `ExecutionControl`) ne doit jamais laisser l'arbre vivant.
        _terminate_tree(proc)
        return Outcome.INTERRUPTED_BY_USER


def _feed(pipe: IO[bytes], data: bytes) -> None:
    """Écrit le prompt puis ferme : sans la fermeture, la CLI attend une fin de
    flux qui ne vient jamais, et le délai dur devient la seule sortie."""
    try:
        pipe.write(data)
        pipe.flush()
    except OSError:
        pass
    finally:
        pipe.close()


def _terminate_tree(proc: subprocess.Popen[bytes]) -> None:
    """Termine l'enfant **et sa descendance** : une CLI d'agent lance ses propres
    processus, et ne tuer que l'enfant laisserait l'arbre vivant."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=_TERMINATE_WAIT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            pass  # la borne de nettoyage prime sur la réussite de la terminaison
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
        proc.wait(timeout=_TERMINATE_WAIT_SECONDS)
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
        self.failed = False
        self.digest = hashlib.sha256()

    def run(self) -> None:
        """Une erreur est **signalée**, jamais confondue avec une fin de flux.

        `os.read` rend `b""` à la fin du flux et lève sur une lecture rompue :
        sortir de la boucle dans les deux cas rendait les deux issues
        indistinguables, et le préfixe déjà copié passait pour la réponse
        entière. Une écriture ou un `fsync` en échec comptent pareil — le
        fichier ne vaut alors pas ce que son empreinte affirme.
        """
        try:
            with open(self._path, "wb") as out:
                while not self.overflowed:
                    try:
                        chunk = os.read(self._source.fileno(), _CHUNK)
                    except (OSError, ValueError):
                        self.failed = True
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
        except OSError:
            self.failed = True
