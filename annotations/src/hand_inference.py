"""Right-hand and left-hand inference heuristics."""

from __future__ import annotations

from statistics import mean

from .note_schema import ChordGroup, NoteEvent


def infer_hands(notes: list[NoteEvent], groups: list[ChordGroup], split_midi: int) -> None:
    """Infer RH/LH assignments in-place for note and group records."""

    if not notes or not groups:
        return

    notes_by_group = {
        group.chord_id: sorted(
            [note for note in notes if note.chord_id == group.chord_id],
            key=lambda note: (note.pitch_midi, note.id),
        )
        for group in groups
    }

    lowest_pitches = [min(group.pitches_midi) for group in groups]
    highest_pitches = [max(group.pitches_midi) for group in groups]
    if lowest_pitches and min(lowest_pitches) >= split_midi:
        _assign_all_one_hand(groups, notes_by_group, "RH")
        return
    if highest_pitches and max(highest_pitches) < split_midi:
        _assign_all_one_hand(groups, notes_by_group, "LH")
        return

    single_hand_candidates: dict[int, str] = {}
    for group in groups:
        group_notes = notes_by_group[group.chord_id]
        pitches = [note.pitch_midi for note in group_notes]
        if all(pitch < split_midi for pitch in pitches):
            _assign_group_hand(group, group_notes, "LH")
            single_hand_candidates[group.chord_id] = "LH"
            continue
        if all(pitch >= split_midi for pitch in pitches):
            _assign_group_hand(group, group_notes, "RH")
            single_hand_candidates[group.chord_id] = "RH"
            continue
        _split_group_by_register(group, group_notes, split_midi)

    _smooth_single_hand_groups(groups, notes_by_group, split_midi, single_hand_candidates)


def _assign_all_one_hand(
    groups: list[ChordGroup], notes_by_group: dict[int, list[NoteEvent]], hand: str
) -> None:
    for group in groups:
        _assign_group_hand(group, notes_by_group[group.chord_id], hand)


def _assign_group_hand(group: ChordGroup, group_notes: list[NoteEvent], hand: str) -> None:
    group.hand = hand
    for note in group_notes:
        note.hand = hand


def _split_group_by_register(group: ChordGroup, group_notes: list[NoteEvent], split_midi: int) -> None:
    """Split a mixed-register onset cluster into LH/RH note assignments."""

    group.hand = None
    note_count = len(group_notes)
    midpoint = note_count // 2

    for index, note in enumerate(group_notes):
        if index < midpoint:
            note.hand = "LH"
        elif index > midpoint:
            note.hand = "RH"
        else:
            note.hand = "LH" if note.pitch_midi < split_midi else "RH"


def _smooth_single_hand_groups(
    groups: list[ChordGroup],
    notes_by_group: dict[int, list[NoteEvent]],
    split_midi: int,
    single_hand_candidates: dict[int, str],
) -> None:
    """Reduce isolated hand flips for neighboring single-hand groups near middle C."""

    avg_pitch_by_group = {group.chord_id: mean(group.pitches_midi) for group in groups}
    for index in range(1, len(groups) - 1):
        previous_group = groups[index - 1]
        current_group = groups[index]
        next_group = groups[index + 1]

        previous_hand = single_hand_candidates.get(previous_group.chord_id)
        current_hand = single_hand_candidates.get(current_group.chord_id)
        next_hand = single_hand_candidates.get(next_group.chord_id)

        if not previous_hand or not current_hand or not next_hand:
            continue
        if previous_hand != next_hand or current_hand == previous_hand:
            continue

        avg_pitch = avg_pitch_by_group[current_group.chord_id]
        if abs(avg_pitch - split_midi) > 6:
            continue

        _assign_group_hand(current_group, notes_by_group[current_group.chord_id], previous_hand)
