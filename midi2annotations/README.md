# Piano Annotations (MIDI → RH/LH note timeline)

This tool turns a piano MIDI file into a beginner-friendly “what to play when” annotation: a time-aligned stream of note/chord labels for the right hand and left hand, rendered as monospaced ASCII or HTML.

Under the hood it runs in two stages:

1) **MIDI → JSON (note events + chord groups + hand labels)**
- Parses MIDI into per-note timing/velocity (via `pretty_midi`).
- Normalizes notes and clusters near-simultaneous onsets into chord groups (`--group-tolerance`).
- Assigns each group/note to `RH`/`LH` using a simple register split + smoothing (`--hand-split-midi`).
- Exports a stable JSON payload (`notes`, `groups`, optional `metadata`).

2) **JSON → aligned annotation (ASCII / HTML)**
- Quantizes note starts onto a fixed time grid (`--time-step`) so both hands share the same columns.
- Pads each column to the widest token across RH/LH so the two lines stay visually aligned.
- Wraps into fixed-width “systems” (`--system-width`) and emits ASCII and/or HTML.

## Quick start (Requires Python 3.9+.)

```bash
python -m pip install -r requirements.txt

# Stage 1: MIDI -> JSON
python -m src.main inputs/Mariage.MID --output outputs/mariage.json

# Stage 2: JSON -> ASCII/HTML
python -m src.main outputs/mariage.json --ascii outputs/mariage.txt --html outputs/mariage.html
```

## Sample run with `run.sh`

If your MIDI file is at `inputs/Mariage.MID`, you can run the full pipeline with:

```bash
bash ./run.sh Mariage
```

This will generate:

```text
outputs/Mariage.json
outputs/Mariage.txt
outputs/Mariage.html
```

You can also pass an optional spacing reduction value for tighter rendered output:

```bash
bash ./run.sh Mariage -2
```

Example ASCII system:

```text
RH:|f-------f--d#----|
LH:|g#d#f#---c#---g#c| 0:00
```

## Project layout

- `src/main.py` exposes both CLIs: MIDI→JSON and JSON→ASCII/HTML.
- `src/midi_parser.py` loads MIDI data with `pretty_midi` and extracts note-level timing.
- `src/chord_grouping.py` groups near-simultaneous onsets into deterministic chord groups.
- `src/hand_inference.py` applies a replaceable RH/LH heuristic.
- `src/exporter.py` builds and writes the final JSON payload.
- `src/note_schema.py` defines the dataclasses used across the pipeline.
- `src/quantizer.py` maps stage-one JSON onto a fixed time grid for aligned rendering.
- `src/renderer.py` renders aligned ASCII output from the fixed grid.
- `src/html_renderer.py` renders the same layout as monospaced HTML with octave colors.

## CLI knobs (the ones you’ll actually tweak)

- `--group-tolerance` (seconds): how close onsets must be to be treated as a chord.
- `--hand-split-midi` (MIDI note number): split point for the RH/LH heuristic (default `60` = middle C).
- `--time-step` (seconds): grid size for rendering; smaller = more columns, higher fidelity.
- `--system-width` (columns): how wide each wrapped system is in ASCII/HTML.

## Output JSON (high level)

The stage-one JSON is meant to be easy to consume for downstream renderers.

- Top-level keys: `notes`, `groups`, and optional `metadata`.
- `notes[]`: `pitch_midi`, `pitch_name`, `start_sec`, `end_sec`, `velocity`, `hand`, `chord_id`, plus source fields.
- `groups[]`: onset clusters with `start_sec`/`end_sec`, the `note_ids`, and the rendered pitch labels.

Schemas live in `src/note_schema.py`.

## Hand labeling notes

Hand inference is intentionally simple and replaceable (`src/hand_inference.py`):
- below the split → `LH`, at/above the split → `RH`
- mixed-register chords are split low-to-high
- a neighbor-smoothing pass reduces isolated flips near the split

Limitations: no voice separation; cross-hand passages and sustained overlaps can be mislabeled.

## Technical details

### Stage 1: MIDI → JSON (how parsing/export works)

- MIDI is loaded with `pretty_midi.PrettyMIDI(...)`, then each instrument’s `notes` are walked.
- Drum tracks are skipped when there are any non-drum notes (so percussion doesn’t pollute pitch output).
- Each extracted note becomes an `ExtractedNote` with `pitch_midi`, `start_sec`, `end_sec`, `velocity`, and instrument metadata.
- Notes are normalized into `NoteEvent` records:
  - stable sort order: `(start_sec, pitch_midi, end_sec, extraction_order)`
  - `pitch_name` is computed (e.g. `60` → `C4`), `duration_sec` is `max(0, end-start)`
- Chord grouping uses an onset “anchor” time:
  - while `note.start_sec - anchor_start <= group_tolerance`, notes stay in the same onset group
  - each onset group gets a `chord_id` (equal to its `onset_rank`), and a `ChordGroup` is exported
- Hand inference works at the onset-group level first, then fills per-note labels:
  - fast-path: if *all* groups sit above the split → everything `RH`; if *all* groups sit below → everything `LH`
  - single-register groups become `RH`/`LH` directly; mixed-register groups are split low-to-high by pitch
  - for odd-sized mixed groups, the middle note is assigned based on which side of `hand_split_midi` it’s on
  - a neighbor-smoothing pass can re-label an isolated flip when the previous and next groups agree and the current group’s average pitch is near the split (±6 semitones)
- Export builds `notes[]` / `groups[]`, and optionally adds derived `metadata` (`note_count`, `group_count`, config values, rounded timing fields).

### Stage 2: JSON → ASCII/HTML (how rendering works)

- The stage-one JSON is validated (must contain a top-level `notes` array).
- Each note is converted into a `RenderNote` and assigned to a column index using half-up rounding:
  - `column_index = floor((start_sec / time_step_sec) + 0.5)`
- Notes are bucketed into `rh_columns` / `lh_columns` by `hand`, then each column becomes a “cell” token:
  - empty column → `-`
  - non-empty column → concatenation of pitch labels (e.g. `c#e`)
- Systems are wrapped to `system_width` columns; per-column widths are shared across RH/LH:
  - `width[i] = max(len(rh_token), len(lh_token), 1)`
  - a small compaction pass removes exactly one dash from fully empty leading or interior runs (keeping RH/LH aligned)
- ASCII rendering writes `RH:|...|` and `LH:|...| m:ss` (timestamp is the system end time).
- HTML rendering uses the same cells, but renders each note label as a `<span>` with octave-based background color; chords are bolded.
