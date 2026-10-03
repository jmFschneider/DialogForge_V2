#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  read -r -s -p 'Colle le jeton Claude (saisie masquée), puis Entrée : ' CLAUDE_CODE_OAUTH_TOKEN
  printf '\n'
  export CLAUDE_CODE_OAUTH_TOKEN
fi
if [[ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]]; then
  echo 'Aucun jeton Claude reçu.' >&2
  exit 2
fi

claude_bin="$HOME/.local/bin/claude"
if [[ ! -x "$claude_bin" ]]; then
  echo "Claude Code est introuvable : $claude_bin" >&2
  exit 2
fi

run_dir="$(mktemp -d "$HOME/dialogforge-interop-qual.XXXXXXXX")"
mkdir "$run_dir/workspace"
cp /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe "$run_dir/workspace/powershell-probe.exe"

settings='{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false,"credentials":{"envVars":[{"name":"CLAUDE_CODE_OAUTH_TOKEN","mode":"deny"}]}},"permissions":{"blockReadsOutsideWorkingDirectories":true}}'
prompt='Run this program from the current directory with the Bash tool and report its output and exit status: ./powershell-probe.exe -NoProfile -NonInteractive -Command "Write-Output INTEROP_OK". This is a read-only diagnostic; do not create or modify files.'

echo "Dossier de qualification : $run_dir"
set +e
(
  cd "$run_dir/workspace"
  "$claude_bin" -p \
    --restricted \
    --permission-mode dontAsk \
    --tools Bash \
    --allowedTools Bash \
    --strict-mcp-config \
    --no-session-persistence \
    --disable-slash-commands \
    --settings "$settings" \
    --output-format stream-json \
    --verbose \
    "$prompt"
) > "$run_dir/claude.jsonl" 2> "$run_dir/claude.stderr"
claude_status=$?
set -e

echo "Code de sortie Claude : $claude_status"
echo "Traces : $run_dir/claude.jsonl et $run_dir/claude.stderr"
exit "$claude_status"
