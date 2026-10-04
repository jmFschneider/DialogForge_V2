"""Remise locale d'un candidat Runner dans `code/`, puis acceptation du commit essayé
(`conception/RUNNER_AGENT_UNIQUE.md` §6-§7).

Le paquet, trace interne, et son bundle sont conservés dans `developpement/` ; le commit est extrait
sur une branche candidate de l'espace d'essai. Accepter avance la branche cible en fast-forward
seulement et laisse un reçu dans `developpement/integrations/`. Ni jeton, ni appel d'agent ; rien
n'est écrasé : une modification de l'utilisateur arrête la remise avec son explication.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from dialogforge_runner.core import bundle_ref

from . import development, executions, storage

BRANCH = "dialogforge/candidat-"


@dataclass(frozen=True)
class Delivered:
    """La version présente dans l'espace d'essai, lue sur Git et sur le paquet conservé."""

    code: Path
    branch: str
    package: Path
    base: str
    head: str
    target: Path
    target_branch: str
    accepted: bool


def _source_path(data: dict[str, Any], package: str, distro: str | None) -> Path:
    run = PurePosixPath(data["run"])
    source = PurePosixPath(package)
    if (not run.is_absolute() or not source.is_absolute() or ".." in source.parts
            or source.parent.parent != run / "results"
            or not source.parent.name.startswith("collect-") or source.name != "package"):
        raise ValueError("chemin du paquet étranger au dossier Runner")
    return _wsl_path(source, distro)


def _wsl_path(source: PurePosixPath, distro: str | None) -> Path:
    if not source.is_absolute() or ".." in source.parts:
        raise ValueError("chemin Linux invalide")
    if os.name != "nt":
        return Path(str(source))
    if not distro or any(c in distro for c in "\\/:\n\r"):
        raise ValueError("distribution WSL du paquet inconnue")
    return Path("\\\\wsl.localhost\\" + distro + "\\" + "\\".join(source.parts[1:]))


def receive_package(
    collab: Path, found: executions.Found, state: dict[str, Any], *,
    source: Path | None = None,
) -> Path:
    """Copie le dernier paquet valide, vérifié avant et après publication ; reprise idempotente."""
    if found.reference is None or found.data is None:
        raise ValueError("aucune exécution Runner enregistrée")
    package = state.get("package")
    if state.get("locked") or not isinstance(package, str):
        raise ValueError("attendre un paquet Runner valide, sans exécution en cours")
    if package not in found.data["paquets"]:
        raise ValueError("le paquet n'appartient pas à cette exécution")
    source = source or _source_path(found.data, package, found.data["wsl"]["distribution"])
    files, metadata = development.read_package(source)
    if (metadata["identity"]["base_oid"] != found.data["projet"]["base_oid"]
            or found.export is None or {
                name[7:]: value for name, value in files.items() if name.startswith("export/")
            } != development._tree(found.export)):
        raise ValueError("le paquet ne correspond pas à la base et à l'export de cette exécution")
    folder = found.dev / "paquets"
    for prior in sorted(folder.glob("[0-9][0-9][0-9]")) if folder.is_dir() else ():
        _, old = development.read_package(prior)
        if old["package_id"] == metadata["package_id"]:
            return prior
    used = (int(p.name) for p in folder.glob("[0-9][0-9][0-9]")) if folder.is_dir() else ()
    target = folder / f"{max(used, default=0) + 1:03d}"
    development._publish(target, files)
    _, copied = development.read_package(target)
    if copied["package_id"] != metadata["package_id"]:
        raise ValueError("le paquet copié ne correspond pas à sa source")
    return target


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1", GIT_PAGER="cat")
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, env=env, timeout=120,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip() or "Git a échoué")
    return result.stdout.decode("utf-8", "replace").strip()


def _bundle(found: executions.Found, remote: str, package_id: str) -> Path:
    """Demande au Runner un bundle Git local au run ; aucun jeton ni appel agent."""
    assert found.data is not None
    from .gui.runner_session import _bridge_command

    process = subprocess.run(
        _bridge_command(found.data["wsl"]["distribution"]),
        input=json.dumps({
            "action": "bundle", "run": found.data["run"], "package": remote,
            "package_id": package_id,
        }) + "\n", capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180,
    )
    events = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    if process.returncode or not events or events[-1].get("event") != "bundle":
        raise ValueError(str(events[-1].get("message")) if events else "transport Git échoué")
    source = PurePosixPath(str(events[-1]["path"]))
    if source.parent != PurePosixPath(found.data["run"]) / "transport":
        raise ValueError("bundle hors du dossier Runner")
    return _wsl_path(source, found.data["wsl"]["distribution"])


def _local_bundle(found: executions.Found, remote: str, package_id: str) -> Path:
    """Le bundle conservé dans `developpement/candidats/` : une version reste disponible même
    après une correction ultérieure dans le clone."""
    target = found.dev / "candidats" / f"{package_id}.bundle"
    if target.is_file():
        return target
    bundle = _bundle(found, remote, package_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".new-{uuid.uuid4().hex}.bundle"
    try:
        shutil.copyfile(bundle, temporary)
        development._rename_without_replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def _fetch(repo: Path, bundle: Path, package_id: str, head: str) -> None:
    _git(repo, "bundle", "verify", str(bundle))
    _git(repo, "fetch", "--quiet", "--no-tags", str(bundle), bundle_ref(package_id))
    if _git(repo, "rev-parse", "FETCH_HEAD") != head:
        raise ValueError("la tête importée diffère de celle du paquet")


def trial_dir(collab: Path, found: executions.Found) -> Path:
    """`code/` : le dépôt créé pour un projet neuf, une copie d'essai pour un dépôt existant."""
    assert found.data is not None
    repo = Path(found.data["projet"]["depot"])
    if found.data["projet"]["mode"] == "nouveau":
        return repo
    code = executions.default_code(collab)
    if code.resolve() == repo.resolve():
        raise ValueError(f"le dépôt existant occupe {code} : la copie d'essai doit en être "
                         "distincte ; déplacer le dépôt ou préparer une nouvelle exécution")
    return code


def _ensure_clean(repo: Path, role: str) -> None:
    if _git(repo, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError(f"{role} {repo} contient des modifications : rien n'est écrasé ; les "
                         "committer ou les retirer, puis reprendre")


def deliver(
    collab: Path, found: executions.Found, state: dict[str, Any], *,
    source: Path | None = None,
) -> Delivered:
    """Conserve paquet et bundle, puis extrait le commit sur sa branche candidate dans `code/`.
    Opération locale et reprenable : la refaire sur une remise faite ne change rien."""
    package = receive_package(collab, found, state, source=source)
    assert found.reference is not None and found.data is not None
    metadata = development.read_package(package)[1]
    head = metadata["identity"]["head_oid"]
    bundle = _local_bundle(found, str(state["package"]), metadata["package_id"])
    target, code = Path(found.data["projet"]["depot"]), trial_dir(collab, found)
    if not code.exists():
        code.parent.mkdir(parents=True, exist_ok=True)
        _git(code.parent, "clone", "--quiet", "--no-hardlinks", str(target), str(code))
    if not found.data["projet"].get("branche"):
        checked_out = _git(target, "symbolic-ref", "--quiet", "--short", "HEAD")
        if checked_out.startswith(BRANCH):
            raise ValueError(f"branche cible inconnue : {target} est sur {checked_out}")
        executions.update(found.reference, projet={"branche": checked_out})
    _ensure_clean(code, "l'espace d'essai")
    name = BRANCH + package.name
    try:
        existing = _git(code, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}")
    except ValueError:
        existing = ""
    if not existing:
        _fetch(code, bundle, metadata["package_id"], head)
        _git(code, "branch", name, head)
    elif existing != head:
        raise ValueError(f"la branche {name} de {code} a reçu d'autres commits : rien n'est écrasé")
    _git(code, "switch", "--quiet", name)
    shown = current(collab, executions.find(collab))
    if shown is None:
        raise ValueError(f"la remise dans {code} n'a pas pu être relue")
    return shown


def current(collab: Path, found: executions.Found) -> Delivered | None:
    """La version remise dans `code/`, si l'espace d'essai est sur une branche candidate dont la
    tête est celle du paquet conservé ; sinon rien. Aucun état n'est copié ailleurs."""
    if found.data is None or not found.data["projet"].get("branche"):
        return None
    try:
        code = trial_dir(collab, found)
        branch = _git(code, "symbolic-ref", "--quiet", "--short", "HEAD")
        head = _git(code, "rev-parse", "HEAD")
    except (OSError, ValueError):
        return None
    number = branch.removeprefix(BRANCH)
    if not branch.startswith(BRANCH) or not re.fullmatch(r"[0-9]{3}", number):
        return None
    package = found.dev / "paquets" / number
    try:
        identity = development.read_package(package)[1]
    except (OSError, ValueError):
        return None
    if identity["identity"]["head_oid"] != head:
        return None
    return Delivered(
        code, branch, package, identity["identity"]["base_oid"], head,
        Path(found.data["projet"]["depot"]), found.data["projet"]["branche"],
        _receipt(found, identity["package_id"]).is_file(),
    )


def _receipt(found: executions.Found, package_id: str) -> Path:
    return found.dev / "integrations" / f"{package_id}.json"


def accept(collab: Path, found: executions.Found) -> Path:
    """Accepte la version essayée : la branche cible avance en fast-forward jusqu'à son commit,
    depuis la base ou une version acceptée antérieure. Une divergence demande l'humain."""
    shown = current(collab, found)
    if shown is None:
        raise ValueError("aucune version remise dans code/ à accepter")
    metadata = development.read_package(shown.package)[1]
    record = {
        "schema_version": 1, "package_id": metadata["package_id"],
        "package": shown.package.name, "base_oid": shown.base, "head_oid": shown.head,
        "target": str(shown.target.resolve()), "branch": shown.target_branch,
    }
    receipt = _receipt(found, metadata["package_id"])
    if receipt.is_file() and json.loads(receipt.read_text("utf-8")) != record:
        raise ValueError("reçu d'acceptation incohérent avec la version essayée")
    _ensure_clean(shown.target, "le dépôt cible")
    ref = f"refs/heads/{shown.target_branch}"
    tip = _git(shown.target, "rev-parse", "--verify", ref)
    if tip != shown.head:
        if shown.target.resolve() != shown.code.resolve():
            bundle = found.dev / "candidats" / f"{metadata['package_id']}.bundle"
            _fetch(shown.target, bundle, metadata["package_id"], shown.head)
        try:
            _git(shown.target, "merge-base", "--is-ancestor", tip, shown.head)
        except ValueError:
            raise ValueError(
                f"la branche {shown.target_branch} de {shown.target} a divergé (tête "
                f"{tip[:12]}) : avance rapide impossible, intervention humaine nécessaire"
            ) from None
        if _git(shown.target, "symbolic-ref", "--quiet", "HEAD") == ref:
            _git(shown.target, "merge", "--ff-only", "--quiet", shown.head)
        else:
            _git(shown.target, "update-ref", ref, shown.head, tip)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_text(receipt, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return receipt
