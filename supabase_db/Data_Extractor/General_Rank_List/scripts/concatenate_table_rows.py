#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - runtime dependency check
    cv2 = None
    np = None


@dataclass
class RowBox:
    x1: int
    y1: int
    x2: int
    y2: int
    segment_count: int = 1

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2.0


def require_opencv() -> None:
    if cv2 is None or np is None:
        raise RuntimeError(
            "This script requires `opencv-python` and `numpy`. "
            "Install them before running the row concatenation utility."
        )


def load_image(path: Path) -> np.ndarray:
    require_opencv()
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Unable to read image: {path}")
    return image


def to_binary(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    return binary


def detect_fragments(
    binary: np.ndarray,
    *,
    horizontal_gap_px: int,
    min_fragment_width_px: int,
    min_fragment_height_px: int,
) -> list[RowBox]:
    # Close small horizontal gaps so split row pieces become one candidate group.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_gap_px, 3))
    connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    num_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
        connected,
        connectivity=8,
    )

    boxes: list[RowBox] = []
    for label_index in range(1, num_labels):
        x, y, width, height, _area = stats[label_index]
        if width < min_fragment_width_px or height < min_fragment_height_px:
            continue
        boxes.append(RowBox(x1=int(x), y1=int(y), x2=int(x + width), y2=int(y + height)))

    return sorted(boxes, key=lambda box: (box.y1, box.x1))


def same_row(left: RowBox, right: RowBox, *, y_tolerance_px: int) -> bool:
    overlap = min(left.y2, right.y2) - max(left.y1, right.y1)
    if overlap > 0:
        return True
    return abs(left.center_y - right.center_y) <= y_tolerance_px


def merge_row_fragments(
    fragments: list[RowBox],
    *,
    y_tolerance_px: int,
) -> list[RowBox]:
    if not fragments:
        return []

    groups: list[list[RowBox]] = []
    current_group: list[RowBox] = [fragments[0]]

    for fragment in fragments[1:]:
        anchor = current_group[-1]
        if same_row(anchor, fragment, y_tolerance_px=y_tolerance_px):
            current_group.append(fragment)
            continue
        groups.append(current_group)
        current_group = [fragment]

    groups.append(current_group)

    merged: list[RowBox] = []
    for group in groups:
        merged.append(
            RowBox(
                x1=min(box.x1 for box in group),
                y1=min(box.y1 for box in group),
                x2=max(box.x2 for box in group),
                y2=max(box.y2 for box in group),
                segment_count=len(group),
            )
        )
    return merged


def normalize_rows(
    merged_rows: list[RowBox],
    *,
    image_width: int,
    min_row_width_ratio: float,
) -> tuple[list[RowBox], tuple[int, int] | None]:
    if not merged_rows:
        return [], None

    min_row_width_px = int(image_width * min_row_width_ratio)
    keepers = [row for row in merged_rows if row.width >= min_row_width_px]
    if not keepers:
        return [], None

    table_left = int(round(statistics.median(row.x1 for row in keepers)))
    table_right = int(round(statistics.median(row.x2 for row in keepers)))

    normalized = [
        RowBox(
            x1=table_left,
            y1=row.y1,
            x2=table_right,
            y2=row.y2,
            segment_count=row.segment_count,
        )
        for row in keepers
    ]
    return normalized, (table_left, table_right)


def draw_debug_image(
    image: np.ndarray,
    fragments: list[RowBox],
    normalized_rows: list[RowBox],
) -> np.ndarray:
    debug = image.copy()

    # Raw fragments in red.
    for box in fragments:
        cv2.rectangle(debug, (box.x1, box.y1), (box.x2, box.y2), (0, 0, 255), 1)

    # Final full-width rows in green.
    for row in normalized_rows:
        cv2.rectangle(debug, (row.x1, row.y1), (row.x2, row.y2), (0, 255, 0), 2)

    return debug


def render_clean_mask(
    image_shape: tuple[int, int, int],
    normalized_rows: list[RowBox],
) -> np.ndarray:
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    for row in normalized_rows:
        cv2.rectangle(mask, (row.x1, row.y1), (row.x2, row.y2), 255, thickness=-1)
    return mask


def stack_row_crops(
    image: np.ndarray,
    normalized_rows: list[RowBox],
    *,
    padding_px: int,
) -> np.ndarray:
    row_crops = [image[row.y1 : row.y2, row.x1 : row.x2].copy() for row in normalized_rows]
    if not row_crops:
        raise RuntimeError("No rows available to stack.")

    max_width = max(crop.shape[1] for crop in row_crops)
    channels = row_crops[0].shape[2]
    background = np.full((1, max_width, channels), 255, dtype=np.uint8)
    stacked_parts: list[np.ndarray] = []

    for index, crop in enumerate(row_crops):
        if crop.shape[1] < max_width:
            pad_width = max_width - crop.shape[1]
            crop = cv2.copyMakeBorder(
                crop,
                0,
                0,
                0,
                pad_width,
                borderType=cv2.BORDER_CONSTANT,
                value=(255, 255, 255),
            )
        stacked_parts.append(crop)
        if padding_px > 0 and index < len(row_crops) - 1:
            stacked_parts.append(np.repeat(background, padding_px, axis=0))

    return np.vstack(stacked_parts)


def write_json(path: Path, rows: list[RowBox]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(row) | {"width": row.width, "height": row.height} for row in rows]
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Concatenate partial table-row fragments into full-width rows and "
            "remove short row fragments."
        )
    )
    parser.add_argument("input_image", type=Path, help="Input table image.")
    parser.add_argument(
        "--debug-output",
        type=Path,
        required=True,
        help="Output image with raw fragments in red and final rows in green.",
    )
    parser.add_argument(
        "--clean-mask-output",
        type=Path,
        default=None,
        help="Optional binary mask that contains only the final full-width rows.",
    )
    parser.add_argument(
        "--stacked-rows-output",
        type=Path,
        default=None,
        help=(
            "Optional training image made by vertically stacking only the kept full-width rows."
        ),
    )
    parser.add_argument(
        "--rows-json-output",
        type=Path,
        default=None,
        help="Optional JSON file with the final row bounding boxes.",
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
        help=(
            "Final merged rows narrower than this fraction of image width are removed. "
            "Default: 0.60"
        ),
    )
    parser.add_argument(
        "--min-fragment-height",
        type=int,
        default=3,
        help="Minimum fragment height in pixels. Default: 3",
    )
    parser.add_argument(
        "--y-tolerance",
        type=int,
        default=8,
        help="Maximum center-line drift when merging fragments into one row. Default: 8",
    )
    parser.add_argument(
        "--stack-padding",
        type=int,
        default=4,
        help="Vertical white padding between stacked training rows. Default: 4",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image = load_image(args.input_image)
    binary = to_binary(image)
    image_height, image_width = binary.shape

    fragments = detect_fragments(
        binary,
        horizontal_gap_px=max(8, int(image_width * args.horizontal_gap_ratio)),
        min_fragment_width_px=max(8, int(image_width * args.min_fragment_width_ratio)),
        min_fragment_height_px=max(1, args.min_fragment_height),
    )
    merged_rows = merge_row_fragments(fragments, y_tolerance_px=args.y_tolerance)
    normalized_rows, _table_span = normalize_rows(
        merged_rows,
        image_width=image_width,
        min_row_width_ratio=args.min_row_width_ratio,
    )

    if not normalized_rows:
        raise RuntimeError(
            "No full-width rows were found. Lower `--min-row-width-ratio` or "
            "`--min-fragment-width-ratio`, or increase `--horizontal-gap-ratio`."
        )

    args.debug_output.parent.mkdir(parents=True, exist_ok=True)
    debug = draw_debug_image(image, fragments, normalized_rows)
    cv2.imwrite(str(args.debug_output), debug)

    if args.clean_mask_output is not None:
        args.clean_mask_output.parent.mkdir(parents=True, exist_ok=True)
        clean_mask = render_clean_mask(image.shape, normalized_rows)
        cv2.imwrite(str(args.clean_mask_output), clean_mask)

    if args.stacked_rows_output is not None:
        args.stacked_rows_output.parent.mkdir(parents=True, exist_ok=True)
        stacked_rows = stack_row_crops(
            image,
            normalized_rows,
            padding_px=max(0, args.stack_padding),
        )
        cv2.imwrite(str(args.stacked_rows_output), stacked_rows)

    if args.rows_json_output is not None:
        write_json(args.rows_json_output, normalized_rows)

    print(
        json.dumps(
            {
                "input_image": str(args.input_image),
                "fragment_count": len(fragments),
                "merged_row_candidates": len(merged_rows),
                "kept_full_rows": len(normalized_rows),
                "debug_output": str(args.debug_output),
                "clean_mask_output": str(args.clean_mask_output) if args.clean_mask_output else None,
                "stacked_rows_output": str(args.stacked_rows_output) if args.stacked_rows_output else None,
                "rows_json_output": str(args.rows_json_output) if args.rows_json_output else None,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
