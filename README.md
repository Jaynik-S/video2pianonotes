# video2pianonotes

`video2pianonotes` is a local two-stage pipeline:

1. `video2midi/` converts an input piano video into MIDI.
2. `midi2annotations/` converts that MIDI into JSON, ASCII, and HTML annotations.

## Layout

```text
video2pianonotes/
├── video2midi/        # video -> MIDI tool
├── midi2annotations/  # MIDI -> annotations tool
├── mp4s/              # input videos
├── midi/              # intermediate MIDI files
├── annotations/       # final annotation outputs
├── requirements.txt   # merged pipeline dependencies
└── run.sh             # unified pipeline entrypoint
```

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Place a video in `mp4s/`, then run:

```bash
./run.sh <video-name-or-file>
```

Examples:

```bash
./run.sh my-song
./run.sh my-song.mp4
```

The pipeline writes:

- `midi/<stem>.mid`
- `annotations/<stem>.json`
- `annotations/<stem>.txt`
- `annotations/<stem>.html`

`video2midi` remains interactive. Once you finish the MIDI capture step and the target MIDI exists, the annotations stage runs automatically.
