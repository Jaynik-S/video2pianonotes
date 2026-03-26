"""MIDI parsing and note normalization utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .note_schema import ExtractedNote, NoteEvent

try:
    import pretty_midi
except ImportError:  # pragma: no cover - exercised through runtime error path
    pretty_midi = None


PITCH_CLASS_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
SUPPORTED_EXTENSIONS = {".mid", ".midi"}
PIANO_PROGRAMS = set(range(8))


class MidiParserError(Exception):
    """Base exception for MIDI parsing failures."""


class InvalidMidiFileError(MidiParserError):
    """Raised when the input is missing, malformed, or unsupported."""


class EmptyMidiError(MidiParserError):
    """Raised when a MIDI file contains no usable notes."""


def midi_to_pitch_name(midi_note: int) -> str:
    """Convert a MIDI note number into scientific pitch notation."""

    if not 0 <= midi_note <= 127:
        raise ValueError(f"MIDI note must be between 0 and 127, got {midi_note}")

    octave = (midi_note // 12) - 1
    pitch_class = PITCH_CLASS_NAMES[midi_note % 12]
    return f"{pitch_class}{octave}"


def sort_notes(notes: list[Any]) -> list[Any]:
    """Return notes sorted by canonical pipeline order."""

    return sorted(
        notes,
        key=lambda note: (
            float(note.start_sec),
            int(note.pitch_midi),
            float(note.end_sec),
            int(getattr(note, "extraction_order", getattr(note, "id", 0))),
        ),
    )


def parse_midi_file(path: str | Path) -> tuple[list[ExtractedNote], dict[str, Any]]:
    """Parse a MIDI file into raw note records plus file-level metadata."""

    midi_path = Path(path)
    _validate_input_path(midi_path)
    _ensure_pretty_midi_available()

    try:
        midi_data = pretty_midi.PrettyMIDI(str(midi_path))
    except FileNotFoundError as exc:
        raise InvalidMidiFileError(f"MIDI file not found: {midi_path}") from exc
    except Exception as exc:  # pragma: no cover - depends on parser internals
        raise InvalidMidiFileError(f"Failed to parse MIDI file '{midi_path}': {exc}") from exc

    extracted_notes = _extract_notes(midi_data)
    if not extracted_notes:
        raise EmptyMidiError(f"MIDI file contains no note events: {midi_path}")

    metadata = _build_metadata(midi_path, midi_data, extracted_notes)
    return sort_notes(extracted_notes), metadata


def normalize_notes(extracted_notes: list[ExtractedNote]) -> list[NoteEvent]:
    """Normalize raw extracted notes into canonical note events."""

    normalized: list[NoteEvent] = []
    for note_id, raw_note in enumerate(sort_notes(extracted_notes)):
        end_sec = max(raw_note.end_sec, raw_note.start_sec)
        normalized.append(
            NoteEvent(
                id=note_id,
                pitch_midi=raw_note.pitch_midi,
                pitch_name=midi_to_pitch_name(raw_note.pitch_midi),
                start_sec=raw_note.start_sec,
                end_sec=end_sec,
                duration_sec=max(0.0, end_sec - raw_note.start_sec),
                velocity=raw_note.velocity,
                hand=None,
                chord_id=-1,
                track_index=raw_note.track_index,
                instrument_index=raw_note.instrument_index,
                instrument_name=raw_note.instrument_name,
                onset_rank=-1,
                metadata=dict(raw_note.metadata),
            )
        )
    return normalized


def _validate_input_path(midi_path: Path) -> None:
    if midi_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise InvalidMidiFileError(
            f"Expected a .mid or .midi file, got '{midi_path.suffix or '<no extension>'}'"
        )
    if not midi_path.exists():
        raise InvalidMidiFileError(f"MIDI file not found: {midi_path}")


def _ensure_pretty_midi_available() -> None:
    if pretty_midi is None:
        raise MidiParserError(
            "pretty_midi is required to parse MIDI files. Install dependencies from requirements.txt."
        )


def _extract_notes(midi_data: "pretty_midi.PrettyMIDI") -> list[ExtractedNote]:
    all_instruments = list(midi_data.instruments)
    non_drum_notes_exist = any(
        instrument.notes for instrument in all_instruments if not instrument.is_drum
    )

    extracted_notes: list[ExtractedNote] = []
    extraction_order = 0
    for instrument_index, instrument in enumerate(all_instruments):
        if instrument.is_drum and non_drum_notes_exist:
            continue

        instrument_name = _instrument_name(instrument)
        for note in instrument.notes:
            extracted_notes.append(
                ExtractedNote(
                    pitch_midi=int(note.pitch),
                    start_sec=float(note.start),
                    end_sec=float(note.end),
                    velocity=int(note.velocity),
                    track_index=instrument_index,
                    instrument_index=instrument_index,
                    instrument_name=instrument_name,
                    is_drum=bool(instrument.is_drum),
                    extraction_order=extraction_order,
                    metadata={"is_drum": bool(instrument.is_drum)},
                )
            )
            extraction_order += 1
    return extracted_notes


def _build_metadata(
    midi_path: Path,
    midi_data: "pretty_midi.PrettyMIDI",
    extracted_notes: list[ExtractedNote],
) -> dict[str, Any]:
    non_drum_instruments = [inst for inst in midi_data.instruments if not inst.is_drum]
    non_drum_programs = {inst.program for inst in non_drum_instruments}

    return {
        "source_file": midi_path.name,
        "source_path": str(midi_path.resolve()),
        "tempo_estimate_bpm": _safe_estimate_tempo(midi_data),
        "initial_tempo_bpm": _initial_tempo_bpm(midi_data),
        "duration_sec": float(midi_data.get_end_time()),
        "instrument_count": len(midi_data.instruments),
        "is_likely_piano_only": bool(non_drum_instruments)
        and all(program in PIANO_PROGRAMS for program in non_drum_programs),
        "ignored_drum_tracks": not any(note.is_drum for note in extracted_notes)
        and any(inst.is_drum for inst in midi_data.instruments),
    }


def _instrument_name(instrument: "pretty_midi.Instrument") -> str:
    if instrument.is_drum:
        return "Drums"
    return pretty_midi.program_to_instrument_name(instrument.program)


def _safe_estimate_tempo(midi_data: "pretty_midi.PrettyMIDI") -> float | None:
    try:
        return float(midi_data.estimate_tempo())
    except Exception:  # pragma: no cover - pretty_midi can fail on sparse files
        return None


def _initial_tempo_bpm(midi_data: "pretty_midi.PrettyMIDI") -> float | None:
    try:
        _, tempi = midi_data.get_tempo_changes()
    except Exception:  # pragma: no cover - defensive around parser internals
        return None

    if len(tempi) == 0:
        return None
    return float(tempi[0])
