"""Core schemas and serialization helpers for the MIDI parsing pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


SECONDS_FIELD_NAMES = {"start_sec", "end_sec", "duration_sec"}


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the MIDI to JSON pipeline."""

    group_tolerance_sec: float = 0.03
    hand_split_midi: int = 60
    pretty_json: bool = True
    include_metadata: bool = True


@dataclass(frozen=True)
class ExtractedNote:
    """Raw note extracted from a MIDI file before normalization."""

    pitch_midi: int
    start_sec: float
    end_sec: float
    velocity: int
    track_index: int
    instrument_index: int
    instrument_name: Optional[str]
    is_drum: bool
    extraction_order: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NoteEvent:
    """Normalized note event used by downstream pipeline stages."""

    id: int
    pitch_midi: int
    pitch_name: str
    start_sec: float
    end_sec: float
    duration_sec: float
    velocity: int
    hand: Optional[str]
    chord_id: int
    track_index: int
    instrument_index: int
    instrument_name: Optional[str]
    onset_rank: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the note event with stable float rounding for JSON."""

        payload = asdict(self)
        return _round_numeric_fields(payload)


@dataclass
class ChordGroup:
    """Near-simultaneous onset cluster."""

    chord_id: int
    start_sec: float
    end_sec: float
    duration_sec: float
    note_ids: list[int]
    pitches_midi: list[int]
    pitches: list[str]
    hand: Optional[str]
    size: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize the chord group with stable float rounding for JSON."""

        payload = asdict(self)
        return _round_numeric_fields(payload)


@dataclass
class ParseResult:
    """Final in-memory representation returned by the pipeline."""

    metadata: dict[str, Any]
    notes: list[NoteEvent]
    groups: list[ChordGroup]


def _round_numeric_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Round exported timing fields without mutating the dataclass instance."""

    rounded: dict[str, Any] = {}
    for key, value in payload.items():
        if key in SECONDS_FIELD_NAMES and isinstance(value, (int, float)):
            rounded[key] = round(float(value), 6)
        else:
            rounded[key] = value
    return rounded
