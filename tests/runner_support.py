"""Aides des tests du Runner : identité Git isolée, conception acceptée, faux agent et pont de test.

Aucun appel fournisseur : l'agent est un petit script Python et le pont de test rejoue le vrai
protocole de `gui_bridge` en profil local, sans WSL.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

from iabinome import decisions, workflow
from tests import fakes

OWNER = ("Test Owner", "owner@example.invalid")
BRIDGE = Path(__file__).resolve().parent / "runner_bridge.py"
AGENT = """\
import os, pathlib, subprocess, sys
sys.stdin.read()
mode = os.environ.get("RUNNER_TEST_MODE", "ok")
log = pathlib.Path(os.environ["RUNNER_TEST_LOG"])
log.open("a").write("appel\\n")
calls = len(log.read_text().splitlines())
if mode == "fail":
    raise SystemExit(7)
if mode == "auth":
    print("Failed to authenticate. API Error: 401 OAuth access token is invalid.")
    raise SystemExit(1)
if mode == "noop":
    print("Aucune correction nécessaire\\nRUNNER: CANDIDAT")
    raise SystemExit(0)
if mode == "illisible":
    print("Tout est fait.")
    raise SystemExit(0)
if mode == "intervention" or mode == "puis-intervention" and calls > 1:
    print("Quel navigateur faut-il viser ?\\nRUNNER: INTERVENTION")
    raise SystemExit(0)
if mode == "toujours-reste" or mode == "reste" and calls == 1:
    print("Une partie reste à écrire.\\nRUNNER: RESTE")
    raise SystemExit(0)
content = ("mauvais\\n" if mode == "repair" and calls == 1 else
           "amélioré\\n" if mode == "improve" else "resultat de l'agent\\n")
path = pathlib.Path("app.txt")
if not path.exists() or path.read_text() != content:
    path.write_text(content)
    subprocess.run(["git", "add", "app.txt"], check=True)
    subprocess.run(["git", "commit", "-qm", "candidat de l'agent"], check=True)
print("Bilan : lancer avec python app.txt\\nRUNNER: CANDIDAT")
"""


def direct_bundle(found: Any, remote: str, package_id: str) -> Path:
    """Le transport du bundle sans `wsl.localhost` : le Runner de test est déjà local."""
    from dialogforge_runner import core

    return core.bundle_candidate(Path(found.data["run"]), Path(remote), package_id)


def local_delivery() -> list[Any]:
    """Remise réelle dans `code/` avec des chemins de run natifs (pas de WSL sous Windows)."""
    return [
        mock.patch("iabinome.delivery._bundle", side_effect=direct_bundle),
        mock.patch("iabinome.delivery._source_path",
                   side_effect=lambda data, package, distro: Path(package)),
    ]


@contextmanager
def git_home(root: Path, identity: tuple[str, str] | None = OWNER) -> Iterator[Path]:
    """Une configuration Git globale jetable : l'identité vient de là, jamais d'un `-c`."""
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    lines = ["[commit]", "\tgpgsign = false", "[init]", "\tdefaultBranch = main"]
    if identity is not None:
        lines += ["[user]", f"\tname = {identity[0]}", f"\temail = {identity[1]}"]
    (home / ".gitconfig").write_text("\n".join(lines) + "\n", encoding="utf-8")
    environment = {"HOME": str(home), "USERPROFILE": str(home), "XDG_CONFIG_HOME": str(home / "x")}
    with mock.patch.dict(os.environ, environment):
        yield home


def git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True, env=env,
    )
    return result.stdout.decode("utf-8", "replace").strip()


def accepted_conception(root: Path, *, open_finding: bool = False) -> Path:
    """Une conception acceptée avec réserves, éventuellement avec un constat resté ouvert."""
    collab = fakes.collaboration(root, max_revisions=0)
    verdict = fakes.review("REVISER") if open_finding else fakes.review("ACCEPTER")
    adapters = {
        "fake-a": fakes.FakeAdapter(
            "fake-a", ("IABINOME:DOCUMENT\n# Plan\nvalidations : node --test\n",),
        ),
        "fake-b": fakes.FakeAdapter("fake-b", (verdict,)),
    }
    workflow.run(collab, adapters=adapters, timeout_seconds=30)
    workflow.decide(
        collab, decisions.ACCEPTED_WITH_RESERVES, reserves="recette à rendre reproductible",
    )
    return collab
