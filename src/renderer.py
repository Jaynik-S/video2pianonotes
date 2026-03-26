"""ASCII renderer built on top of the fixed-grid quantized score."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .quantizer import QuantizedScore, RenderNote


@dataclass(frozen=True)
class ColumnCell:
    """A single logical time cell for one hand."""

    token: str
    notes: tuple[RenderNote, ...]


@dataclass(frozen=True)
class RenderSystem:
    """A wrapped system containing RH and LH cells plus per-column widths."""

    start_column: int
    rh_cells: tuple[ColumnCell, ...]
    lh_cells: tuple[ColumnCell, ...]
    cell_widths: tuple[int, ...]
    end_time_sec: float


def build_hand_sequence(
    columns: dict[int, list[RenderNote]],
    total_columns: int,
) -> list[ColumnCell]:
    """Build the full logical column sequence for one hand."""

    sequence: list[ColumnCell] = []
    for column_index in range(total_columns):
        notes_in_column = tuple(columns.get(column_index, []))
        token = "".join(note.pitch_label for note in notes_in_column) if notes_in_column else "-"
        sequence.append(ColumnCell(token=token, notes=notes_in_column))
    return sequence


def build_render_systems(score: QuantizedScore, system_width: int) -> list[RenderSystem]:
    """Split the full score into wrapped systems with shared RH/LH column widths."""

    if system_width <= 0:
        raise ValueError("system_width must be greater than zero")

    total_columns = score.total_columns
    if total_columns == 0:
        return [
            RenderSystem(
                start_column=0,
                rh_cells=tuple(),
                lh_cells=tuple(),
                cell_widths=tuple(),
                end_time_sec=0.0,
            )
        ]

    rh_sequence = build_hand_sequence(score.rh_columns, total_columns)
    lh_sequence = build_hand_sequence(score.lh_columns, total_columns)
    duration_sec = _extract_duration_sec(score)

    systems: list[RenderSystem] = []
    for start in range(0, total_columns, system_width):
        rh_chunk = tuple(rh_sequence[start : start + system_width])
        lh_chunk = tuple(lh_sequence[start : start + system_width])
        base_widths = tuple(
            max(len(rh_cell.token), len(lh_cell.token), 1)
            for rh_cell, lh_cell in zip(rh_chunk, lh_chunk)
        )
        widths = tuple(_compact_empty_run_widths(rh_chunk, lh_chunk, base_widths))
        end_time_sec = (start + len(rh_chunk)) * score.time_step_sec
        if duration_sec is not None:
            end_time_sec = min(end_time_sec, duration_sec)
        systems.append(
            RenderSystem(
                start_column=start,
                rh_cells=rh_chunk,
                lh_cells=lh_chunk,
                cell_widths=widths,
                end_time_sec=end_time_sec,
            )
        )
    return systems


def render_ascii(score: QuantizedScore, system_width: int = 50) -> str:
    """Render the quantized score into wrapped ASCII notation."""

    systems = build_render_systems(score, system_width=system_width)
    blocks: list[str] = []
    for system in systems:
        rh_line = _render_ascii_line("RH", system.rh_cells, system.cell_widths)
        lh_line = _render_ascii_line(
            "LH",
            system.lh_cells,
            system.cell_widths,
            suffix=format_elapsed_time(system.end_time_sec),
        )
        blocks.append(f"{rh_line}\n{lh_line}")
    return "\n\n".join(blocks)


def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time as m:ss using floor-to-second semantics."""

    total_seconds = max(0, math.floor(seconds))
    minutes, remainder = divmod(total_seconds, 60)
    return f"{minutes}:{remainder:02d}"


def _render_ascii_line(
    label: str,
    cells: tuple[ColumnCell, ...],
    widths: tuple[int, ...],
    suffix: str | None = None,
) -> str:
    body = "".join(_render_ascii_cell(cell, width) for cell, width in zip(cells, widths))
    rendered = f"{label}:|{body}|"
    if suffix:
        rendered = f"{rendered} {suffix}"
    return rendered


def _render_ascii_cell(cell: ColumnCell, width: int) -> str:
    if not cell.notes:
        return "-" * width
    return f"{cell.token}{'-' * (width - len(cell.token))}"


def _compact_empty_run_widths(
    rh_cells: tuple[ColumnCell, ...],
    lh_cells: tuple[ColumnCell, ...],
    base_widths: tuple[int, ...],
) -> list[int]:
    widths = list(base_widths)
    occupancy = [bool(rh_cell.notes or lh_cell.notes) for rh_cell, lh_cell in zip(rh_cells, lh_cells)]

    if not any(occupancy):
        return [0] * len(widths)

    last_occupied_index = max(index for index, is_occupied in enumerate(occupancy) if is_occupied)
    index = 0
    while index < len(occupancy):
        if occupancy[index]:
            index += 1
            continue

        run_start = index
        while index < len(occupancy) and not occupancy[index]:
            index += 1

        is_leading_run = run_start == 0
        is_trailing_run = run_start > last_occupied_index
        if (is_leading_run or not is_trailing_run) and widths[run_start] > 0:
            widths[run_start] -= 1

    return widths


def _extract_duration_sec(score: QuantizedScore) -> float | None:
    duration_value = score.metadata.get("duration_sec")
    if duration_value is None:
        return None
    try:
        return float(duration_value)
    except (TypeError, ValueError):
        return None
