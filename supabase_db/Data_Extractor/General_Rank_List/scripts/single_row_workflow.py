#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import cv2

from concatenate_table_rows import (
    RowBox,
    detect_fragments,
    draw_debug_image,
    load_image,
    merge_row_fragments,
    stack_row_crops,
    to_binary,
    write_json,
)


def keep_full_rows(
    merged_rows: list[RowBox],
    *,
    image_width: int,
    min_row_width_ratio: float,
    min_height_ratio: float,
    max_height_ratio: float,
) -> tuple[list[RowBox], dict[str, float] | None]:
    if not merged_rows:
        return [], None

    min_row_width_px = int(image_width * min_row_width_ratio)
    wide_rows = [row for row in merged_rows if row.width >= min_row_width_px]
    if not wide_rows:
        return [], None

    median_height = statistics.median(row.height for row in wide_rows)
    height_filtered = [
        row
        for row in wide_rows
        if median_height * min_height_ratio <= row.height <= median_height * max_height_ratio
    ]
    if not height_filtered:
        height_filtered = wide_rows

    table_left = int(round(statistics.median(row.x1 for row in height_filtered)))
    table_right = int(round(statistics.median(row.x2 for row in height_filtered)))
    normalized_rows = [
        RowBox(
            x1=table_left,
            y1=row.y1,
            x2=table_right,
            y2=row.y2,
            segment_count=row.segment_count,
        )
        for row in height_filtered
    ]

    metrics = {
        "min_row_width_px": float(min_row_width_px),
        "table_left": float(table_left),
        "table_right": float(table_right),
        "median_row_height": float(median_height),
    }
    return normalized_rows, metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Single end-to-end row workflow: detect fragments, merge same-row pieces, "
            "drop broken short rows, and export one stacked training image."
        )
    )
    parser.add_argument("input_image", type=Path, help="Input table image.")
    parser.add_argument(
        "output_training_image",
        type=Path,
        help="Output image that contains only the kept full-width rows stacked vertically.",
    )
    parser.add_argument(
        "--debug-output",
        type=Path,
        default=None,
        help="Optional debug image with raw fragments in red and kept rows in green.",
    )
    parser.add_argument(
        "--rows-json-output",
        type=Path,
        default=None,
        help="Optional JSON output of the final kept rows.",
    )
    parser.add_argument(
        "--horizontal-gap-ratio",
        type=float,
        default=0.05,
        help="Horizontal closing kernel width as a fraction of image width. Default: 0.05",
    )
    parser.add_argument(
        "--min-fragment-width-ratio",
        type=float,
        default=0.04,
        help="Minimum raw fragment width as a fraction of image width. Default: 0.04",
    )
    parser.add_argument(
        "--min-row-width-ratio",
        type=float,
        default=0.60,
        help="Rows narrower than this fraction of image width are removed. Default: 0.60",
    )
    parser.add_argument(
        "--min-fragment-height",
        type=int,
        default=3,
        help="Minimum raw fragment height in pixels. Default: 3",
    )
    parser.add_argument(
        "--y-tolerance",
        type=int,
        default=8,
        help="Maximum center-line drift when merging fragments into one row. Default: 8",
    )
    parser.add_argument(
        "--min-height-ratio",
        type=float,
        default=0.50,
        help="Drop rows shorter than this times the median row height. Default: 0.50",
    )
    parser.add_argument(
        "--max-height-ratio",
        type=float,
        default=2.00,
        help="Drop rows taller than this times the median row height. Default: 2.00",
    )
    parser.add_argument(
        "--stack-padding",
        type=int,
        default=4,
        help="Vertical white padding between stacked rows. Default: 4",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image = load_image(args.input_image)
    binary = to_binary(image)
    image_width = binary.shape[1]

    fragments = detect_fragments(
        binary,
        horizontal_gap_px=max(8, int(image_width * args.horizontal_gap_ratio)),
        min_fragment_width_px=max(8, int(image_width * args.min_fragment_width_ratio)),
        min_fragment_height_px=max(1, args.min_fragment_height),
    )
    merged_rows = merge_row_fragments(fragments, y_tolerance_px=args.y_tolerance)
    kept_rows, metrics = keep_full_rows(
        merged_rows,
        image_width=image_width,
        min_row_width_ratio=args.min_row_width_ratio,
        min_height_ratio=args.min_height_ratio,
        max_height_ratio=args.max_height_ratio,
    )
    if not kept_rows:
        raise RuntimeError(
            "No valid full-width rows were found. Lower `--min-row-width-ratio` or "
            "adjust the fragment thresholds."
        )

    stacked_rows = stack_row_crops(
        image,
        kept_rows,
        padding_px=max(0, args.stack_padding),
    )
    args.output_training_image.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output_training_image), stacked_rows)

    if args.debug_output is not None:
        args.debug_output.parent.mkdir(parents=True, exist_ok=True)
        debug_image = draw_debug_image(image, fragments, kept_rows)
        cv2.imwrite(str(args.debug_output), debug_image)

    if args.rows_json_output is not None:
        write_json(args.rows_json_output, kept_rows)

    print(
        json.dumps(
            {
                "input_image": str(args.input_image),
                "fragment_count": len(fragments),
                "merged_row_candidates": len(merged_rows),
                "kept_full_rows": len(kept_rows),
                "output_training_image": str(args.output_training_image),
                "debug_output": str(args.debug_output) if args.debug_output else None,
                "rows_json_output": str(args.rows_json_output) if args.rows_json_output else None,
                "metrics": metrics,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
