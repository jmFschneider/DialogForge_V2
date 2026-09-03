"""Faux agent en ligne de commande — un sous-processus Python scripté.

Aucun appel fournisseur, aucun réseau : la suite n'appelle jamais un modèle
payant (`RULES.md`). Le faux agent est néanmoins un **vrai** sous-processus,
parce que c'est justement le comportement de l'OS — deux tubes concurrents,
délai, terminaison d'arbre — que `transport.py` doit tenir. Un objet processus
simulé ne prouverait rien de ce pour quoi ce module existe.

`FakeAdapter` n'arrive qu'avec `adapters/base.py` : le protocole qu'il doit
implémenter n'existe pas encore.
"""

from __future__ import annotations

import sys

_CHILD = (
    "import pathlib, time\n"
    "time.sleep({delay!r})\n"
    "pathlib.Path({marker!r}).write_text('vivant', encoding='utf-8')\n"
)


def command(
    *,
    stdout: str = "",
    stderr: str = "",
    stdout_bytes: int = 0,
    stderr_bytes: int = 0,
    rounds: int = 1,
    exit_code: int = 0,
    sleep_seconds: float = 0.0,
    child_marker: str | None = None,
    child_delay_seconds: float = 2.0,
) -> list[str]:
    """Commande d'un faux agent.

    Il écrit sur les deux flux — `stdout_bytes`/`stderr_bytes` répartis en
    `rounds` tours **alternés**, de quoi bloquer un lecteur qui ne draine qu'un
    tube à la fois —, peut engendrer un petit-fils qui dépose `child_marker`
    après `child_delay_seconds` (la preuve qu'un arbre a survécu, s'il
    apparaît), dort, puis sort avec `exit_code`.

    `stdout_bytes` et `stderr_bytes` doivent être divisibles par `rounds`.
    """
    lines = ["import sys, time"]
    if child_marker is not None:
        child = _CHILD.format(delay=child_delay_seconds, marker=child_marker)
        lines.append(f"import subprocess; subprocess.Popen([sys.executable, '-c', {child!r}])")
    if stdout:
        lines.append(f"sys.stdout.write({stdout!r}); sys.stdout.flush()")
    if stderr:
        lines.append(f"sys.stderr.write({stderr!r}); sys.stderr.flush()")
    if stdout_bytes or stderr_bytes:
        lines.append(f"for _ in range({rounds}):")
        lines.append(f"    sys.stdout.write('x' * {stdout_bytes // rounds}); sys.stdout.flush()")
        lines.append(f"    sys.stderr.write('y' * {stderr_bytes // rounds}); sys.stderr.flush()")
    if sleep_seconds:
        lines.append(f"time.sleep({sleep_seconds!r})")
    lines.append(f"sys.exit({exit_code})")
    return [sys.executable, "-c", "\n".join(lines)]
