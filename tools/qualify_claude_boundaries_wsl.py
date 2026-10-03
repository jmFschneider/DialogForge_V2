"""Mesure réseau et jeton depuis un vrai appel Bash de Claude sous WSL2."""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from iabinome import transport  # noqa: E402

PROBE = """import os
import socket
import sys

print("TOKEN_VISIBLE" if os.getenv("CLAUDE_CODE_OAUTH_TOKEN") else "TOKEN_DENIED")
with socket.socket() as connection:
    connection.settimeout(1)
    try:
        connection.connect(("127.0.0.1", int(sys.argv[1])))
    except OSError:
        print("NETWORK_DENIED")
    else:
        print("NETWORK_ALLOWED")
"""


def _tool_results(trace: Path) -> list[str]:
    calls: set[str] = set()
    results: list[str] = []
    for line in trace.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        message = event.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            command = item.get("input", {}).get("command", "")
            if item.get("type") == "tool_use" and item.get("name") == "Bash":
                if "probe.py" in command:
                    calls.add(str(item.get("id")))
            if item.get("type") == "tool_result" and item.get("tool_use_id") in calls:
                results.append(str(item.get("content", "")))
    return results


def _verify(call: Path) -> None:
    record = json.loads((call / "resultat.json").read_text(encoding="utf-8"))
    results = _tool_results(call / "stdout.txt")
    print(f"Appel : COMPLETED, code {record['return_code']}")
    for item in results:
        print(item)
    if record["return_code"] != 0:
        raise SystemExit("Appel Claude échoué ; examiner les traces")
    if len(results) != 1 or "TOKEN_DENIED" not in results[0] or "NETWORK_DENIED" not in results[0]:
        raise SystemExit("Frontière non prouvée ; examiner les traces")
    if "TOKEN_VISIBLE" in results[0] or "NETWORK_ALLOWED" in results[0]:
        raise SystemExit("Frontière défaillante ; examiner les traces")
    print("Frontières Claude Bash vérifiées")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        _verify(Path(sys.argv[2]))
        return
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = getpass("Jeton Claude (masqué) : ")
    if not os.environ["CLAUDE_CODE_OAUTH_TOKEN"]:
        raise SystemExit("Jeton absent")
    root = Path(tempfile.mkdtemp(prefix="dialogforge-claude-boundaries.", dir=Path.home()))
    workspace = root / "workspace"
    workspace.mkdir()
    (workspace / "probe.py").write_text(PROBE, encoding="utf-8")
    settings = json.dumps({
        "sandbox": {"enabled": True, "failIfUnavailable": True,
                    "allowUnsandboxedCommands": False,
                    "credentials": {"envVars": [
                        {"name": "CLAUDE_CODE_OAUTH_TOKEN", "mode": "deny"}]}},
        "permissions": {"blockReadsOutsideWorkingDirectories": True},
    })
    env_keys = {"HOME", "PATH", "LANG", "LC_ALL", "TERM", "USER", "TMPDIR", "VIRTUAL_ENV"}
    env = {key: value for key, value in os.environ.items() if key in env_keys}
    env["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
    command = [
        str(Path.home() / ".local" / "bin" / "claude"), "-p", "--restricted",
        "--permission-mode", "dontAsk", "--tools", "Bash,Read,Write,Edit,Glob,Grep",
        "--allowedTools", "Bash,Write,Edit", "--strict-mcp-config",
        "--no-session-persistence", "--disable-slash-commands", "--settings", settings,
        "--output-format", "stream-json", "--verbose",
    ]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        with socket.socket() as control:
            assert control.connect_ex(("127.0.0.1", port)) == 0
        prompt = (
            "This is a local sandbox qualification. Run exactly one Bash tool command: "
            f"python3 probe.py {port}. The script only prints whether the OAuth token's "
            "environment variable is present and whether a local TCP connection succeeds; "
            "it never prints the token. Do not use another tool or change sandbox settings. "
            "Report the command's output."
        )
        call = root / "call"
        call.mkdir()
        print(f"Qualification : {root}", flush=True)
        result = transport.run(
            command, cwd=workspace, call_dir=call, timeout_seconds=180,
            stdin_text=prompt, env=env,
        )
    if result.outcome is not transport.Outcome.COMPLETED or result.return_code:
        raise SystemExit("Appel Claude inabouti ; examiner les traces")
    _verify(call)


if __name__ == "__main__":
    main()
