"""JSON export utilities for parsed MIDI note events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .note_schema import ParseResult, PipelineConfig


def build_export_dict(result: ParseResult, config: PipelineConfig) -> dict[str, Any]:
    """Convert the in-memory parse result into a JSON-ready dictionary."""

    payload: dict[str, Any] = {
        "notes": [note.to_dict() for note in result.notes],
        "groups": [group.to_dict() for group in result.groups],
    }
    if config.include_metadata:
        metadata = dict(result.metadata)
        metadata.update(
            {
                "note_count": len(result.notes),
                "group_count": len(result.groups),
                "group_tolerance_sec": round(config.group_tolerance_sec, 6),
                "hand_split_midi": config.hand_split_midi,
            }
        )
        for key in ("tempo_estimate_bpm", "initial_tempo_bpm", "duration_sec"):
            if isinstance(metadata.get(key), (float, int)):
                metadata[key] = round(float(metadata[key]), 6)
        payload["metadata"] = metadata
    return payload


def export_to_json(data: dict[str, Any], output_path: str | Path, pretty: bool = True) -> None:
    """Persist JSON output to disk."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(data, handle, indent=2, sort_keys=False)
            handle.write("\n")
        else:
            json.dump(data, handle, separators=(",", ":"), sort_keys=False)
