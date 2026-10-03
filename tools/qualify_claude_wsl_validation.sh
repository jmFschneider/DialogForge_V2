#!/usr/bin/env bash
set -euo pipefail

run_dir="$(mktemp -d "$HOME/dialogforge-validation-qual.XXXXXXXX")"
mkdir "$run_dir/workspace" "$run_dir/source"
printf 'SOURCE_ORIGINAL\n' > "$run_dir/source/witness.txt"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
host_witness="$repo_root/.runner-qualification/wsl-validation-host-witness.txt"
mkdir -p "$(dirname "$host_witness")"
printf 'HOST_ORIGINAL\n' > "$host_witness"
windows_witness="$(wslpath -w "$host_witness")"
cp /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe "$run_dir/workspace/powershell-probe.exe"
cat > "$run_dir/srt-settings.json" <<'EOF'
{"filesystem":{"denyRead":[],"allowWrite":["."],"denyWrite":[]},"network":{"allowedDomains":[],"deniedDomains":[]}}
EOF

cat > "$run_dir/workspace/validate.sh" <<'EOF'
#!/usr/bin/env bash
printf 'VALIDATION_INSIDE\n' > validation-inside.txt
inside=$?
printf 'VALIDATION_OUTSIDE\n' > ../source/witness.txt
outside=$?
./powershell-probe.exe -NoProfile -NonInteractive -Command "Set-Content -LiteralPath '$1' -Value 'VALIDATION_HOST_INTEROP'"
interop=$?
printf 'inside=%s outside=%s interop=%s\n' "$inside" "$outside" "$interop"
EOF

echo "Dossier de qualification : $run_dir"
set +e
(
  cd "$run_dir/workspace"
  /usr/local/bin/srt --debug --settings "$run_dir/srt-settings.json" /bin/bash ./validate.sh "$windows_witness"
) > "$run_dir/validation.stdout" 2> "$run_dir/validation.stderr"
validation_status=$?
set -e

echo "Code de sortie validation : $validation_status"
cat "$run_dir/validation.stdout"
if [[ -f "$run_dir/workspace/validation-inside.txt" ]]; then
  echo "Écriture interne : $(cat "$run_dir/workspace/validation-inside.txt")"
else
  echo "Écriture interne : absente"
fi
echo "Témoin extérieur : $(cat "$run_dir/source/witness.txt")"
echo "Témoin Windows : $(cat "$host_witness")"
echo "Traces : $run_dir/validation.stdout et $run_dir/validation.stderr"

[[ "$validation_status" -eq 0 ]]
[[ "$(cat "$run_dir/workspace/validation-inside.txt")" == VALIDATION_INSIDE ]]
[[ "$(cat "$run_dir/source/witness.txt")" == SOURCE_ORIGINAL ]]
[[ "$(cat "$host_witness")" == HOST_ORIGINAL ]]
rg -q 'Applying seccomp filter for Unix socket blocking' "$run_dir/validation.stderr"
