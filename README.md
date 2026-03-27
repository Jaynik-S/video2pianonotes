# video2pianonotes

`video2pianonotes` is a local two-stage pipeline:

1. `video2midi/` converts an input piano video into MIDI.
2. `midi2annotations/` converts that MIDI into JSON, ASCII, and HTML annotations.

## Layout

```text
video2pianonotes/
├── video2midi/        # video -> MIDI tool
├── midi2annotations/  # MIDI -> annotations tool
├── data/
│   ├── videos/        # input videos
│   ├── midi/          # intermediate MIDI files
│   └── annotations/   # final annotation outputs
├── requirements.txt   # merged pipeline dependencies
└── run.sh             # unified pipeline entrypoint
```

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Pass either a YouTube URL or an existing local video name from `data/videos/`:

```bash
./run.sh <youtube-url-or-local-video>
```

Examples:

```bash
./run.sh https://www.youtube.com/watch?v=dQw4w9WgXcQ
./run.sh my-song
./run.sh my-song.mkv
```

The pipeline writes:

- `data/videos/<title>.mkv` for YouTube downloads
- `data/midi/<stem>.mid`
- `data/annotations/<stem>.json`
- `data/annotations/<stem>.txt`
- `data/annotations/<stem>.html`

YouTube downloads are handled by `yt-dlp` in the root launcher and are saved into `data/videos/` as `.mkv` files. `video2midi` remains interactive. Once you finish the MIDI capture step and the target MIDI exists, the annotations stage runs automatically.
