import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Local imports from existing pipeline
from src.multi_generate_select import generate_and_validate_async, select_best
from src.send_to_model import _load_prompt_from_yaml
from src.preprocess import subjects_from_image
from src.validation import analyze_rectangles_and_empty_space

app = FastAPI()

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = WORKSPACE_ROOT / "output"
CONFIG_PROMPT_PATH = WORKSPACE_ROOT / "config" / "prompt.yaml"
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/generated", StaticFiles(directory=OUTPUT_DIR), name="generated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://127.0.0.1:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate")
async def generate_endpoint(
    image: UploadFile = File(...),
    aspect: str = Form("1:1"),
    num: int = Form(5),
    sleep: float = Form(0.75),
    timeout: float = Form(300),
):
    """Accepts an image upload, runs multi-candidate generation, returns best image.

    Form fields:
    - aspect: aspect ratio string like "1:1"
    - num: number of candidates to generate
    - sleep: polling sleep seconds
    - timeout: polling timeout seconds
    """
    # Save uploaded image to a temp path inside output
    if image.content_type is None or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    tmp_name = f"upload_{uuid.uuid4().hex}.png"
    tmp_path = OUTPUT_DIR / tmp_name
    try:
        data = await image.read()
        tmp_path.write_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded image: {e}")

    # Load base prompt and augment with subjects from the image
    try:
        prompt = _load_prompt_from_yaml(CONFIG_PROMPT_PATH)
        subjects = subjects_from_image(str(tmp_path))
        prompt["subjects"] = subjects
    except Exception as e:
        # Clean up temp file on failure
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to prepare prompt: {e}")

    # Analyze original for baseline rectangle count and areas
    original_rect_count: Optional[int] = None
    original_rect_areas: Optional[list[float]] = None
    try:
        original_summary = analyze_rectangles_and_empty_space(str(tmp_path))
        original_rect_count = original_summary.get("rectangle_count")
        orig_rectangles = original_summary.get("rectangles", [])
        original_rect_areas = [
            r.get("area")
            for r in orig_rectangles
            if isinstance(r, dict) and r.get("area") is not None
        ]
    except Exception:
        # non-fatal; proceed without baseline
        original_rect_count = None
        original_rect_areas = None

    api_key = os.getenv("BFL_API_KEY")

    # Run generation + validation
    try:
        candidates = await generate_and_validate_async(
            prompt=prompt,
            aspect_ratio=aspect,
            input_image_path=tmp_path,
            api_key=api_key,
            sleep_seconds=sleep,
            timeout_seconds=timeout,
            output_dir=OUTPUT_DIR,
            count=num,
        )
        best = select_best(candidates, original_rect_count, original_rect_areas)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")
    finally:
        # Remove the uploaded temp image
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    if not best or not best.get("path"):
        return JSONResponse(status_code=200, content={
            "message": "No valid candidate selected",
            "candidates": candidates,
        })

    best_path = Path(best["path"]).resolve()
    if not best_path.exists():
        raise HTTPException(status_code=500, detail="Best candidate file missing.")

    # Return the image URL so frontend can fetch it
    print(best_path)
    relative_url = f"/generated/{best_path.name}"
    return JSONResponse(
        status_code=200,
        content={
            "image_url": relative_url,
            "filename": best_path.name,
        },
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
