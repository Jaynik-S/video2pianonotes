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
  echo "Usage: ./run.sh <youtube-url-or-local-video>" >&2
  exit 1
fi

input="$1"
videos_dir="$data_dir/videos"
target=""

is_youtube_url() {
  [[ "$1" =~ ^https?://([[:alnum:]-]+\.)?(youtube\.com|youtu\.be)/ ]]
}

download_youtube_video() {
  if ! "$python_cmd" -m yt_dlp --version >/dev/null 2>&1; then
    echo "yt-dlp is not installed in the selected Python environment." >&2
    exit 1
  fi

  local downloaded_path
  downloaded_path="$(
    "$python_cmd" -m yt_dlp \
      --quiet \
      --no-warnings \
      --no-progress \
      --force-overwrites \
      --paths "home:$videos_dir" \
      --output "%(title)s.%(ext)s" \
      --recode-video mkv \
      --print after_move:filepath \
      "$input"
  )"

  downloaded_path="${downloaded_path%%$'\r'}"
  downloaded_path="${downloaded_path%%$'\n'}"

  if [[ -z "$downloaded_path" || ! -f "$downloaded_path" ]]; then
    echo "yt-dlp did not produce a usable video file in $videos_dir." >&2
    exit 1
  fi

  printf '%s\n' "$downloaded_path"
}

mkdir -p "$videos_dir" "$data_dir/midi" "$data_dir/annotations"

if is_youtube_url "$input"; then
  target="$(download_youtube_video)"
else
  target="$videos_dir/$input"

  if [[ ! -f "$target" ]]; then
    for ext in mp4 mkv avi webm mpg; do
      candidate="$videos_dir/$input.$ext"
      if [[ -f "$candidate" ]]; then
        target="$candidate"
        break
      fi
    done
  fi

  if [[ ! -f "$target" ]]; then
    echo "File not found in $videos_dir: $input" >&2
    exit 1
  fi
fi

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
