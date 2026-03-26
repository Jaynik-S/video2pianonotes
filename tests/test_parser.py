from __future__ import annotations

from pathlib import Path

import pytest

from src.midi_parser import (
    InvalidMidiFileError,
    midi_to_pitch_name,
    normalize_notes,
    parse_midi_file,
    sort_notes,
)
from src.note_schema import ExtractedNote


def make_extracted_note(
    *,
    pitch_midi: int,
    start_sec: float,
    end_sec: float,
    velocity: int = 80,
    extraction_order: int = 0,
) -> ExtractedNote:
    return ExtractedNote(
        pitch_midi=pitch_midi,
        start_sec=start_sec,
        end_sec=end_sec,
        velocity=velocity,
        track_index=0,
        instrument_index=0,
        instrument_name="Acoustic Grand Piano",
        is_drum=False,
        extraction_order=extraction_order,
    )


def test_midi_to_pitch_name_middle_c() -> None:
    assert midi_to_pitch_name(60) == "C4"


def test_sort_notes_is_deterministic() -> None:
    notes = [
        make_extracted_note(pitch_midi=64, start_sec=0.0, end_sec=0.5, extraction_order=1),
        make_extracted_note(pitch_midi=60, start_sec=0.0, end_sec=0.5, extraction_order=2),
        make_extracted_note(pitch_midi=60, start_sec=0.0, end_sec=0.6, extraction_order=0),
    ]

    sorted_notes = sort_notes(notes)
    assert [note.extraction_order for note in sorted_notes] == [2, 0, 1]


def test_normalize_notes_assigns_stable_ids() -> None:
    raw_notes = [
        make_extracted_note(pitch_midi=67, start_sec=1.0, end_sec=1.5, extraction_order=5),
        make_extracted_note(pitch_midi=55, start_sec=0.5, end_sec=0.8, extraction_order=2),
    ]

    normalized = normalize_notes(raw_notes)
    assert [note.id for note in normalized] == [0, 1]
    assert normalized[0].pitch_name == "G3"
    assert normalized[0].duration_sec == pytest.approx(0.3)


def test_parse_midi_file_invalid_path_raises() -> None:
    with pytest.raises(InvalidMidiFileError):
        parse_midi_file("missing.mid")


def test_parse_midi_file_smoke(tmp_path: Path) -> None:
    pretty_midi = pytest.importorskip("pretty_midi")

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    instrument.notes.append(pretty_midi.Note(velocity=96, pitch=60, start=0.0, end=0.5))
    instrument.notes.append(pretty_midi.Note(velocity=88, pitch=64, start=0.02, end=0.6))
    midi.instruments.append(instrument)

    midi_path = tmp_path / "smoke.mid"
    midi.write(str(midi_path))

    extracted_notes, metadata = parse_midi_file(midi_path)

    assert len(extracted_notes) == 2
    assert metadata["source_file"] == "smoke.mid"
    assert extracted_notes[0].pitch_midi == 60
