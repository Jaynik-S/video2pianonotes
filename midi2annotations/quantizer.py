"""Fixed-grid quantization helpers for stage-two JSON rendering."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PITCH_NAME_PATTERN = re.compile(r"^([A-Ga-g](?:#)?)(-?\d+)$")
VALID_HANDS = {"RH", "LH"}


@dataclass(frozen=True)
class RenderConfig:
    """Configuration shared by ASCII and HTML renderers."""

    time_step_sec: float = 0.05
    system_width: int = 50
    spacing_reduction: int = 0


@dataclass(frozen=True)
class RenderNote:
    """Note event normalized for fixed-grid rendering."""

    id: int
    pitch_midi: int
    pitch_label: str
    octave: int
    hand: str
    chord_id: int
    start_sec: float
    column_index: int


@dataclass
class QuantizedScore:
    """Quantized score representation built from stage-one JSON."""

    source_path: str
    metadata: dict[str, Any]
    time_step_sec: float
    notes: list[RenderNote]
    rh_columns: dict[int, list[RenderNote]]
    lh_columns: dict[int, list[RenderNote]]
    max_column_index: int

    @property
    def total_columns(self) -> int:
        """Return the total number of logical time columns in the score."""

        return self.max_column_index + 1 if self.max_column_index >= 0 else 0


def load_note_event_json(path: str | Path) -> dict[str, Any]:
    """Load the stage-one JSON file from disk."""

    json_path = Path(path)
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Expected a .json file, got '{json_path.suffix or '<no extension>'}'")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if "notes" not in payload or not isinstance(payload["notes"], list):
        raise ValueError("Input JSON must contain a top-level 'notes' array")
    return payload


def quantize_note_events(
    payload: dict[str, Any],
    time_step_sec: float,
    source_path: str = "<memory>",
) -> QuantizedScore:
    """Convert note-event JSON into a fixed-grid quantized score."""

    if time_step_sec <= 0:
        raise ValueError("time_step_sec must be greater than zero")

    quantized_notes: list[RenderNote] = []
    rh_columns: dict[int, list[RenderNote]] = {}
    lh_columns: dict[int, list[RenderNote]] = {}
    max_column_index = -1

    for raw_note in payload.get("notes", []):
        render_note = _build_render_note(raw_note, time_step_sec)
        quantized_notes.append(render_note)
        target_columns = rh_columns if render_note.hand == "RH" else lh_columns
        target_columns.setdefault(render_note.column_index, []).append(render_note)
        max_column_index = max(max_column_index, render_note.column_index)

    for columns in (rh_columns, lh_columns):
        for notes_in_column in columns.values():
            notes_in_column.sort(key=lambda note: (note.pitch_midi, note.id))

    return QuantizedScore(
        source_path=source_path,
        metadata=dict(payload.get("metadata", {})),
        time_step_sec=time_step_sec,
        notes=sorted(quantized_notes, key=lambda note: (note.column_index, note.pitch_midi, note.id)),
        rh_columns=rh_columns,
        lh_columns=lh_columns,
        max_column_index=max_column_index,
    )


def load_and_quantize_json(path: str | Path, time_step_sec: float) -> QuantizedScore:
    """Load a stage-one JSON file and quantize it onto the fixed time grid."""

    payload = load_note_event_json(path)
    return quantize_note_events(payload, time_step_sec=time_step_sec, source_path=str(Path(path).resolve()))


def quantize_start_time(start_sec: float, time_step_sec: float) -> int:
    """Convert a note onset time into a stable column index using half-up rounding."""

    if start_sec < 0:
        raise ValueError("start_sec must be non-negative")
    return int(math.floor((start_sec / time_step_sec) + 0.5))


def normalize_pitch_name(pitch_name: str) -> tuple[str, int]:
    """Convert stage-one pitch names like 'C#4' into ('c#', 4)."""

    match = PITCH_NAME_PATTERN.match(pitch_name)
    if not match:
        raise ValueError(f"Unsupported pitch name format: {pitch_name}")
    note_label, octave = match.groups()
    return note_label.lower(), int(octave)


def _build_render_note(raw_note: dict[str, Any], time_step_sec: float) -> RenderNote:
    try:
        pitch_label, octave = normalize_pitch_name(str(raw_note["pitch_name"]))
        hand = str(raw_note["hand"])
        start_sec = float(raw_note["start_sec"])
        pitch_midi = int(raw_note["pitch_midi"])
        note_id = int(raw_note["id"])
        chord_id = int(raw_note["chord_id"])
    except KeyError as exc:
        raise ValueError(f"Missing required note field: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid note value: {exc}") from exc

    if hand not in VALID_HANDS:
        raise ValueError(f"Unsupported hand value '{hand}'. Expected one of {sorted(VALID_HANDS)}")

    return RenderNote(
        id=note_id,
        pitch_midi=pitch_midi,
        pitch_label=pitch_label,
        octave=octave,
        hand=hand,
        chord_id=chord_id,
        start_sec=start_sec,
        column_index=quantize_start_time(start_sec, time_step_sec),
    )
