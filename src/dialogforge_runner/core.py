"""Préparation et collecte d'un candidat Git issu d'un développement extérieur."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
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
) -> None:
    """Copie le mandat et un commit dans un dossier de travail indépendant."""
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
    return ["/usr/local/bin/srt", "--settings", str(settings), "--", *command]


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
            raise ValueError(f"validation {index} échouée ; traces : {call}")
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
    if calls and (calls[-1] / "stdout.txt").exists():
        summary = attempt / "agent-bilan.md"
        text = (calls[-1] / "stdout.txt").read_bytes().decode("utf-8", "replace")
        storage.write_atomic_text(summary, "# Bilan déclaré par l'agent\n\n" + text)
        notes.append(summary)
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
            raise ValueError(f"appel agent interrompu ou échoué ; traces : {call}")
        if control is not None and control.pause_requested.is_set():
            raise ValueError(f"appel terminé ; collecte à lancer séparément ; traces : {call}")
        if control is not None and control.interrupt_requested.is_set():
            raise ValueError(f"appel terminé ; collecte interrompue ; traces : {call}")
        return _collect_locked(run, control)


def run_claude(
    run: Path, *, timeout_seconds: float, continue_existing: bool = False,
    control: transport.ExecutionControl | None = None,
) -> Path:
    """Lance Claude dans le profil WSL mesuré, puis valide sous srt."""
    _require_linux_run(run)
    if _config(run).get("profile") != "claude-wsl":
        raise ValueError("préparer ce dossier avec le profil claude-wsl")
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        raise ValueError("CLAUDE_CODE_OAUTH_TOKEN absent du processus Runner")
    claude = Path.home() / ".local" / "bin" / "claude"
    if not claude.is_file() or not Path("/usr/local/bin/srt").is_file():
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
        control=control,
    )
