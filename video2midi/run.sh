#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

if [[ -x "$repo_root/.venv/Scripts/python.exe" ]]; then
  python_cmd="$repo_root/.venv/Scripts/python.exe"
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_cmd="$repo_root/.venv/bin/python"
elif [[ -x "$repo_root/venv/Scripts/python.exe" ]]; then
  python_cmd="$repo_root/venv/Scripts/python.exe"
elif [[ -x "$repo_root/venv/bin/python" ]]; then
  python_cmd="$repo_root/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="$(command -v python3)"
else
  echo "Could not find a Python interpreter." >&2
  exit 1
fi

exec "$python_cmd" -m video2midi.v2m "$@"
