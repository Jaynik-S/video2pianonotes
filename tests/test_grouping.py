from __future__ import annotations

from src.chord_grouping import build_chord_groups, group_notes_by_onset
from src.note_schema import NoteEvent


def make_note(
    note_id: int,
    pitch_midi: int,
    start_sec: float,
    end_sec: float = 0.5,
) -> NoteEvent:
    return NoteEvent(
        id=note_id,
        pitch_midi=pitch_midi,
        pitch_name="X",
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=end_sec - start_sec,
        velocity=80,
        hand=None,
        chord_id=-1,
        track_index=0,
        instrument_index=0,
        instrument_name="Acoustic Grand Piano",
        onset_rank=-1,
    )


def test_group_notes_by_onset_within_tolerance() -> None:
    notes = [
        make_note(0, 60, 0.0),
        make_note(1, 67, 0.02),
        make_note(2, 55, 0.5),
    ]

    groups = group_notes_by_onset(notes, tolerance_sec=0.03)
    assert len(groups) == 2
    assert [note.id for note in groups[0]] == [0, 1]


def test_group_notes_by_onset_splits_beyond_tolerance() -> None:
    notes = [
        make_note(0, 60, 0.0),
        make_note(1, 64, 0.031),
    ]

    groups = group_notes_by_onset(notes, tolerance_sec=0.03)
    assert len(groups) == 2


def test_build_chord_groups_orders_low_to_high_and_assigns_ids() -> None:
    notes = [
        make_note(0, 72, 0.0),
        make_note(1, 48, 0.0),
        make_note(2, 60, 0.5),
    ]

    chord_groups = build_chord_groups(notes, tolerance_sec=0.03)

    assert len(chord_groups) == 2
    assert chord_groups[0].pitches_midi == [48, 72]
    assert notes[0].chord_id == 0
    assert notes[1].chord_id == 0
    assert notes[2].chord_id == 1
