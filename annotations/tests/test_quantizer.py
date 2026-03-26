from __future__ import annotations

import json

from src.quantizer import (
    load_and_quantize_json,
    normalize_pitch_name,
    quantize_note_events,
    quantize_start_time,
)


def sample_payload() -> dict:
    return {
        "metadata": {"source_file": "example.json"},
        "notes": [
            {"id": 0, "pitch_name": "F4", "pitch_midi": 65, "start_sec": 0.0, "hand": "RH", "chord_id": 0},
            {"id": 1, "pitch_name": "G#2", "pitch_midi": 44, "start_sec": 0.0, "hand": "LH", "chord_id": 0},
            {"id": 2, "pitch_name": "D#3", "pitch_midi": 51, "start_sec": 0.0, "hand": "LH", "chord_id": 0},
            {"id": 3, "pitch_name": "F#3", "pitch_midi": 54, "start_sec": 0.0, "hand": "LH", "chord_id": 0},
            {"id": 4, "pitch_name": "D#4", "pitch_midi": 63, "start_sec": 0.3, "hand": "RH", "chord_id": 1},
        ],
    }


def test_normalize_pitch_name_returns_lowercase_name_and_octave() -> None:
    assert normalize_pitch_name("C#4") == ("c#", 4)


def test_quantize_start_time_uses_stable_half_up_rounding() -> None:
    assert quantize_start_time(0.024, 0.05) == 0
    assert quantize_start_time(0.025, 0.05) == 1


def test_quantize_note_events_builds_separate_hand_columns() -> None:
    score = quantize_note_events(sample_payload(), time_step_sec=0.05)

    assert score.total_columns == 7
    assert [note.pitch_label for note in score.rh_columns[0]] == ["f"]
    assert [note.pitch_label for note in score.lh_columns[0]] == ["g#", "d#", "f#"]
    assert [note.pitch_label for note in score.rh_columns[6]] == ["d#"]


def test_load_and_quantize_json_reads_payload_from_disk(tmp_path) -> None:
    json_path = tmp_path / "sample.json"
    json_path.write_text(json.dumps(sample_payload()), encoding="utf-8")

    score = load_and_quantize_json(json_path, time_step_sec=0.05)

    assert score.source_path.endswith("sample.json")
    assert score.metadata["source_file"] == "example.json"
