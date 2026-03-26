"""Chord grouping based on near-simultaneous note onsets."""

from __future__ import annotations

from .note_schema import ChordGroup, NoteEvent


def group_notes_by_onset(notes: list[NoteEvent], tolerance_sec: float) -> list[list[NoteEvent]]:
    """Cluster notes whose onsets fall within the configured tolerance."""

    if tolerance_sec < 0:
        raise ValueError("group tolerance must be non-negative")

    if not notes:
        return []

    groups: list[list[NoteEvent]] = []
    current_group: list[NoteEvent] = [notes[0]]
    group_anchor_start = notes[0].start_sec

    for note in notes[1:]:
        if note.start_sec - group_anchor_start > tolerance_sec:
            groups.append(_sort_group(current_group))
            current_group = [note]
            group_anchor_start = note.start_sec
        else:
            current_group.append(note)

    groups.append(_sort_group(current_group))
    return groups


def build_chord_groups(notes: list[NoteEvent], tolerance_sec: float) -> list[ChordGroup]:
    """Assign chord ids and build export-friendly group objects."""

    grouped_notes = group_notes_by_onset(notes, tolerance_sec)
    chord_groups: list[ChordGroup] = []

    for onset_rank, group in enumerate(grouped_notes):
        chord_id = onset_rank
        for note in group:
            note.chord_id = chord_id
            note.onset_rank = onset_rank

        group_start = min(note.start_sec for note in group)
        group_end = max(note.end_sec for note in group)
        chord_groups.append(
            ChordGroup(
                chord_id=chord_id,
                start_sec=group_start,
                end_sec=group_end,
                duration_sec=max(0.0, group_end - group_start),
                note_ids=[note.id for note in group],
                pitches_midi=[note.pitch_midi for note in group],
                pitches=[note.pitch_name for note in group],
                hand=None,
                size=len(group),
            )
        )

    return chord_groups


def _sort_group(group: list[NoteEvent]) -> list[NoteEvent]:
    return sorted(group, key=lambda note: (note.pitch_midi, note.id))
