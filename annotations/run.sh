#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <name>"
  echo "Example: $0 lalaland"
  exit 1
fi

name="$1"
name="${name%.mid}"
name="${name%.MID}"
name="${name%.midi}"
name="${name%.MIDI}"
input_path=""

if [[ -x "$script_dir/venv/Scripts/python.exe" ]]; then
  python_cmd="$script_dir/venv/Scripts/python.exe"
elif [[ -x "$script_dir/venv/bin/python" ]]; then
  python_cmd="$script_dir/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  python_cmd="$(command -v python)"
else
  echo "Could not find a Python interpreter."
  exit 1
fi

normalize_path_for_python() {
  local path="$1"

  if [[ "$python_cmd" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
    wslpath -w "$path"
  else
    printf '%s\n' "$path"
  fi
}

for candidate in \
  "$script_dir/inputs/${name}.MID" \
  "$script_dir/inputs/${name}.mid" \
  "$script_dir/inputs/${name}.midi" \
  "$script_dir/inputs/${name}.MIDI"; do
  if [[ -f "$candidate" ]]; then
    input_path="$candidate"
    break
  fi
done

if [[ -z "$input_path" ]]; then
  echo "Could not find input MIDI for '${name}' in inputs/."
  exit 1
fi

json_output="$script_dir/outputs/${name}.json"
ascii_output="$script_dir/outputs/${name}.txt"
html_output="$script_dir/outputs/${name}.html"

python_input_path="$(normalize_path_for_python "$input_path")"
python_json_output="$(normalize_path_for_python "$json_output")"
python_ascii_output="$(normalize_path_for_python "$ascii_output")"
python_html_output="$(normalize_path_for_python "$html_output")"

"$python_cmd" -m src.main "$python_input_path" --output "$python_json_output"
"$python_cmd" -m src.main "$python_json_output" --ascii "$python_ascii_output" --html "$python_html_output"

echo "Generated:"
echo "  $json_output"
echo "  $ascii_output"
echo "  $html_output"
