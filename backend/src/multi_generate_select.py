import os
import sys
import json
import time
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.flux_generate import submit_generation
from src.poll_results import poll_until_ready
from src.validation import analyze_rectangles_and_empty_space
from src.send_to_model import _load_prompt_from_yaml, _load_image_from_yaml, _save_image
from src.preprocess import subjects_from_image

async def generate_single_candidate(
    index: int,
    prompt: str,
    aspect_ratio: str,
    input_image_path: Optional[Path],
    api_key: Optional[str],
    sleep_seconds: float,
    timeout_seconds: float,
    output_dir: Path,
    loop,
) -> Dict[str, Any]:
    """Generate and validate a single candidate image."""
    print(f"\n=== Generating candidate {index} ===")
    try:
        # Submit generation in thread pool to avoid blocking
        request_id, polling_url = await loop.run_in_executor(
            None,
            submit_generation,
            prompt,
            aspect_ratio,
            str(input_image_path) if input_image_path else None,
            api_key,
        )
        print(f"Candidate {index} - Request ID: {request_id}")

        def progress_cb(status: str, _data):
            print(f"Candidate {index} - Status: {status}")

        # Poll for results in thread pool to avoid blocking
        result = await loop.run_in_executor(
            None,
            poll_until_ready,
            polling_url,
            request_id,
            api_key,
            sleep_seconds,
            timeout_seconds,
            progress_cb,
        )
        
        sample = result.get("result", {}).get("sample")
        if not sample:
            print(f"Candidate {index} - No sample returned")
            return {
                "index": index,
                "path": None,
                "error": "No sample in API response"
            }
        
        # Save image in thread pool
        saved_path = await loop.run_in_executor(
            None,
            _save_image,
            sample,
            output_dir,
            f"flux_candidate_{index}",
        )
        print(f"Candidate {index} saved to: {saved_path}")
        
        # Run validation in thread pool
        try:
            summary = await loop.run_in_executor(
                None,
                analyze_rectangles_and_empty_space,
                str(saved_path),
            )
            rectangles = summary.get("rectangles", [])
            rect_areas = [r.get("area") for r in rectangles if isinstance(r, dict) and r.get("area") is not None]
            return {
                "index": index,
                "path": str(saved_path),
                "empty_percentage": summary.get("empty_percentage"),
                "rectangle_count": summary.get("rectangle_count"),
                "occupied_pixels": summary.get("occupied_pixels"),
                "total_pixels": summary.get("total_pixels"),
                "rect_areas": rect_areas,
            }
        except Exception as e:
            print(f"Validation failed for candidate {index}: {e}")
            return {
                "index": index,
                "path": str(saved_path),
                "error": str(e),
            }
    except Exception as e:
        print(f"Generation failed for candidate {index}: {e}")
        return {
            "index": index,
            "path": None,
            "error": str(e)
        }


async def generate_and_validate_parallel(
    prompt: str,
    aspect_ratio: str,
    input_image_path: Optional[Path],
    api_key: Optional[str],
    sleep_seconds: float,
    timeout_seconds: float,
    output_dir: Path,
    count: int,
) -> List[Dict[str, Any]]:
    """Generate multiple candidate images in parallel, validate each, and return metrics list."""
    print(f"Submitting {count} generation requests in parallel...")
    
    loop = asyncio.get_event_loop()
    
    # Create tasks for all candidates
    tasks = [
        generate_single_candidate(
            index=i,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            input_image_path=input_image_path,
            api_key=api_key,
            sleep_seconds=sleep_seconds,
            timeout_seconds=timeout_seconds,
            output_dir=output_dir,
            loop=loop,
        )
        for i in range(1, count + 1)
    ]
    
    # Run all tasks concurrently
    candidates = await asyncio.gather(*tasks)
    
    return list(candidates)


async def generate_and_validate_async(
    prompt: str,
    aspect_ratio: str,
    input_image_path: Optional[Path],
    api_key: Optional[str],
    sleep_seconds: float,
    timeout_seconds: float,
    output_dir: Path,
    count: int,
) -> List[Dict[str, Any]]:
    """Async interface for FastAPI usage to avoid nested event loops."""
    return await generate_and_validate_parallel(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        input_image_path=input_image_path,
        api_key=api_key,
        sleep_seconds=sleep_seconds,
        timeout_seconds=timeout_seconds,
        output_dir=output_dir,
        count=count,
    )


def generate_and_validate(
    prompt: str,
    aspect_ratio: str,
    input_image_path: Optional[Path],
    api_key: Optional[str],
    sleep_seconds: float,
    timeout_seconds: float,
    output_dir: Path,
    count: int,
) -> List[Dict[str, Any]]:
    """Sync helper for CLI scripts."""
    return asyncio.run(
        generate_and_validate_parallel(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            input_image_path=input_image_path,
            api_key=api_key,
            sleep_seconds=sleep_seconds,
            timeout_seconds=timeout_seconds,
            output_dir=output_dir,
            count=count,
        )
    )


def _size_match_score(orig_areas: List[float], cand_areas: List[float]) -> float:
    """Compute a size-match score: lower is better (mean relative difference).

    - Sort both lists and compare up to min length.
    - If lengths differ, penalize by adding 1.0 per missing/excess element.
    """
    if not orig_areas or not cand_areas:
        return float("inf")
    a = sorted([float(x) for x in orig_areas])
    b = sorted([float(x) for x in cand_areas])
    n = min(len(a), len(b))
    if n == 0:
        return float("inf")
    diffs = []
    for i in range(n):
        oa, ca = a[i], b[i]
        if oa <= 0:
            diffs.append(1.0)
        else:
            diffs.append(abs(ca - oa) / oa)
    penalty = abs(len(a) - len(b)) * 1.0
    return (sum(diffs) / n) + penalty


def select_best(
    candidates: List[Dict[str, Any]],
    original_rect_count: Optional[int],
    original_rect_areas: Optional[List[float]],
) -> Optional[Dict[str, Any]]:
    """Select the best candidate prioritizing:
    1) Matching rectangle count to original
    2) Better size match to original block areas
    3) Lower empty percentage
    """
    valid = [c for c in candidates if c.get("empty_percentage") is not None]
    if not valid:
        return None

    def sort_key(c: Dict[str, Any]) -> Tuple[int, float, float]:
        count_mismatch = 0
        if original_rect_count is not None:
            count_mismatch = 0 if c.get("rectangle_count") == original_rect_count else 1
        size_score = float("inf")
        if original_rect_areas:
            size_score = _size_match_score(original_rect_areas, c.get("rect_areas", []))
        empty = float(c.get("empty_percentage", float("inf")))
        return (count_mismatch, size_score, empty)

    best = min(valid, key=sort_key)
    return best


def main():
    parser = argparse.ArgumentParser(description="Generate multiple images, validate, and select best.")
    parser.add_argument("--num", type=int, default=5, help="Number of candidates to generate")
    parser.add_argument("--aspect", type=str, default="1:1", help="Aspect ratio for generation")
    parser.add_argument("--prompt", type=str, default=None, help="Override prompt text")
    parser.add_argument("--input", type=str, default=None, help="Path to input image for editing")
    parser.add_argument("--sleep", type=float, default=0.75, help="Polling sleep seconds")
    parser.add_argument("--timeout", type=float, default=300, help="Polling timeout seconds")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parents[1]
    config_prompt_path = workspace_root / "config" / "prompt.yaml"

    prompt = args.prompt or _load_prompt_from_yaml(config_prompt_path)
    input_image_path: Optional[Path] = None
    if args.input:
        ipath = Path(args.input)
        if ipath.exists():
            input_image_path = ipath
    else:
        raise ValueError("Input image path must be provided and exist.")

    if input_image_path:
        print(f"Using input image: {input_image_path}")
    else:
        raise ValueError("Input image path must be provided and exist.")
    
    subjects = subjects_from_image(str(input_image_path))  # Just to ensure preprocessing works
    prompt['subjects'] = subjects

    api_key = os.getenv("BFL_API_KEY")
    output_dir = workspace_root / args.output
    output_dir.mkdir(exist_ok=True)

    original_rect_count: Optional[int] = None
    original_rect_areas: Optional[List[float]] = None
    if input_image_path and input_image_path.exists():
        try:
            print("Analyzing original image for baseline shape count...")
            original_summary = analyze_rectangles_and_empty_space(str(input_image_path))
            original_rect_count = original_summary.get("rectangle_count")
            orig_rectangles = original_summary.get("rectangles", [])
            original_rect_areas = [r.get("area") for r in orig_rectangles if isinstance(r, dict) and r.get("area") is not None]
            print(f"Original rectangle count: {original_rect_count}")
        except Exception as e:
            print(f"Failed to analyze original image: {e}")

    candidates = generate_and_validate(
        prompt=prompt,
        aspect_ratio=args.aspect,
        input_image_path=input_image_path,
        api_key=api_key,
        sleep_seconds=args.sleep,
        timeout_seconds=args.timeout,
        output_dir=output_dir,
        count=args.num,
    )

    best = select_best(candidates, original_rect_count, original_rect_areas)
    summary_path = output_dir / "multi_generation_summary.json"
    payload = {
        "prompt": prompt,
        "input_image": str(input_image_path) if input_image_path else None,
        "original_rectangle_count": original_rect_count,
        "candidates": candidates,
        "selected": best,
        "selection_reason": (
            "Prioritized rectangle count match, then closest block sizes, then lowest empty percentage"
        ),
    }
    summary_path.write_text(json.dumps(payload, indent=2))
    if best:
        print(f"\nBest candidate: {best['path']} (empty %={best.get('empty_percentage')}, rectangles={best.get('rectangle_count')})")
    else:
        print("\nNo valid candidate selected.")
    print(f"Full summary written to {summary_path}")

    return 0 if best else 1


if __name__ == "__main__":
    sys.exit(main())
