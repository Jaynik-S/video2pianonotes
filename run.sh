#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: ./run.sh <youtube-url-or-local-video> [spacing_reduction]" >&2
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

video_stage="$script_dir/video2midi/run.sh"
annotation_stage="$script_dir/midi2annotations/run.sh"

if [[ ! -f "$video_stage" ]]; then
  echo "Missing stage launcher: $video_stage" >&2
  exit 1
fi

if [[ ! -f "$annotation_stage" ]]; then
  echo "Missing stage launcher: $annotation_stage" >&2
  exit 1
fi

midi_output="$(bash "$video_stage" "$input")"
midi_output="${midi_output%%$'\r'}"
midi_output="${midi_output%%$'\n'}"

if [[ -z "$midi_output" || ! -f "$midi_output" ]]; then
  echo "video2midi did not produce a usable MIDI file." >&2
  exit 1
fi

if [[ -n "$spacing_reduction" ]]; then
  exec bash "$annotation_stage" "$midi_output" "$spacing_reduction"
fi

exec bash "$annotation_stage" "$midi_output"
