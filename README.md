# video2pianonotes

**video2pianonotes** is a local two-stage pipeline that takes a piano video (or YouTube URL) and produces structured MIDI annotations — all in one command.

It combines two tools:
- [`video2midi`](https://github.com/svsdval/video2midi) *(forked from svsdval)* — converts a piano video into a MIDI file
- [`midi2annotations`](https://github.com/Jaynik-S/PianoAnnotations) *(by Jaynik-S)* — converts that MIDI file into JSON, ASCII, and HTML annotations

---

## Layout
```text
video2pianonotes/
├── video2midi/        # video → MIDI tool (forked from svsdval/video2midi)
├── midi2annotations/  # MIDI → annotations tool (Jaynik-S/PianoAnnotations)
├── data/
│   ├── videos/        # input videos (local or downloaded from YouTube)
│   ├── midi/          # intermediate MIDI files
│   └── annotations/   # final annotation outputs
├── requirements.txt   # merged dependencies for the full pipeline
├── README.md
└── run.sh             # single entrypoint to run the entire pipeline
```

---

## Setup
```bash
python3 -m pip install -r requirements.txt
```

---

## Usage

Pass either a YouTube URL or a local video filename from `data/videos/`:
```bash
./run.sh https://www.youtube.com/watch?v=dQw4w9WgXcQ
./run.sh my-song
./run.sh my-song.mkv
```

---

## Pipeline
```
YouTube URL / local video
        │
        ▼
  [ video2midi ]  →  data/midi/<stem>.mid
        │
        ▼
[ midi2annotations ] →  data/annotations/<stem>.json
                        data/annotations/<stem>.txt
                        data/annotations/<stem>.html
```

- YouTube downloads are handled by `yt-dlp` and saved to `data/videos/` as `.mkv` files
- `video2midi` is interactive — once you complete the MIDI capture step, the annotations stage runs automatically
- All outputs are organized under `data/` so nothing is hardcoded

---

## Credits

- [video2midi](https://github.com/svsdval/video2midi) by [@svsdval](https://github.com/svsdval)
- [PianoAnnotations](https://github.com/Jaynik-S/PianoAnnotations) by [@Jaynik-S](https://github.com/Jaynik-S)