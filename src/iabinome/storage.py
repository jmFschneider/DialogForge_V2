"""Écriture atomique : temporaire unique, flush, fsync, os.replace.

UTF-8 sans BOM, fins de ligne `\\n` — écriture en mode binaire, jamais de
traduction de fin de ligne du mode texte. `fsync` du dossier sous POSIX ;
nouvelle tentative brève sous Windows, où `os.replace` peut échouer
transitoirement (antivirus, indexeur). L'atomicité de publication n'est pas
la durabilité — rien de plus n'est promis (CONCEPTION_FINALE.md §5).
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

_BOM = b"\xef\xbb\xbf"
_WINDOWS_REPLACE_RETRIES = 5
_WINDOWS_REPLACE_DELAY_SECONDS = 0.05


def read_text(path: Path) -> tuple[str, bool]:
    """Lit un fichier UTF-8. Un BOM en tête est toléré et retiré ; le second
    élément du tuple le signale, pour que l'appelant le consigne comme
    transformation."""
    raw = path.read_bytes()
    had_bom = raw.startswith(_BOM)
    if had_bom:
        raw = raw[len(_BOM):]
    return raw.decode("utf-8"), had_bom


def write_atomic_text(path: Path, text: str) -> None:
    write_atomic_bytes(path, text.encode("utf-8"))


def write_atomic_bytes(path: Path, data: bytes) -> None:
    parent = path.parent
    fd, tmp_name = tempfile.mkstemp(dir=parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        _replace_with_retry(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    _fsync_dir(parent)


def _replace_with_retry(src: Path, dst: Path) -> None:
    if os.name != "nt":
        os.replace(src, dst)
        return
    last_error: OSError | None = None
    for attempt in range(_WINDOWS_REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(_WINDOWS_REPLACE_DELAY_SECONDS * (attempt + 1))
    assert last_error is not None
    raise last_error


def _fsync_dir(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
