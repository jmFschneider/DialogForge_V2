"""Qualification locale du Runner sous Ubuntu WSL2, sans appel fournisseur."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dialogforge_runner import core  # noqa: E402
from iabinome import development  # noqa: E402


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return result.stdout.decode().strip()


def main() -> None:
    home = Path.home()
    root = Path(tempfile.mkdtemp(prefix="dialogforge-runner-qual.", dir=home))
    source = root / "source"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.name", "Runner Qualification")
    git(source, "config", "user.email", "runner@example.invalid")
    git(source, "config", "commit.gpgsign", "false")
    (source / "code.txt").write_text("base\n", encoding="utf-8")
    git(source, "add", "code.txt")
    git(source, "commit", "-qm", "base")
    base = git(source, "rev-parse", "HEAD")
    (source / "secret.txt").write_text("OUTSIDE_SECRET\n", encoding="utf-8")

    export = root / "export"
    export.mkdir()
    mandate = (b"# Mandat\n\nModifier code.txt : remplacer son contenu par exactement "
               b"candidate suivi d'un saut de ligne, puis creer un commit local.\n")
    (export / "export.md").write_bytes(mandate)
    (export / "export.json").write_text(json.dumps({
        "schema_version": 1, "source_collaboration": "qualification",
        "request_sha256": "a", "document_sha256": "b", "review_sha256": "c",
        "decision_sha256": "d", "export_md_sha256": hashlib.sha256(mandate).hexdigest(),
    }), encoding="utf-8")

    run = root / "run"
    core.prepare(
        export, source, base, run, profile="claude-wsl",
        validations=[["python3", "-c", "from pathlib import Path; "
                      "assert Path('code.txt').read_text() == 'candidate\\n'; "
                      f"assert not Path({str(source / 'secret.txt')!r}).exists(); "
                      "print('VALID_OK')"]],
    )
    workspace = run / "workspace"
    git(workspace, "config", "user.name", "Runner Qualification")
    git(workspace, "config", "user.email", "runner@example.invalid")
    git(workspace, "config", "commit.gpgsign", "false")
    sandbox_settings = run / "agent-srt-settings.json"
    sandbox_settings.write_text(json.dumps({
        "filesystem": {"denyRead": [], "allowWrite": ["."], "denyWrite": []},
        "network": {"allowedDomains": [], "deniedDomains": []},
    }), encoding="utf-8")
    fake = (
        "import pathlib, subprocess, sys; "
        "assert 'Modifier code.txt' in sys.stdin.read(); "
        "pathlib.Path('code.txt').write_text('candidate\\n'); "
        "subprocess.run(['git','add','code.txt'], check=True); "
        "subprocess.run(['git','commit','-qm','candidate'], check=True); "
        "print('BILAN_OK\\nRUNNER: CANDIDAT')"
    )
    print(f"Qualification : {root}", flush=True)
    real_agent = "--claude" in sys.argv[1:]
    if real_agent:
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = getpass("Jeton Claude (masqué) : ")
        package = core.run_claude(run, timeout_seconds=600)
    else:
        package = core.run_agent(
            run, ["/usr/local/bin/srt", "--settings", str(sandbox_settings), "--",
                  "python3", "-c", fake], timeout_seconds=120,
        )
    files, metadata = development.read_package(package)
    assert files["revision/files/code.txt"] == b"candidate\n"
    if real_agent:
        assert files["developer-notes/0001.md"].strip()
    else:
        assert b"BILAN_OK" in files["developer-notes/0001.md"]
    validation = json.loads(files["validations/validation-01.json"])
    assert validation["outcome"] == "PASSED"
    assert metadata["identity"]["head_oid"] == git(workspace, "rev-parse", "HEAD")
    assert (source / "code.txt").read_text(encoding="utf-8") == "base\n"
    assert (source / "secret.txt").read_text(encoding="utf-8") == "OUTSIDE_SECRET\n"
    print(f"Paquet vérifié : {package}")
    print(f"HEAD : {metadata['identity']['head_oid']}")
    if not real_agent:
        bridge = (
            Path(__file__).resolve().parents[1] / "src" / "dialogforge_runner" / "gui_bridge.py"
        )
        response = subprocess.run(
            [sys.executable, str(bridge)],
            input=json.dumps({"action": "collect", "run": str(run)}) + "\n",
            text=True, capture_output=True, check=True, timeout=120,
        )
        event = json.loads(response.stdout.splitlines()[-1])
        assert event["event"] == "completed"
        assert Path(event["package"]).is_dir()
        print(f"Pont GUI vérifié : {event['package']}")
        qualification_root = Path(__file__).resolve().parents[1] / ".runner-qualification"
        qualification_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="gui-bridge-", dir=qualification_root) as raw:
            temporary = Path(raw).resolve()
            assert temporary.is_relative_to(qualification_root.resolve())
            windows_repo = temporary / "repo"
            windows_export = temporary / "export"
            shutil.copytree(source, windows_repo)
            shutil.copytree(export, windows_export)

            def windows(path: Path) -> str:
                return subprocess.run(
                    ["wslpath", "-w", str(path)], check=True, capture_output=True, text=True,
                ).stdout.strip()

            second_run = root / "run-from-gui"

            def bridge_events(**request: object) -> list[dict[str, str]]:
                response = subprocess.run(
                    [sys.executable, str(bridge)], input=json.dumps(request) + "\n",
                    text=True, capture_output=True, check=False, timeout=120,
                )
                return [json.loads(line) for line in response.stdout.splitlines()]

            events = bridge_events(
                action="prepare", run=str(second_run), export=windows(windows_export),
                repo=windows(windows_repo), base=base,
                validations=[["python3", "-c", "print('ok')"]], validation_timeout=30,
                identity=["Runner Qualification", "runner@example.invalid"],
            )
            assert [event["event"] for event in events] == ["prepared"], events
            assert events[0]["base_oid"] == base
            events = bridge_events(action="launch", run=str(second_run), timeout=30, token="")
            assert [event["event"] for event in events] == ["error"]
            assert "jeton Claude absent" in events[-1]["message"]
            state = bridge_events(action="inspect", run=str(second_run))[0]
            assert (state["stage"], state["calls"]) == ("prepare", 0), state
            assert (second_run / "workspace" / "code.txt").read_text() == "base\n"
            print("Pont GUI Windows → WSL : export et clone vérifiés sans appel Claude")


if __name__ == "__main__":
    main()
