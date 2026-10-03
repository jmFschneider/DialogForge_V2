"""Vérifie les frontières srt sur des témoins jetables, sans agent fournisseur."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="dialogforge-boundaries-qual.", dir=Path.home()))
    workspace = root / "workspace"
    workspace.mkdir()
    secret = root / "outside-secret.txt"
    secret.write_text("FAKE_CREDENTIAL\n", encoding="utf-8")
    settings = root / "srt-settings.json"
    settings.write_text(json.dumps({
        "filesystem": {"denyRead": [str(Path.home())], "allowRead": ["."],
                       "allowWrite": ["."], "denyWrite": []},
        "network": {"allowedDomains": [], "deniedDomains": []},
        "credentials": {"envVars": [{"name": "RUNNER_FAKE_TOKEN", "mode": "deny"}]},
    }), encoding="utf-8")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        with socket.socket() as control:
            assert control.connect_ex(("127.0.0.1", port)) == 0
        probe = (
            "import os, pathlib, socket, sys\n"
            "assert 'RUNNER_FAKE_TOKEN' not in os.environ\n"
            "print('TOKEN_DENIED')\n"
            "assert not pathlib.Path(sys.argv[1]).exists()\n"
            "print('SECRET_HIDDEN')\n"
            "with socket.socket() as connection:\n"
            "    assert connection.connect_ex(('127.0.0.1', int(sys.argv[2]))) != 0\n"
            "print('NETWORK_DENIED')\n"
        )
        env = dict(os.environ)
        env["RUNNER_FAKE_TOKEN"] = "fake-token-never-print"
        result = subprocess.run(
            ["/usr/local/bin/srt", "--settings", str(settings), "--", "python3", "-c",
             probe, str(secret), str(port)],
            cwd=workspace, env=env, capture_output=True, text=True, check=False, timeout=30,
        )
    print(f"Qualification : {root}")
    print(result.stdout, end="")
    if result.returncode:
        print(result.stderr, end="")
        raise SystemExit(result.returncode)
    assert (secret.read_text(encoding="utf-8") == "FAKE_CREDENTIAL\n")
    assert result.stdout.splitlines() == ["TOKEN_DENIED", "SECRET_HIDDEN", "NETWORK_DENIED"]


if __name__ == "__main__":
    main()
