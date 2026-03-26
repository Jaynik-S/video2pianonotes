from __future__ import annotations

from midi2annotations.html_renderer import render_html
from midi2annotations.quantizer import quantize_note_events


def test_render_html_contains_monospace_layout_and_octave_colors() -> None:
    payload = {
        "notes": [
            {"id": 0, "pitch_name": "C4", "pitch_midi": 60, "start_sec": 0.0, "hand": "RH", "chord_id": 0},
            {"id": 1, "pitch_name": "E4", "pitch_midi": 64, "start_sec": 0.0, "hand": "RH", "chord_id": 0},
            {"id": 2, "pitch_name": "G2", "pitch_midi": 43, "start_sec": 0.0, "hand": "LH", "chord_id": 0},
        ]
    }

    score = quantize_note_events(payload, time_step_sec=0.05)
    html = render_html(score, system_width=10)

    assert "font-family:Consolas, monospace;" in html
    assert "font-size:10pt;" in html
    assert "margin:0;padding:0;line-height:1;" in html
    assert "margin-bottom: 16px" not in html
    assert "Courier New" not in html
    assert "background:#6d9eeb" in html
    assert "background:#ffe599" in html
    assert "font-weight:700" in html
    assert "| 0:00</div>" in html


def test_render_html_inserts_exactly_one_blank_line_between_systems() -> None:
    payload = {
        "notes": [
            {"id": 0, "pitch_name": "C4", "pitch_midi": 60, "start_sec": 0.0, "hand": "RH", "chord_id": 0},
            {"id": 1, "pitch_name": "D4", "pitch_midi": 62, "start_sec": 3.0, "hand": "RH", "chord_id": 1},
        ]
    }

    score = quantize_note_events(payload, time_step_sec=0.05)
    html = render_html(score, system_width=50)

    assert html.count("&#8203;") == 1
