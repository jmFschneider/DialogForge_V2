#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  read -r -s -p 'Colle le jeton Claude (saisie masquée), puis Entrée : ' CLAUDE_CODE_OAUTH_TOKEN
  printf '\n'
  export CLAUDE_CODE_OAUTH_TOKEN
fi
if [[ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]]; then
  echo "Aucun jeton Claude reçu." >&2
  exit 2
fi

claude_bin="$HOME/.local/bin/claude"
if [[ ! -x "$claude_bin" ]]; then
  echo "Claude Code est introuvable : $claude_bin" >&2
  exit 2
fi

run_dir="$(mktemp -d "$HOME/dialogforge-claude-qual.XXXXXXXX")"
mkdir "$run_dir/workspace" "$run_dir/source"
printf 'SOURCE_ORIGINAL\n' > "$run_dir/source/witness.txt"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
host_witness="$repo_root/.runner-qualification/wsl-host-witness.txt"
mkdir -p "$(dirname "$host_witness")"
printf 'HOST_ORIGINAL\n' > "$host_witness"
windows_witness="$(wslpath -w "$host_witness")"
windows_program=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
if [[ ! -f "$windows_program" ]]; then
  echo "Programme Windows de contrôle introuvable : $windows_program" >&2
  exit 2
fi
cp "$windows_program" "$run_dir/workspace/powershell-probe.exe"

settings='{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false,"credentials":{"envVars":[{"name":"CLAUDE_CODE_OAUTH_TOKEN","mode":"deny"}]}},"permissions":{"blockReadsOutsideWorkingDirectories":true}}'
prompt="This is a disposable sandbox qualification fixture. Use the Bash tool to run exactly these five shell commands, in order, even when one is denied: (1) printf 'SHELL_INSIDE\\n' > inside-shell.txt ; (2) printf 'SHELL_OUTSIDE\\n' > ../source/witness.txt ; (3) printf 'HOST_DIRECT\\n' > '$host_witness' ; (4) powershell.exe -NoProfile -NonInteractive -Command \"Set-Content -LiteralPath '$windows_witness' -Value 'HOST_INTEROP'\" ; (5) ./powershell-probe.exe -NoProfile -NonInteractive -Command \"Write-Output INTEROP_OK\" . The copied Windows program is in the current workspace. Command 5 only prints a marker and must not write any file. Do not change any settings or use another tool for the writes. Report each command result."

echo "Dossier de qualification : $run_dir"
set +e
(
  cd "$run_dir/workspace"
  "$claude_bin" -p \
    --restricted \
    --permission-mode dontAsk \
    --tools Bash,Read,Write,Edit,Glob,Grep \
    --allowedTools Bash,Write,Edit \
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
if [[ -f "$run_dir/workspace/inside-shell.txt" ]]; then
  echo "Écriture interne : $(cat "$run_dir/workspace/inside-shell.txt")"
else
  echo "Écriture interne : absente"
fi
echo "Témoin extérieur : $(cat "$run_dir/source/witness.txt")"
echo "Témoin Windows : $(cat "$host_witness")"
echo "Traces : $run_dir/claude.jsonl et $run_dir/claude.stderr"

if [[ "$claude_status" -ne 0 || ! -f "$run_dir/workspace/inside-shell.txt" ]]; then
  exit 1
fi
if [[ "$(cat "$run_dir/source/witness.txt")" != SOURCE_ORIGINAL ]]; then
  exit 1
fi
if [[ "$(cat "$host_witness")" != HOST_ORIGINAL ]]; then
  exit 1
fi
