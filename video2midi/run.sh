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

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <youtube-url-or-local-video>" >&2
  exit 1
fi

input="$1"
data_dir="$repo_root/data"
videos_dir="$data_dir/videos"
midi_dir="$data_dir/midi"

is_youtube_url() {
  [[ "$1" =~ ^https?://([[:alnum:]-]+\.)?(youtube\.com|youtu\.be)/ ]]
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
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

probe_primary_video_codec() {
  ffprobe \
    -v error \
    -select_streams v:0 \
    -show_entries stream=codec_name \
    -of default=noprint_wrappers=1:nokey=1 \
    "$1" 2>/dev/null | head -n 1
}

normalize_for_opencv() {
  local source_video="$1"
  local normalized_dir="$videos_dir/.normalized"
  local codec_name=""
  local normalized_path="$normalized_dir/$(basename "$source_video").opencv.mkv"
  local temp_path=""

  require_command ffprobe
  require_command ffmpeg

  codec_name="$(probe_primary_video_codec "$source_video" | tr '[:upper:]' '[:lower:]')"
  if [[ -n "$codec_name" && "$codec_name" != "av1" ]]; then
    printf '%s\n' "$source_video"
    return
  fi

  mkdir -p "$normalized_dir"

  if [[ -f "$normalized_path" && "$normalized_path" -nt "$source_video" ]]; then
    printf '%s\n' "$normalized_path"
    return
  fi

  temp_path="$(mktemp "$normalized_dir/$(basename "$source_video").opencv.tmp.XXXXXX.mkv")"
  echo "Creating OpenCV-compatible working copy for $(basename "$source_video")" >&2

  if ! ffmpeg \
    -hide_banner \
    -loglevel error \
    -y \
    -i "$source_video" \
    -map 0:v:0 \
    -an \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -f matroska \
    "$temp_path"; then
    rm -f "$temp_path"
    echo "ffmpeg failed to create an OpenCV-compatible working copy for $source_video" >&2
    exit 1
  fi

  mv -f "$temp_path" "$normalized_path"
  printf '%s\n' "$normalized_path"
}

sync_sidecar_to_working_copy() {
  local original_video="$1"
  local working_video="$2"
  local original_sidecar="${original_video}.ini"
  local working_sidecar="${working_video}.ini"

  if [[ "$original_video" == "$working_video" ]]; then
    return
  fi

  if [[ -f "$original_sidecar" && ( ! -f "$working_sidecar" || "$original_sidecar" -nt "$working_sidecar" ) ]]; then
    cp -f "$original_sidecar" "$working_sidecar"
  fi
}

sync_sidecar_from_working_copy() {
  local original_video="$1"
  local working_video="$2"
  local original_sidecar="${original_video}.ini"
  local working_sidecar="${working_video}.ini"

  if [[ "$original_video" == "$working_video" ]]; then
    return
  fi

  if [[ -f "$working_sidecar" && ( ! -f "$original_sidecar" || "$working_sidecar" -nt "$original_sidecar" ) ]]; then
    cp -f "$working_sidecar" "$original_sidecar"
  fi
}

resolve_video_input() {
  local raw_input="$1"
  local candidate=""

  if is_youtube_url "$raw_input"; then
    download_youtube_video
    return
  fi

  if [[ -f "$raw_input" ]]; then
    candidate="$raw_input"
  elif [[ -f "$caller_cwd/$raw_input" ]]; then
    candidate="$caller_cwd/$raw_input"
  elif [[ -f "$repo_root/$raw_input" ]]; then
    candidate="$repo_root/$raw_input"
  elif [[ -f "$videos_dir/$raw_input" ]]; then
    candidate="$videos_dir/$raw_input"
  else
    for ext in mp4 mkv avi webm mpg; do
      if [[ -f "$videos_dir/$raw_input.$ext" ]]; then
        candidate="$videos_dir/$raw_input.$ext"
        break
      fi
    done
  fi

  if [[ -z "$candidate" ]]; then
    echo "File not found: $raw_input" >&2
    echo "Searched current path, repo root, and $videos_dir." >&2
    exit 1
  fi

  printf '%s\n' "$candidate"
}

mkdir -p "$videos_dir" "$midi_dir"

original_target="$(resolve_video_input "$input")"
working_target="$(normalize_for_opencv "$original_target")"

sync_sidecar_to_working_copy "$original_target" "$working_target"

filename="$(basename "$original_target")"
stem="${filename%.*}"
midi_output="$midi_dir/$stem.mid"

video2midi_status=0
"$python_cmd" -m video2midi.v2m "$working_target" \
  --output-midi "$midi_output" \
  --config "$script_dir/.v2m.ini" \
  1>&2 || video2midi_status=$?

sync_sidecar_from_working_copy "$original_target" "$working_target"

if [[ $video2midi_status -ne 0 ]]; then
  exit "$video2midi_status"
fi

if [[ ! -f "$midi_output" ]]; then
  echo "Expected MIDI output was not created: $midi_output" >&2
  exit 1
fi

printf '%s\n' "$midi_output"
