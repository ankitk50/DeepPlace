#!/usr/bin/env python3
"""
Script to generate 100 PNG images with colored boxes.
Each image contains boxes in red, green, blue, orange, and yellow with different sizes.

For every random image, a second version is produced where the same
boxes are repositioned to remove any overlaps.
"""

import random
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw

# Colors: red, green, blue, orange, yellow
COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'orange': (255, 165, 0),
    'yellow': (255, 255, 0)
}

# Image dimensions
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
OUTLINE_WIDTH = 2  # keep in sync with draw operations


def create_random_boxes() -> List[Dict[str, int]]:
    """Create a list of random boxes (may overlap)."""
    boxes = []
    for color_name, color_value in COLORS.items():
        box_width = random.randint(50, 200)
        box_height = random.randint(50, 200)
        x = random.randint(0, IMAGE_WIDTH - box_width)
        y = random.randint(0, IMAGE_HEIGHT - box_height)
        boxes.append({
            'x': x,
            'y': y,
            'width': box_width,
            'height': box_height,
            'color': color_value,
            'color_name': color_name,
        })
    return boxes


def boxes_overlap(box_a: Dict[str, int], box_b: Dict[str, int]) -> bool:
    """Return True if two axis-aligned boxes overlap."""
    a_left, a_top = box_a['x'], box_a['y']
    a_right, a_bottom = a_left + box_a['width'], a_top + box_a['height']

    b_left, b_top = box_b['x'], box_b['y']
    b_right, b_bottom = b_left + box_b['width'], b_top + box_b['height']

    if a_right <= b_left or a_left >= b_right:
        return False
    if a_bottom <= b_top or a_top >= b_bottom:
        return False
    return True


def arrange_boxes_without_overlap(boxes: List[Dict[str, int]]) -> List[Dict[str, int]]:
    """Return a new list of boxes repositioned to avoid overlaps."""
    boxes_copy = [box.copy() for box in boxes]
    placed_boxes: List[Dict[str, int]] = []

    order = sorted(
        range(len(boxes_copy)),
        key=lambda idx: boxes_copy[idx]['width'] * boxes_copy[idx]['height'],
        reverse=True,
    )

    for idx in order:
        box = boxes_copy[idx]
        placed = False

        for _ in range(500):
            x = random.randint(0, IMAGE_WIDTH - box['width'])
            y = random.randint(0, IMAGE_HEIGHT - box['height'])
            box['x'], box['y'] = x, y

            if all(not boxes_overlap(box, other) for other in placed_boxes):
                placed = True
                break

        if not placed:
            # Fallback: deterministic grid search to guarantee placement
            step = 5
            for y in range(0, IMAGE_HEIGHT - box['height'] + 1, step):
                if placed:
                    break
                for x in range(0, IMAGE_WIDTH - box['width'] + 1, step):
                    box['x'], box['y'] = x, y
                    if all(not boxes_overlap(box, other) for other in placed_boxes):
                        placed = True
                        break

        if not placed:
            raise RuntimeError('Unable to place box without overlap')

        placed_boxes.append(box)

    color_order = list(COLORS.keys())
    ordered_boxes = sorted(
        boxes_copy,
        key=lambda box: color_order.index(box['color_name'])
    )
    return ordered_boxes


def compute_bounds(boxes: List[Dict[str, int]]) -> Dict[str, int]:
    """Return the smallest rectangle that contains all boxes."""
    min_x = min(box['x'] for box in boxes)
    min_y = min(box['y'] for box in boxes)
    max_x = max(box['x'] + box['width'] for box in boxes)
    max_y = max(box['y'] + box['height'] for box in boxes)
    # Expand by outline width to avoid clipping borders
    min_x = max(min_x - OUTLINE_WIDTH, 0)
    min_y = max(min_y - OUTLINE_WIDTH, 0)
    max_x = min(max_x + OUTLINE_WIDTH, IMAGE_WIDTH)
    max_y = min(max_y + OUTLINE_WIDTH, IMAGE_HEIGHT)
    return {
        'left': min_x,
        'top': min_y,
        'right': max_x,
        'bottom': max_y,
    }


def draw_boxes(boxes: List[Dict[str, int]], output_path: Path) -> None:
    """Draw boxes on an image, crop to their combined bounds, and save."""
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color='white')
    draw = ImageDraw.Draw(img)
    for box in boxes:
        draw.rectangle(
            [
                box['x'],
                box['y'],
                box['x'] + box['width'],
                box['y'] + box['height'],
            ],
            fill=box['color'],
            outline='black',
            width=OUTLINE_WIDTH,
        )

    bounds = compute_bounds(boxes)
    cropped = img.crop((bounds['left'], bounds['top'], bounds['right'], bounds['bottom']))
    cropped.save(output_path, 'PNG')


def generate_images_for_index(image_number: int, images_dir: Path, images_no_overlap_dir: Path) -> None:
    """Generate overlapping and non-overlapping versions for a given index."""
    filename = f"image_{image_number:03d}.png"

    boxes = create_random_boxes()
    draw_boxes(boxes, images_dir / filename)

    boxes_no_overlap = arrange_boxes_without_overlap(boxes)
    draw_boxes(boxes_no_overlap, images_no_overlap_dir / filename)


def main():
    """Generate 100 PNG images with colored boxes."""
    script_dir = Path(__file__).parent
    images_dir = script_dir / "images"
    images_dir.mkdir(exist_ok=True)

    images_without_overlap_dir = script_dir / "images_without_overlap"
    images_without_overlap_dir.mkdir(exist_ok=True)

    print(f"Generating 100 images in: {images_dir}")
    print(f"Generating 100 non-overlapping images in: {images_without_overlap_dir}")

    for i in range(1, 101):
        generate_images_for_index(i, images_dir, images_without_overlap_dir)
        if i % 10 == 0:
            print(f"Generated {i}/100 image pairs...")

    print("\n✓ Successfully generated 100 PNG files in both folders")
    print(f"  Overlapping images: {images_dir} (image_001.png .. image_100.png)")
    print(f"  Non-overlapping images: {images_without_overlap_dir} (image_001.png .. image_100.png)")


if __name__ == '__main__':
    main()

