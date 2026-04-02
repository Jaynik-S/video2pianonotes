"""HTML renderer for fixed-grid piano annotations."""

from __future__ import annotations

from html import escape

from .quantizer import QuantizedScore
from .renderer import ColumnCell, build_render_systems_with_spacing, format_elapsed_time


OCTAVE_COLORS = {
    1: "#ea9999",
    2: "#ffe599",
    3: "#ffffff",
    4: "#6d9eeb",
    5: "#8e7cc3",
    6: "#c27ba0",
    7: "#000000",
}

LINE_WRAPPER_STYLE = (
    "margin:0;padding:0;line-height:1;font-family:Consolas, monospace;"
    "font-size:10pt;white-space:pre;"
)


def render_html(
    score: QuantizedScore,
    system_width: int = 50,
    spacing_reduction: int = 0,
) -> str:
    """Render the quantized score into standalone HTML."""

    systems = build_render_systems_with_spacing(
        score,
        system_width=system_width,
        spacing_reduction=spacing_reduction,
    )
    blank_line = f'    <div style="{LINE_WRAPPER_STYLE}">&#8203;</div>'
    line_markup = f"\n{blank_line}\n".join(_render_html_system_lines(system) for system in systems)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Piano Annotation</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: #111111;
    }}
    .score {{
      margin: 0;
      padding: 0;
    }}
    .line-label {{
      font-weight: 700;
    }}
    .note {{
      margin: 0;
      padding: 0;
      border-radius: 0;
    }}
  </style>
</head>
<body>
  <div class="score">
{line_markup}
  </div>
</body>
</html>
"""


def _render_html_system_lines(system) -> str:
    rh_line = _render_html_line("RH", system.rh_cells, system.cell_widths)
    lh_line = _render_html_line(
        "LH",
        system.lh_cells,
        system.cell_widths,
        suffix=format_elapsed_time(system.end_time_sec),
    )
    return f"{rh_line}\n{lh_line}"


def _render_html_line(
    label: str,
    cells: tuple[ColumnCell, ...],
    widths: tuple[int, ...],
    suffix: str | None = None,
) -> str:
    body = "".join(_render_html_cell(cell, width) for cell, width in zip(cells, widths))
    timestamp = escape(f" {suffix}") if suffix else ""
    return (
        f'    <div style="{LINE_WRAPPER_STYLE}"><span class="line-label">{label}:|</span>{body}|'
        f"{timestamp}</div>"
    )


def _render_html_cell(cell: ColumnCell, width: int) -> str:
    if not cell.notes:
        return escape("-" * width)

    is_chord = len(cell.notes) > 1
    rendered_notes = "".join(
        _render_html_note_fragment(note.pitch_label, note.octave, bold=is_chord)
        for note in cell.notes
    )
    filler = "-" * max(0, width - len(cell.token))
    return f"{rendered_notes}{escape(filler)}"


def _render_html_note_fragment(note_label: str, octave: int, bold: bool) -> str:
    background = OCTAVE_COLORS.get(octave, "#d9d9d9")
    foreground = "#ffffff" if background.lower() == "#000000" else "#111111"
    weight = "700" if bold else "400"
    return (
        f'<span class="note" style="background:{background};color:{foreground};'
        f'font-weight:{weight};">{escape(note_label)}</span>'
    )
