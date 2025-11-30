import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.validation import analyze_rectangles_and_empty_space


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
	r, g, b = rgb
	return f"#{r:02X}{g:02X}{b:02X}"


def size_label(area: int, total_pixels: int) -> str:
	"""Map rectangle area to size bucket.

	Thresholds are heuristic; adjust as needed:
	- large: > 12% of image
	- medium: > 4% and <= 12%
	- small: <= 4%
	"""
	if total_pixels <= 0:
		return "small"
	pct = area / total_pixels * 100
	if pct > 12:
		return "large"
	if pct > 4:
		return "medium"
	return "small"


def subjects_from_image(image_path: str) -> List[Dict[str, Any]]:
	"""Extract subjects list from an image using rectangle analysis.

	Each subject dict: {"type": "box", "color": "#RRGGBB", "size": "large|medium|small", "area": int}
	"""
	summary = analyze_rectangles_and_empty_space(image_path)
	rects = summary.get("rectangles", [])
	total_pixels = summary.get("total_pixels", 1)
	subjects: List[Dict[str, Any]] = []
	for r in rects:
		color_rgb = r.get("color_rgb")
		area = r.get("area")
		if color_rgb is None or area is None:
			continue
		subjects.append({
			"type": "box",
			"color": rgb_to_hex(color_rgb),
			"size": size_label(area, total_pixels),
			"area": area,
		})
	return subjects