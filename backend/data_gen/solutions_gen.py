#!/usr/bin/env python3
"""
Generate rectpack-based packing “solutions” for the images in ./images.

For every source PNG (with five colored boxes) we:
1. Detect the rectangles by color.
2. Feed their widths/heights to rectpack to obtain a compact packing.
3. Render the packed layout into ./solutions (mirror filenames).

Usage:
    python solutions_gen.py
    python solutions_gen.py --source images --output solutions --limit 10
"""

import argparse
import math
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw

try:
    from rectpack import newPacker
except ImportError as exc:  # pragma: no cover - fail fast when dependency missing
    raise SystemExit(
        "rectpack is required. Install it with `pip install rectpack`."
    ) from exc

# Colors used in the generated datasets
COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
}
COLOR_LOOKUP = {rgb: name for name, rgb in COLORS.items()}
COLOR_ORDER = list(COLORS.keys())

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
OUTLINE_WIDTH = 2  # matches generate_images.py


def extract_boxes(image_path: Path) -> List[Dict[str, int]]:
    """Read an existing image and recover the colored rectangles."""
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()

    bounds = {
        name: {"min_x": width, "max_x": -1, "min_y": height, "max_y": -1}
        for name in COLORS
    }

    for y in range(height):
        for x in range(width):
            color_name = COLOR_LOOKUP.get(pixels[x, y])
            if color_name is None:
                continue
            data = bounds[color_name]
            if x < data["min_x"]:
                data["min_x"] = x
            if x > data["max_x"]:
                data["max_x"] = x
            if y < data["min_y"]:
                data["min_y"] = y
            if y > data["max_y"]:
                data["max_y"] = y

    boxes: List[Dict[str, int]] = []
    for color_name, data in bounds.items():
        if data["max_x"] == -1:
            print(
                f"Warning: {color_name} pixels not found in {image_path.name}; "
                "skipping this rectangle."
            )
            continue

        min_x = max(data["min_x"] - OUTLINE_WIDTH, 0)
        min_y = max(data["min_y"] - OUTLINE_WIDTH, 0)
        max_x = min(data["max_x"] + OUTLINE_WIDTH, width - 1)
        max_y = min(data["max_y"] + OUTLINE_WIDTH, height - 1)

        boxes.append(
            {
                "color_name": color_name,
                "color": COLORS[color_name],
                "width": max_x - min_x + 1,
                "height": max_y - min_y + 1,
            }
        )

    if not boxes:
        raise ValueError(f"No recognizable rectangles found in {image_path.name}")

    return boxes


def compute_bounds(boxes: List[Dict[str, int]]) -> Dict[str, int]:
    """Return minimal rectangle covering all boxes."""
    min_x = min(box["x"] for box in boxes)
    min_y = min(box["y"] for box in boxes)
    max_x = max(box["x"] + box["width"] for box in boxes)
    max_y = max(box["y"] + box["height"] for box in boxes)

    min_x = max(min_x - OUTLINE_WIDTH, 0)
    min_y = max(min_y - OUTLINE_WIDTH, 0)
    max_x = min(max_x + OUTLINE_WIDTH, IMAGE_WIDTH)
    max_y = min(max_y + OUTLINE_WIDTH, IMAGE_HEIGHT)

    return {"left": min_x, "top": min_y, "right": max_x, "bottom": max_y}


def try_pack_in_bin(
    boxes: List[Dict[str, int]], width: int, height: int
) -> tuple[list[Dict[str, int]], int] | None:
    """Attempt to pack boxes into a specific bin. Return placements and used area."""
    packer = newPacker(rotation=True)

    for idx, box in enumerate(boxes):
        packer.add_rect(box["width"], box["height"], rid=idx)

    packer.add_bin(width, height)
    packer.pack()

    rects = packer.rect_list()
    if len(rects) < len(boxes):
        return None

    placements: List[Dict[str, int]] = []
    for _, x, y, w, h, rid in rects:
        source = boxes[rid]
        placements.append(
            {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "color_name": source["color_name"],
                "color": source["color"],
            }
        )

    bounds = compute_bounds(placements)
    used_area = (bounds["right"] - bounds["left"]) * (
        bounds["bottom"] - bounds["top"]
    )
    return placements, used_area


def generate_candidate_bins(boxes: List[Dict[str, int]]) -> List[tuple[int, int]]:
    """Generate bin sizes to test, ordered by theoretical area."""
    total_area = sum(box["width"] * box["height"] for box in boxes)
    max_width = max(box["width"] for box in boxes)
    max_height = max(box["height"] for box in boxes)
    base = int(math.ceil(math.sqrt(total_area)))

    width_candidates = {
        max_width,
        base,
        IMAGE_WIDTH,
    }
    height_candidates = {
        max_height,
        base,
        IMAGE_HEIGHT,
    }

    for step in (25, 50, 100):
        width_candidates.update(
            range(max_width, IMAGE_WIDTH + 1, step)
        )
        height_candidates.update(
            range(max_height, IMAGE_HEIGHT + 1, step)
        )

    widths = sorted(w for w in width_candidates if w <= IMAGE_WIDTH)
    heights = sorted(h for h in height_candidates if h <= IMAGE_HEIGHT)

    bins = {(w, h) for w in widths for h in heights if w >= max_width and h >= max_height}
    return sorted(bins, key=lambda wh: wh[0] * wh[1])


def pack_boxes(boxes: List[Dict[str, int]]) -> List[Dict[str, int]]:
    """Use rectpack repeatedly to approximate the minimal bounding area."""
    best_result: tuple[list[Dict[str, int]], int] | None = None
    min_possible_area = sum(box["width"] * box["height"] for box in boxes)

    for width, height in generate_candidate_bins(boxes):
        attempt = try_pack_in_bin(boxes, width, height)
        if attempt is None:
            continue

        placements, used_area = attempt
        if best_result is None or used_area < best_result[1]:
            best_result = (placements, used_area)
            if used_area <= min_possible_area:
                break

    if best_result is None:
        fallback = try_pack_in_bin(boxes, IMAGE_WIDTH, IMAGE_HEIGHT)
        if fallback is None:
            raise RuntimeError("Rectpack could not place every rectangle in the bin.")
        best_result = fallback

    placements = best_result[0]
    placements.sort(key=lambda box: COLOR_ORDER.index(box["color_name"]))
    return placements


def draw_boxes(boxes: List[Dict[str, int]], output_path: Path) -> None:
    """Render rectangles to an image file cropped to their bounds."""
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color="white")
    draw = ImageDraw.Draw(img)

    for box in boxes:
        draw.rectangle(
            [
                box["x"],
                box["y"],
                box["x"] + box["width"] - 1,
                box["y"] + box["height"] - 1,
            ],
            fill=box["color"],
            outline="black",
            width=OUTLINE_WIDTH,
        )

    bounds = compute_bounds(boxes)
    cropped = img.crop(
        (bounds["left"], bounds["top"], bounds["right"], bounds["bottom"])
    )
    cropped.save(output_path, "PNG")


def process_images(source_dir: Path, output_dir: Path, limit: int | None = None) -> None:
    image_paths = sorted(p for p in source_dir.glob("*.png") if p.is_file())
    if not image_paths:
        raise SystemExit(f"No .png files found in {source_dir}")

    if limit is not None:
        image_paths = image_paths[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, image_path in enumerate(image_paths, start=1):
        boxes = extract_boxes(image_path)
        placement = pack_boxes(boxes)
        draw_boxes(placement, output_dir / image_path.name)

        print(f"[{idx}/{len(image_paths)}] Packed {image_path.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate rectpack-based packing solutions for existing images."
    )
    parser.add_argument(
        "--source",
        "-s",
        default="images",
        help="Folder containing the original overlapping images (default: images)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="solutions",
        help="Destination folder for packed solutions (default: solutions)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        help="Optional limit on the number of images to process.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).parent
    source_dir = (script_dir / args.source).resolve()
    output_dir = (script_dir / args.output).resolve()

    print(f"Reading images from: {source_dir}")
    print(f"Writing packed solutions to: {output_dir}")

    process_images(source_dir, output_dir, args.limit)

    print("\n✓ Finished generating rectpack solutions.")


if __name__ == "__main__":
    main()

