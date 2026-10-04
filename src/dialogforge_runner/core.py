"""Préparation et collecte d'un candidat Git issu d'un développement extérieur."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from iabinome import development, lock, storage, transport
from iabinome.models import positive_seconds


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1", GIT_PAGER="cat")
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        env=env,
        check=False,
        timeout=60,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip() or "Git a échoué")
    return result.stdout.decode("utf-8", "replace").strip()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    storage.write_atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


SRT = "/usr/local/bin/srt"


class ValidationFailed(ValueError):
    """Une validation finale a échoué ; le candidat peut être corrigé dans le clone."""


def _claude() -> Path:
    return Path.home() / ".local" / "bin" / "claude"


def _folder(path: Path) -> Path:
    """Le dossier existant le plus proche : où lire une configuration Git avant de créer `path`."""
    return next((p for p in (path, *path.parents) if p.is_dir()), Path.home())


def _inside_repo(folder: Path) -> bool:
    try:
        _git(folder, "rev-parse", "--show-toplevel")
    except ValueError:
        return False
    return True


def git_identity(where: Path | None = None) -> tuple[str, str] | None:
    """L'identité Git **déjà configurée** à cet endroit ; jamais inventée, jamais écrite."""
    folder = _folder(where) if where is not None else Path.home()
    values = []
    for key in ("user.name", "user.email"):
        try:
            values.append(_git(folder, "config", "--get", key))
        except ValueError:
            return None
    return (values[0], values[1]) if all(values) else None


def check_new_project(path: Path) -> None:
    """Refus avant toute mutation : dossier absent ou vide (ou dépôt sans commit), Git, identité."""
    if shutil.which("git") is None:
        raise ValueError("Git est introuvable : l'installer avant de créer un projet")
    if path.exists():
        content = [entry.name for entry in path.iterdir() if entry.name != ".git"]
        has_git = (path / ".git").exists()
        if not path.is_dir() or content or (has_git and (
            not (path / ".git").is_dir() or _has_commit(path)
        )):
            raise ValueError(
                f"{path} contient déjà des fichiers ou un historique Git : "
                "choisir « Dépôt existant » ou un dossier vide"
            )
        if not has_git and _inside_repo(path):
            raise ValueError(f"{path} est dans un dépôt Git existant : choisir un autre dossier")
    elif _inside_repo(_folder(path)):
        raise ValueError(f"{path} serait dans un dépôt Git existant : choisir un autre dossier")
    if git_identity(path) is None:
        raise ValueError(
            "identité Git absente : configurer user.name et user.email "
            "(git config --global ...) avant de créer le projet ; rien n'est inventé"
        )


def _has_commit(repo: Path) -> bool:
    try:
        _git(repo, "rev-parse", "--verify", "HEAD")
    except ValueError:
        return False
    return True


def init_project(path: Path) -> tuple[str, str]:
    """Initialise le dépôt d'un projet neuf et y crée un commit initial vide, avec l'identité
    déjà configurée. Rend l'OID et l'auteur de ce commit ; un échec rend le dossier comme avant."""
    check_new_project(path)
    created, had_git = not path.exists(), (path / ".git").exists()
    path.mkdir(parents=True, exist_ok=True)
    try:
        if not had_git:
            _git(path, "init", "--quiet")
        _git(path, "commit", "--quiet", "--allow-empty", "-m", "Commit initial vide")
        return _git(path, "rev-parse", "HEAD"), _git(path, "log", "-1", "--format=%an <%ae>")
    except BaseException:
        if not had_git:
            shutil.rmtree(path / ".git", ignore_errors=True)
        if created:
            shutil.rmtree(path, ignore_errors=True)
        raise


def reuse_initial_base(path: Path, oid: str, author: str) -> None:
    """Ne reconnaît que la base initiale enregistrée, intacte ; jamais un autre dépôt."""
    try:
        intact = (
            (path / ".git").is_dir() and _git(path, "rev-parse", "HEAD") == oid
            and _git(path, "rev-list", "--all", "--count") == "1"
            and not _git(path, "ls-tree", "-r", "--name-only", oid)
            and not _git(path, "status", "--porcelain", "--untracked-files=normal")
            and _git(path, "log", "-1", "--format=%an <%ae>", oid) == author
        )
    except ValueError:
        intact = False
    if not intact:
        raise ValueError(
            f"{path} n'est plus le dépôt initial créé pour ce projet : "
            "choisir « Dépôt existant » pour l'utiliser tel qu'il est"
        )


def preflight(run: Path, validations: Sequence[Sequence[str]], profile: str) -> None:
    """Prérequis de l'exécution, sans rien écrire : Git, Claude et srt pour le profil Ubuntu,
    chaque exécutable de validation. Un prérequis présent ne prouve pas que les tests passeront."""
    if shutil.which("git") is None:
        raise ValueError("Git est introuvable dans cet environnement")
    if profile == "claude-wsl":
        _require_linux_run(run)
        for name, tool in (("srt", Path(SRT)), ("Claude", _claude())):
            if not tool.is_file():
                raise ValueError(f"{name} est absent dans Ubuntu : {tool}")
    path_env = _validation_env().get("PATH", "")
    for command in validations:
        executable = command[0]
        if "/" in executable or "\\" in executable:
            continue  # chemin dans le clone : vérifié à la collecte
        found = shutil.which(executable, path=path_env)
        if found is None:
            raise ValueError(
                f"validation « {' '.join(command)} » : {executable} est introuvable "
                f"dans le PATH d'Ubuntu ({path_env})"
            )
        if profile == "claude-wsl" and Path(found).resolve().is_relative_to(Path.home()):
            raise ValueError(
                f"validation « {' '.join(command)} » : {found} est dans le dossier personnel, "
                "illisible sous srt ; installer l'outil pour le système (hors du dossier personnel)"
            )


def inspect_run(run: Path) -> dict[str, Any]:
    """L'état d'un dossier Runner, lu sur ses artefacts : rien n'est écrit, rien n'est relancé."""
    if not run.exists():
        return {"stage": "absent"}
    try:
        config = _config(run)
    except (OSError, ValueError) as exc:
        return {"stage": "invalide", "detail": f"run.json illisible : {exc}"}
    calls = sorted((run / "calls").glob("call-*"))
    attempts = sorted((run / "results").glob("collect-*"))
    valid: list[str] = []
    report = ""
    checks: list[dict[str, Any]] = []
    for attempt in attempts:
        try:
            files, _ = development.read_package(attempt / "package")
            valid.append(str(attempt / "package"))
            notes = sorted(name for name in files if name.startswith("developer-notes/"))
            report = files[notes[-1]].decode("utf-8", "replace")[:8000] if notes else ""
            checks = [json.loads(data) for name, data in files.items()
                      if name.startswith("validations/") and name.endswith(".json")]
        except (OSError, ValueError):
            pass
    for call in reversed(calls):
        result = call / "resultat.json"
        output = call / "stdout.txt"
        try:
            if json.loads(result.read_text("utf-8"))["return_code"] == 0 and output.is_file():
                report = output.read_bytes().decode("utf-8", "replace")[:8000]
                break
        except (OSError, ValueError, KeyError):
            continue
    last_ok = bool(attempts) and valid[-1:] == [str(attempts[-1] / "package")]
    last_call = calls[-1] / "resultat.json" if calls else None
    if last_call is not None and not last_call.exists():
        last_call = calls[-1]
    later_call = last_call is not None and (
        not attempts or last_call.stat().st_mtime_ns > attempts[-1].stat().st_mtime_ns
    )
    stage = "appel" if later_call else (
        "paquet" if last_ok else "validations" if attempts else "prepare"
    )
    return {
        "stage": stage, "calls": len(calls), "collects": len(attempts),
        "last_collect": None if not attempts else "reussie" if last_ok else "echouee",
        "package": valid[-1] if valid else None,
        "report": report, "checks": checks,
        "base_oid": config["base_oid"], "locked": (run / "verrou.json").exists(),
        "last_call_complete": bool(calls) and (calls[-1] / "resultat.json").exists(),
    }


def bundle_ref(package_id: str) -> str:
    return f"refs/dialogforge/{package_id}"


def bundle_candidate(run: Path, package: Path, package_id: str) -> Path:
    """Transporte uniquement les commits du candidat exact d'un paquet valide, même si le clone a
    avancé depuis : le bundle désigne la tête du paquet par une référence à son nom."""
    with lock.acquire(run / "verrou.json", "runner-bundle"):
        if not package.is_relative_to(run / "results"):
            raise ValueError("paquet étranger au dossier Runner")
        _, metadata = development.read_package(package)
        if metadata["package_id"] != package_id:
            raise ValueError("identité du paquet différente de celle demandée")
        base, head = metadata["identity"]["base_oid"], metadata["identity"]["head_oid"]
        if base != _config(run)["base_oid"]:
            raise ValueError("base du paquet différente du dossier Runner")
        workspace, ref = run / "workspace", bundle_ref(package_id)
        _git(workspace, "update-ref", ref, head)
        folder = run / "transport"
        folder.mkdir(exist_ok=True)
        target = folder / f"{package_id}.bundle"
        if not target.exists():
            temporary = folder / f".new-{uuid.uuid4().hex}.bundle"
            try:
                _git(workspace, "bundle", "create", str(temporary), ref, f"^{base}")
                _git(workspace, "bundle", "verify", str(temporary))
                temporary.rename(target)
            finally:
                temporary.unlink(missing_ok=True)
        _git(workspace, "bundle", "verify", str(target))
        if f"{head} {ref}" not in _git(workspace, "bundle", "list-heads", str(target)):
            raise ValueError("le bundle ne désigne pas la tête du paquet")
        return target


def _config(run: Path) -> dict[str, Any]:
    value = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("run.json invalide")
    return value


def prepare(
    export: Path,
    repo: Path,
    base: str,
    output: Path,
    *,
    validations: Sequence[Sequence[str]],
    validation_timeout: float = 300,
    lot: Path | None = None,
    profile: str = "local",
    identity: tuple[str, str] | None = None,
) -> str:
    """Copie le mandat et un commit dans un dossier de travail indépendant ; rend l'OID de base.

    `identity` (nom, courriel déjà configurés ailleurs) n'est posée dans la configuration locale
    du clone que s'il n'en voit aucune : l'agent doit pouvoir committer, sans rien inventer.
    """
    development.validate_export(export)
    if not validations or any(not command or not all(command) for command in validations):
        raise ValueError("au moins une commande de validation complète est requise")
    validation_timeout = positive_seconds(validation_timeout)
    if profile not in {"local", "claude-wsl"}:
        raise ValueError("profil Runner inconnu")
    if profile == "claude-wsl":
        _require_linux_run(output)
    source = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    oid = _git(source, "rev-parse", "--verify", f"{base}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
        raise ValueError("commit de départ invalide")
    target = output.resolve()
    if target.exists():
        raise ValueError(f"{target} existe déjà")
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError("le dossier d'exécution doit être séparé du dépôt source")
    if target.is_relative_to(export.resolve()):
        raise ValueError("le dossier d'exécution doit être séparé de l'export")
    if lot is not None and not lot.is_file():
        raise ValueError("lot.md absent")
    target.mkdir(parents=True)
    try:
        (target / "input").mkdir()
        (target / "input" / "export").mkdir()
        shutil.copy2(export / "export.md", target / "input" / "export" / "export.md")
        shutil.copy2(export / "export.json", target / "input" / "export" / "export.json")
        if lot is not None:
            shutil.copy2(lot, target / "input" / "lot.md")
        development.validate_export(target / "input" / "export")
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-local",
                "--no-hardlinks",
                "--no-checkout",
                str(source),
                str(target / "workspace"),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        workspace = target / "workspace"
        _git(workspace, "remote", "remove", "origin")
        _git(workspace, "checkout", "--quiet", "--detach", oid)
        if identity is not None and git_identity(workspace) is None:
            _git(workspace, "config", "user.name", identity[0])
            _git(workspace, "config", "user.email", identity[1])
        _write_json(
            target / "run.json",
            {
                "schema_version": 1,
                "source": str(source),
                "base_oid": oid,
                "validations": [list(command) for command in validations],
                "validation_timeout": validation_timeout,
                "profile": profile,
            },
        )
        (target / "calls").mkdir()
        (target / "results").mkdir()
    except BaseException:
        shutil.rmtree(target)
        raise
    return oid


def _candidate(run: Path, base: str) -> str:
    workspace = run / "workspace"
    if _git(workspace, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("espace de travail non propre : traiter les fichiers avant collecte")
    head = _git(workspace, "rev-parse", "HEAD")
    if head == base:
        raise ValueError("aucun commit candidat depuis la base")
    _git(workspace, "merge-base", "--is-ancestor", base, head)
    return head


def _require_linux_run(run: Path) -> None:
    if os.name != "posix" or run.resolve().is_relative_to(Path("/mnt")):
        raise ValueError("le profil claude-wsl exige un dossier natif Linux hors de /mnt")


def _validation_command(run: Path, config: dict[str, Any], command: list[str]) -> list[str]:
    if config.get("profile", "local") == "local":
        return command
    _require_linux_run(run)
    settings = run / "srt-settings.json"
    _write_json(settings, {
        "filesystem": {"denyRead": [str(Path.home())], "allowRead": ["."],
                       "allowWrite": ["."], "denyWrite": []},
        "network": {"allowedDomains": [], "deniedDomains": []},
    })
    return [SRT, "--settings", str(settings), "--", *command]


def _validation_env() -> dict[str, str]:
    """Ne transmet pas les identifiants de l'appel agent aux validations."""
    kept = {"HOME", "PATH", "LANG", "LC_ALL", "TERM", "USER", "TMPDIR", "VIRTUAL_ENV"}
    return {key: value for key, value in os.environ.items() if key in kept}


def collect(run: Path, *, control: transport.ExecutionControl | None = None) -> Path:
    """Valide le HEAD exact puis construit un paquet neuf, sans agent."""
    with lock.acquire(run / "verrou.json", "runner-collect"):
        return _collect_locked(run, control)


def _collect_locked(run: Path, control: transport.ExecutionControl | None = None) -> Path:
    config = _config(run)
    base = str(config["base_oid"])
    head = _candidate(run, base)
    results = run / "results"
    attempt = results / f"collect-{len(list(results.glob('collect-*'))) + 1:04d}"
    attempt.mkdir()
    validations: list[Path] = []
    for index, command in enumerate(config["validations"], 1):
        if control is not None and control.interrupt_requested.is_set():
            raise ValueError("collecte interrompue avant la validation suivante")
        call = attempt / f"validation-{index:02d}"
        call.mkdir()
        started = datetime.now(UTC).isoformat()
        try:
            actual_command = _validation_command(run, config, command)
            outcome = transport.run(
                actual_command,
                cwd=run / "workspace",
                call_dir=call,
                timeout_seconds=float(config["validation_timeout"]),
                env=_validation_env() if config.get("profile") == "claude-wsl" else None,
                control=control,
            )
        except transport.TransportError as exc:
            _write_json(
                call / "validation.json",
                {
                    "schema_version": 1,
                    "validation_id": f"validation-{index:02d}",
                    "head_oid": head,
                    "command": command,
                    "started_at": started,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "exit_code": None,
                    "outcome": "NOT_RUN",
                    "environment": config.get("profile", "local"),
                    "summary": str(exc),
                    "artifacts": [],
                },
            )
            raise ValueError(f"validation {index} non lancée ; traces : {call}") from exc
        completed = datetime.now(UTC).isoformat()
        snippets = []
        for stream in ("stdout", "stderr"):
            path = call / f"{stream}.txt"
            if path.exists():
                excerpt = path.read_bytes()[-2000:].decode("utf-8", "replace")
                snippets.append(f"{stream}: {excerpt}")
        record = {
            "schema_version": 1,
            "validation_id": f"validation-{index:02d}",
            "head_oid": head,
            "command": command,
            "started_at": started,
            "completed_at": completed,
            "exit_code": outcome.return_code,
            "outcome": "PASSED"
            if outcome.outcome is transport.Outcome.COMPLETED and outcome.return_code == 0
            else "FAILED",
            "environment": config.get("profile", "local"),
            "summary": outcome.outcome.value + ("\n" + "\n".join(snippets) if snippets else ""),
            "artifacts": [],
        }
        path = call / "validation.json"
        _write_json(path, record)
        validations.append(path)
        if record["outcome"] != "PASSED":
            raise ValidationFailed(f"validation {index} échouée ; traces : {call}")
        try:
            current = _candidate(run, base)
        except ValueError as exc:
            raise ValueError(f"validation {index} a modifié le candidat") from exc
        if current != head:
            raise ValueError(f"validation {index} a modifié le candidat")
        if control is not None and control.pause_requested.is_set():
            raise ValueError("collecte mise en pause ; la relancer explicitement")
    if _candidate(run, base) != head:
        raise ValueError("candidat modifié pendant la collecte")
    notes = [run / "input" / "lot.md"] if (run / "input" / "lot.md").exists() else []
    calls = sorted((run / "calls").glob("call-*"))
    for call in reversed(calls):
        output, result = call / "stdout.txt", call / "resultat.json"
        try:
            succeeded = json.loads(result.read_text("utf-8"))["return_code"] == 0
        except (OSError, ValueError, KeyError):
            succeeded = False
        if succeeded and output.is_file():
            summary = attempt / "agent-bilan.md"
            text = output.read_bytes().decode("utf-8", "replace")
            storage.write_atomic_text(summary, "# Bilan déclaré par l'agent\n\n" + text)
            notes.append(summary)
            break
    package = attempt / "package"
    development.build_package(
        run / "input" / "export",
        run / "workspace",
        base,
        head,
        package,
        validations=validations,
        developer_notes=notes,
    )
    return package


def run_agent(
    run: Path,
    command: Sequence[str],
    *,
    timeout_seconds: float,
    env: Mapping[str, str] | None = None,
    continue_existing: bool = False,
    correction: str = "",
    control: transport.ExecutionControl | None = None,
) -> Path:
    """Lance un agent fourni par l'appelant, puis collecte sans fenêtre concurrente.

    Cette interface interne sert d'abord au faux agent. L'adaptateur réel et son
    environnement d'écriture doivent être qualifiés avant exposition dans la CLI.
    """
    timeout_seconds = positive_seconds(timeout_seconds)
    with lock.acquire(run / "verrou.json", "runner-run"):
        config = _config(run)
        calls = run / "calls"
        previous = sorted(calls.glob("call-*"))
        if previous and not continue_existing:
            raise ValueError("appel déjà tenté ; continuation explicite requise")
        if not previous and continue_existing:
            raise ValueError("aucun appel à continuer")
        if correction and not continue_existing:
            raise ValueError("une correction exige un appel de continuation")
        prior = inspect_run(run) if continue_existing else None
        if prior and prior["package"] and not correction:
            raise ValueError("un paquet existe déjà : préciser la correction demandée")
        call = calls / f"call-{len(previous) + 1:04d}"
        call.mkdir()
        mandate = (run / "input" / "export" / "export.md").read_text(encoding="utf-8")
        lot = run / "input" / "lot.md"
        prompt = (
            f"Réalise le lot dans le dépôt courant à partir du commit {config['base_oid']}. "
            "Organise librement ton travail, teste-le, puis crée les commits locaux. "
            "Termine sur un candidat committé. Explique tout travail incomplet ou arbitrage "
            "nécessaire dans ta réponse finale. Arrête-toi si un prérequis manque ou si une "
            "décision dépasse le mandat. Ne publie ni ne déploie rien.\n\n"
            f"# Mandat\n{mandate}\n"
            "\n# Validations finales prévues\n"
            f"{json.dumps(config['validations'], ensure_ascii=False)}\n"
        )
        if lot.exists():
            prompt += f"\n# Lot choisi\n{lot.read_text(encoding='utf-8')}\n"
        if previous:
            prompt += "\nExamine l'état Git et le travail présent avant de continuer.\n"
            attempts = sorted((run / "results").glob("collect-*"))
            if attempts:
                records = sorted(attempts[-1].glob("validation-*/validation.json"))
                for record in records:
                    result = json.loads(record.read_text(encoding="utf-8"))
                    if result.get("outcome") != "PASSED":
                        prompt += ("\n# Validation finale à corriger\n"
                                   + str(result.get("summary", ""))[:4000] + "\n")
        if correction:
            prompt += f"\n# Correction demandée par l'utilisateur\n{correction}\n"
        storage.write_atomic_text(call / "prompt.md", prompt)
        result = transport.run(
            command,
            cwd=run / "workspace",
            call_dir=call,
            timeout_seconds=timeout_seconds,
            stdin_text=prompt,
            env=env,
            control=control,
        )
        if result.outcome is not transport.Outcome.COMPLETED or result.return_code:
            output = call / "stdout.txt"
            if output.is_file():
                with output.open("rb") as stream:
                    if b"OAuth access token is invalid" in stream.read(4096):
                        raise ValueError(
                            "authentification de l'agent refusée (401) ; vérifier le jeton"
                        )
            raise ValueError(f"appel agent interrompu ou échoué ; traces : {call}")
        if (prior and prior["stage"] == "paquet" and
                _git(run / "workspace", "rev-parse", "HEAD") ==
                development.read_package(Path(prior["package"]))[1]["identity"]["head_oid"]):
            raise ValueError(
                "la correction n'a produit aucun nouveau commit ; paquet précédent conservé"
            )
        if control is not None and control.pause_requested.is_set():
            raise ValueError(f"appel terminé ; collecte à lancer séparément ; traces : {call}")
        if control is not None and control.interrupt_requested.is_set():
            raise ValueError(f"appel terminé ; collecte interrompue ; traces : {call}")
        return _collect_locked(run, control)


def run_claude(
    run: Path, *, timeout_seconds: float, continue_existing: bool = False,
    correction: str = "",
    control: transport.ExecutionControl | None = None,
) -> Path:
    """Lance Claude dans le profil WSL mesuré, puis valide sous srt."""
    _require_linux_run(run)
    if _config(run).get("profile") != "claude-wsl":
        raise ValueError("préparer ce dossier avec le profil claude-wsl")
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        raise ValueError("CLAUDE_CODE_OAUTH_TOKEN absent du processus Runner")
    claude = _claude()
    if not claude.is_file() or not Path(SRT).is_file():
        raise ValueError("Claude ou srt absent dans Ubuntu")
    settings = json.dumps({
        "sandbox": {"enabled": True, "failIfUnavailable": True,
                    "allowUnsandboxedCommands": False,
                    "credentials": {"envVars": [
                        {"name": "CLAUDE_CODE_OAUTH_TOKEN", "mode": "deny"}]}},
        "permissions": {"blockReadsOutsideWorkingDirectories": True},
    })
    env = _validation_env()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    return run_agent(
        run,
        [str(claude), "-p", "--restricted", "--permission-mode", "dontAsk",
         "--tools", "Bash,Read,Write,Edit,Glob,Grep", "--allowedTools", "Bash,Write,Edit",
         "--strict-mcp-config", "--no-session-persistence", "--disable-slash-commands",
         "--settings", settings],
        timeout_seconds=timeout_seconds, env=env, continue_existing=continue_existing,
        correction=correction, control=control,
    )
