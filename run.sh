#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./run.sh <video-name-or-file>" >&2
  exit 1
fi

input="$1"
target="./mp4s/$input"

if [ ! -f "$target" ]; then
  for ext in mp4 mkv avi webm mpg; do
    candidate="./mp4s/$input.$ext"
    if [ -f "$candidate" ]; then
      target="$candidate"
      break
    fi
  done
fi

if [ ! -f "$target" ]; then
  echo "File not found in ./mp4s: $input" >&2
  exit 1
fi

exec ./v2m.py "$target"