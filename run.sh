#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
data_dir="$script_dir/data"
cd "$script_dir"

if [[ -x "$script_dir/.venv/Scripts/python.exe" ]]; then
  python_cmd="$script_dir/.venv/Scripts/python.exe"
elif [[ -x "$script_dir/.venv/bin/python" ]]; then
  python_cmd="$script_dir/.venv/bin/python"
elif [[ -x "$script_dir/venv/Scripts/python.exe" ]]; then
  python_cmd="$script_dir/venv/Scripts/python.exe"
elif [[ -x "$script_dir/venv/bin/python" ]]; then
  python_cmd="$script_dir/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="$(command -v python3)"
else
  echo "Could not find a Python interpreter." >&2
  exit 1
fi

if [[ $# -ne 1 ]]; then
  echo "Usage: ./run.sh <video-name-or-file>" >&2
  exit 1
fi

input="$1"
target="$data_dir/videos/$input"

if [[ ! -f "$target" ]]; then
  for ext in mp4 mkv avi webm mpg; do
    candidate="$data_dir/videos/$input.$ext"
    if [[ -f "$candidate" ]]; then
      target="$candidate"
      break
    fi
  done
fi

if [[ ! -f "$target" ]]; then
  echo "File not found in $data_dir/videos: $input" >&2
  exit 1
fi

mkdir -p "$data_dir/midi" "$data_dir/annotations"

filename="$(basename "$target")"
stem="${filename%.*}"

midi_output="$data_dir/midi/$stem.mid"
json_output="$data_dir/annotations/$stem.json"
ascii_output="$data_dir/annotations/$stem.txt"
html_output="$data_dir/annotations/$stem.html"

"$python_cmd" -m video2midi.v2m "$target" \
  --output-midi "$midi_output" \
  --config "$script_dir/video2midi/.v2m.ini"

if [[ ! -f "$midi_output" ]]; then
  echo "Expected MIDI output was not created: $midi_output" >&2
  exit 1
fi

"$python_cmd" -m midi2annotations.main "$midi_output" --output "$json_output"
"$python_cmd" -m midi2annotations.main "$json_output" --ascii "$ascii_output" --html "$html_output"

echo "Generated:"
echo "  $midi_output"
echo "  $json_output"
echo "  $ascii_output"
echo "  $html_output"
