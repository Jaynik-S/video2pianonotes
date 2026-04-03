#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
caller_cwd="$(pwd)"
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

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <input.mid> [spacing_reduction]" >&2
  exit 1
fi

input="$1"
spacing_reduction=""
if [[ $# -eq 2 ]]; then
  spacing_reduction="$2"
  if ! [[ "$spacing_reduction" =~ ^-?[0-9]+$ ]]; then
    echo "spacing_reduction must be an integer." >&2
    exit 1
  fi
  if (( spacing_reduction < 0 )); then
    echo "spacing_reduction must be 0 or greater." >&2
    exit 1
  fi
fi

data_dir="$repo_root/data"
midi_dir="$data_dir/midi"
annotations_dir="$data_dir/annotations"

resolve_midi_input() {
  local raw_input="$1"
  local candidate=""

  if [[ -f "$raw_input" ]]; then
    candidate="$raw_input"
  elif [[ -f "$caller_cwd/$raw_input" ]]; then
    candidate="$caller_cwd/$raw_input"
  elif [[ -f "$repo_root/$raw_input" ]]; then
    candidate="$repo_root/$raw_input"
  elif [[ -f "$midi_dir/$raw_input" ]]; then
    candidate="$midi_dir/$raw_input"
  else
    for ext in mid midi; do
      if [[ -f "$midi_dir/$raw_input.$ext" ]]; then
        candidate="$midi_dir/$raw_input.$ext"
        break
      fi
    done
  fi

  if [[ -z "$candidate" ]]; then
    echo "MIDI file not found: $raw_input" >&2
    echo "Searched current path, repo root, and $midi_dir." >&2
    exit 1
  fi

  printf '%s\n' "$candidate"
}

mkdir -p "$annotations_dir"

midi_input="$(resolve_midi_input "$input")"
filename="$(basename "$midi_input")"
stem="${filename%.*}"

json_output="$annotations_dir/$stem.json"
ascii_output="$annotations_dir/$stem.txt"
html_output="$annotations_dir/$stem.html"

"$python_cmd" -m midi2annotations.main "$midi_input" --output "$json_output"

render_args=("$json_output" "--ascii" "$ascii_output" "--html" "$html_output")
if [[ -n "$spacing_reduction" ]]; then
  render_args+=("--spacing-reduction" "$spacing_reduction")
fi
"$python_cmd" -m midi2annotations.main "${render_args[@]}"

echo "Generated:"
echo "  $json_output"
echo "  $ascii_output"
echo "  $html_output"
