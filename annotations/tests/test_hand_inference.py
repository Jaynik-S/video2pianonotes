from __future__ import annotations

from src.chord_grouping import build_chord_groups
from src.hand_inference import infer_hands
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


def test_low_register_notes_become_left_hand() -> None:
    notes = [make_note(0, 43, 0.0), make_note(1, 47, 0.5)]
    groups = build_chord_groups(notes, tolerance_sec=0.03)

    infer_hands(notes, groups, split_midi=60)

    assert [note.hand for note in notes] == ["LH", "LH"]
    assert [group.hand for group in groups] == ["LH", "LH"]


def test_high_register_notes_become_right_hand() -> None:
    notes = [make_note(0, 72, 0.0), make_note(1, 79, 0.5)]
    groups = build_chord_groups(notes, tolerance_sec=0.03)

    infer_hands(notes, groups, split_midi=60)

    assert [note.hand for note in notes] == ["RH", "RH"]


def test_mixed_dyad_is_split_between_hands() -> None:
    notes = [make_note(0, 55, 0.0), make_note(1, 64, 0.0)]
    groups = build_chord_groups(notes, tolerance_sec=0.03)

    infer_hands(notes, groups, split_midi=60)

    assert notes[0].hand == "LH"
    assert notes[1].hand == "RH"
    assert groups[0].hand is None


def test_single_register_passage_can_resolve_to_one_hand() -> None:
    notes = [make_note(0, 85, 0.0), make_note(1, 88, 0.2), make_note(2, 91, 0.4)]
    groups = build_chord_groups(notes, tolerance_sec=0.03)

    infer_hands(notes, groups, split_midi=60)

    assert all(note.hand == "RH" for note in notes)
