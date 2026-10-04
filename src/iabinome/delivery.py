"""Remise locale d'un paquet Runner et ouverture de sa revue documentaire."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

from . import decisions, development, executions, facade, mission, storage
from .models import Configuration, MissionKind, ReviewerAccess, State
from .registry import ADAPTERS


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
    """Copie le paquet exact, vérifié avant et après publication ; reprise idempotente."""
    if found.reference is None or found.data is None:
        raise ValueError("aucune exécution Runner enregistrée")
    executions.check_current(collab, found.reference)
    if state.get("stage") != "paquet" or state.get("locked"):
        raise ValueError("attendre un paquet Runner terminé avant la revue")
    package = state.get("package")
    if not isinstance(package, str) or package not in found.data["paquets"]:
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
    next_number = max(used, default=0) + 1
    target = folder / f"{next_number:03d}"
    development._publish(target, files)
    _, copied = development.read_package(target)
    if copied["package_id"] != metadata["package_id"]:
        raise ValueError("le paquet copié ne correspond pas à sa source")
    return target


def review_for(collab: Path, package: Path) -> Path | None:
    """Retrouve une revue liée au paquet, même après fermeture de la GUI."""
    folder = executions.dev_dir(collab) / "revues"
    for review in sorted(folder.glob("[0-9][0-9][0-9]")) if folder.is_dir() else ():
        try:
            development.verify_package(package, review)
        except (OSError, ValueError):
            continue
        return review
    return None


def create_review(collab: Path, package: Path) -> Path:
    """Crée une revue sans appel ; sa demande et son corpus viennent du paquet figé."""
    development.read_package(package)
    existing = review_for(collab, package)
    if existing is not None:
        _link_review(collab, package, existing)
        return existing
    config = Configuration.from_dict(json.loads((collab / "configuration.json").read_text("utf-8")))
    folder = executions.dev_dir(collab) / "revues"
    used = (int(p.name) for p in folder.glob("[0-9][0-9][0-9]")) if folder.is_dir() else ()
    number = max(used, default=0) + 1
    target = folder / f"{number:03d}"
    request = facade.CreationRequest(
        collab=target,
        demande=facade.DemandeSource((package / "review-request.md").read_text("utf-8"), "fichier"),
        kind=MissionKind.RECHERCHE, reviewer_access=ReviewerAccess.CONSULT,
        agent_a=config.agent_a.adapter_id, agent_b=config.agent_b.adapter_id,
        max_revisions=config.max_revisions,
        model_a=config.agent_a.model, model_b=config.agent_b.model,
        effort_a=config.agent_a.effort, effort_b=config.agent_b.effort,
        source_root=package, source_list=package / "sources.txt",
    )
    facade.create_collaboration(request, adapters=ADAPTERS)
    _link_review(collab, package, target)
    return target


def _link_review(collab: Path, package: Path, review: Path) -> None:
    anchor = executions.dev_dir(collab).parent.resolve()
    metadata = development.read_package(package)[1]
    link = {
        "schema_version": 1,
        "conception": collab.resolve().relative_to(anchor).as_posix(),
        "package": package.resolve().relative_to(anchor).as_posix(),
        "package_id": metadata["package_id"],
    }
    path = review / "provenance_runner.json"
    if path.is_file():
        if json.loads(path.read_text("utf-8")) != link:
            raise ValueError("provenance de la revue différente du paquet")
    else:
        storage.write_atomic_text(path, json.dumps(link, ensure_ascii=False, indent=2) + "\n")
    root = mission.root_of(collab)
    if root is not None:
        rel = collab.resolve().relative_to(root.resolve()).as_posix()
        mission.attach(root, review, "revue", source=rel)
    development.verify_package(package, review)


def review_context(review: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Relit le lien local et refuse les chemins sortant de la mission."""
    link = json.loads((review / "provenance_runner.json").read_text("utf-8"))
    if not isinstance(link, dict) or set(link) != {
        "schema_version", "conception", "package", "package_id",
    } or link["schema_version"] != 1:
        raise ValueError("provenance de la revue invalide")
    anchor = review.parent.parent.parent.resolve()
    paths = []
    for key in ("conception", "package"):
        value = link[key]
        if (not isinstance(value, str) or not value or "\\" in value or ":" in value
                or any(part in ("", ".", "..") for part in value.split("/"))):
            raise ValueError(f"chemin {key} invalide")
        path = (anchor / value).resolve()
        if not path.is_relative_to(anchor):
            raise ValueError(f"chemin {key} hors de la mission")
        paths.append(path)
    collab, package = paths
    metadata = development.read_package(package)[1]
    if metadata["package_id"] != link["package_id"]:
        raise ValueError("paquet différent de celui de la revue")
    development.verify_package(package, review)
    return collab, package, metadata


def integration_preview(review: Path) -> tuple[str, str, str]:
    collab, _, metadata = review_context(review)
    found = executions.find(collab)
    if found.data is None:
        raise ValueError("exécution Runner introuvable")
    identity = metadata["identity"]
    return found.data["projet"]["depot"], identity["base_oid"], identity["head_oid"]


def can_integrate(review: Path, state: State) -> bool:
    verdict = decisions.latest(review) if (review / "provenance_runner.json").is_file() else None
    return (verdict is not None and decisions.is_acceptance(verdict)
            and decisions.applies_to_current(review, verdict, state))


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


def _local_bundle(found: executions.Found, package_id: str) -> Path:
    assert found.data is not None
    folder = found.dev / "candidats"
    target = folder / f"{package_id}.bundle"
    if target.is_file():
        return target
    for remote in reversed(found.data["paquets"]):
        source = _source_path(found.data, remote, found.data["wsl"]["distribution"])
        try:
            same = development.read_package(source)[1]["package_id"] == package_id
        except (OSError, ValueError):
            continue
        if same:
            break
    else:
        raise ValueError("paquet Runner d'origine introuvable")
    bundle = _bundle(found, remote, package_id)
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / f".new-{uuid.uuid4().hex}.bundle"
    try:
        shutil.copyfile(bundle, temporary)
        development._rename_without_replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def integrate_candidate(review: Path) -> Path:
    """Après acceptation de la revue, avance le dépôt cible en fast-forward explicite."""
    collab, package, metadata = review_context(review)
    verdict = decisions.latest(review)
    if not decisions.is_acceptance(verdict):
        raise ValueError("accepter d'abord la revue du paquet")
    found = executions.find(collab)
    if found.reference is None or found.data is None:
        raise ValueError("exécution Runner de ce candidat introuvable")
    executions.check_current(collab, found.reference)
    identity = metadata["identity"]
    base, head = identity["base_oid"], identity["head_oid"]
    if (base != found.data["projet"]["base_oid"] or found.export is None or
            {name[7:]: value for name, value in development.read_package(package)[0].items()
             if name.startswith("export/")} != development._tree(found.export)):
        raise ValueError("paquet différent de la base ou de l'export de l'exécution")
    repo = Path(found.data["projet"]["depot"])
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo.resolve():
        raise ValueError("le dépôt cible n'est pas sa racine Git")
    if _git(repo, "status", "--porcelain"):
        raise ValueError("le dépôt cible contient des changements locaux")
    current = _git(repo, "rev-parse", "HEAD")
    receipt = found.dev / "integrations" / f"{metadata['package_id']}.json"
    record = {
        "schema_version": 1, "package_id": metadata["package_id"],
        "base_oid": base, "head_oid": head, "target": str(repo.resolve()),
    }
    if receipt.is_file():
        if json.loads(receipt.read_text("utf-8")) != record or current != head:
            raise ValueError("reçu d'intégration incohérent avec le dépôt cible")
        return receipt
    if current not in (base, head):
        raise ValueError(f"le dépôt cible a avancé depuis la base {base[:12]} : {current[:12]}")
    if current == base:
        bundle = _local_bundle(found, metadata["package_id"])
        _git(repo, "bundle", "verify", str(bundle))
        _git(repo, "fetch", "--no-tags", str(bundle), "HEAD")
        if _git(repo, "rev-parse", "FETCH_HEAD") != head:
            raise ValueError("la tête importée diffère de celle du paquet")
        _git(repo, "merge-base", "--is-ancestor", base, head)
        development.verify_package(package, review)
        if _git(repo, "rev-parse", "HEAD") != base or _git(repo, "status", "--porcelain"):
            raise ValueError("le dépôt cible a changé pendant l'import Git")
        _git(repo, "merge", "--ff-only", head)
        if _git(repo, "rev-parse", "HEAD") != head:
            raise ValueError("la tête cible diffère après intégration")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_text(receipt, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return receipt
