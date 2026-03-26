"""CLI entrypoint for both MIDI parsing and JSON rendering stages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .chord_grouping import build_chord_groups
from .exporter import build_export_dict, export_to_json
from .hand_inference import infer_hands
from .html_renderer import render_html
from .midi_parser import MidiParserError, normalize_notes, parse_midi_file
from .note_schema import ParseResult, PipelineConfig
from .quantizer import RenderConfig, load_and_quantize_json
from .renderer import render_ascii


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path | None = None,
    config: PipelineConfig | None = None,
) -> dict:
    """Run the full pipeline and optionally export the result to disk."""

    effective_config = config or PipelineConfig()
    extracted_notes, metadata = parse_midi_file(input_path)
    notes = normalize_notes(extracted_notes)
    groups = build_chord_groups(notes, effective_config.group_tolerance_sec)
    infer_hands(notes, groups, effective_config.hand_split_midi)

    result = ParseResult(metadata=metadata, notes=notes, groups=groups)
    payload = build_export_dict(result, effective_config)
    if output_path is not None:
        export_to_json(payload, output_path, pretty=effective_config.pretty_json)
    return payload


def run_render_pipeline(
    input_path: str | Path,
    ascii_output_path: str | Path | None = None,
    html_output_path: str | Path | None = None,
    config: RenderConfig | None = None,
) -> dict[str, str]:
    """Run the second-stage JSON to ASCII/HTML renderer."""

    if ascii_output_path is None and html_output_path is None:
        raise ValueError("At least one render output path must be provided via --ascii or --html")

    effective_config = config or RenderConfig()
    score = load_and_quantize_json(input_path, time_step_sec=effective_config.time_step_sec)

    outputs: dict[str, str] = {}
    if ascii_output_path is not None:
        ascii_text = render_ascii(score, system_width=effective_config.system_width)
        _write_text_output(ascii_output_path, ascii_text)
        outputs["ascii"] = ascii_text
    if html_output_path is not None:
        html_text = render_html(score, system_width=effective_config.system_width)
        _write_text_output(html_output_path, html_text)
        outputs["html"] = html_text
    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for both project stages."""

    parser = argparse.ArgumentParser(
        description=(
            "Parse a MIDI file into note-event JSON, or render stage-one JSON into "
            "aligned ASCII and HTML annotations."
        )
    )
    parser.add_argument("input", help="Path to the input .mid/.midi or stage-one .json file")
    parser.add_argument("--output", help="Path to the output JSON file for MIDI parsing")
    parser.add_argument(
        "--group-tolerance",
        type=float,
        default=0.03,
        help="Maximum onset difference in seconds for grouping notes into a chord",
    )
    parser.add_argument(
        "--hand-split-midi",
        type=int,
        default=60,
        help="Register split threshold used by the RH/LH heuristic",
    )
    parser.add_argument(
        "--pretty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pretty-print the exported JSON",
    )
    parser.add_argument(
        "--include-metadata",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include top-level metadata in the exported JSON",
    )
    parser.add_argument("--ascii", dest="ascii_output", help="Path to the output ASCII annotation")
    parser.add_argument("--html", dest="html_output", help="Path to the output HTML annotation")
    parser.add_argument(
        "--time-step",
        type=float,
        default=0.05,
        help="Fixed time step in seconds used to quantize JSON note starts into columns",
    )
    parser.add_argument(
        "--system-width",
        type=int,
        default=50,
        help="Number of logical columns per wrapped system in ASCII/HTML rendering",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the CLI and return a process exit code."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input)

    try:
        if input_path.suffix.lower() in {".mid", ".midi"}:
            if not args.output:
                raise ValueError("--output is required when the input is a MIDI file")
            config = PipelineConfig(
                group_tolerance_sec=args.group_tolerance,
                hand_split_midi=args.hand_split_midi,
                pretty_json=args.pretty,
                include_metadata=args.include_metadata,
            )
            payload = run_pipeline(args.input, args.output, config=config)
            note_count = len(payload["notes"])
            group_count = len(payload["groups"])
            print(f"Exported {note_count} notes across {group_count} groups to {args.output}")
            return 0

        if input_path.suffix.lower() == ".json":
            render_config = RenderConfig(
                time_step_sec=args.time_step,
                system_width=args.system_width,
            )
            outputs = run_render_pipeline(
                args.input,
                ascii_output_path=args.ascii_output,
                html_output_path=args.html_output,
                config=render_config,
            )
            destinations = []
            if args.ascii_output:
                destinations.append(f"ASCII to {args.ascii_output}")
            if args.html_output:
                destinations.append(f"HTML to {args.html_output}")
            print(f"Rendered {' and '.join(destinations)}")
            return 0

        raise ValueError("Input must be a .mid, .midi, or .json file")
    except (MidiParserError, ValueError, FileNotFoundError) as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")
    except OSError as exc:
        parser.exit(status=1, message=f"Error writing output: {exc}\n")
    return 0


def _write_text_output(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

