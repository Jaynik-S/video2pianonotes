from __future__ import annotations

import json

from src.exporter import build_export_dict, export_to_json
from src.note_schema import ChordGroup, NoteEvent, ParseResult, PipelineConfig


def test_export_dict_contains_metadata_notes_and_groups(tmp_path) -> None:
    note = NoteEvent(
        id=0,
        pitch_midi=60,
        pitch_name="C4",
        start_sec=0.0,
        end_sec=0.5,
        duration_sec=0.5,
        velocity=80,
        hand="RH",
        chord_id=0,
        track_index=0,
        instrument_index=0,
        instrument_name="Acoustic Grand Piano",
        onset_rank=0,
    )
    group = ChordGroup(
        chord_id=0,
        start_sec=0.0,
        end_sec=0.5,
        duration_sec=0.5,
        note_ids=[0],
        pitches_midi=[60],
        pitches=["C4"],
        hand="RH",
        size=1,
    )
    result = ParseResult(
        metadata={"source_file": "example.mid", "source_path": "example.mid", "duration_sec": 0.5},
        notes=[note],
        groups=[group],
    )
    config = PipelineConfig()

    payload = build_export_dict(result, config)
    export_path = tmp_path / "output.json"
    export_to_json(payload, export_path, pretty=True)

    written = json.loads(export_path.read_text(encoding="utf-8"))
    assert set(written) == {"metadata", "notes", "groups"}
    assert written["metadata"]["note_count"] == 1
    assert written["metadata"]["group_count"] == 1
