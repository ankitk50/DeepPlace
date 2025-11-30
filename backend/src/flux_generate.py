import os
import base64
import requests
from typing import Optional, Tuple, Dict, Any, Union
import yaml
from pathlib import Path

def _get_model_from_yaml(yaml_path: Path) -> Optional[str]:
    if not yaml_path.exists():
        return None
    data = yaml.safe_load(yaml_path.read_text())
    return data.get("model") if isinstance(data, dict) else None

def get_api_url(yaml_path: Path) -> str:
    model = _get_model_from_yaml(yaml_path)
    print("Using model:", model)
    if model:
        return f"https://api.bfl.ai/v1/{model}"
    else:
        return "https://api.bfl.ai/v1/flux-kontext-pro"

API_URL = get_api_url(Path("config/prompt.yaml"))


def submit_generation(
    prompt: Union[str, Dict[str, Any], Any],
    aspect_ratio: str = "1:1",
    input_image_path: Optional[str] = None,
    api_key: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """Submit a generation/edit request and return (request_id, polling_url).

    - If `input_image_path` is provided and exists, the image will be sent for image-to-image editing.
    - If `api_key` is None, attempts to read from environment var `BFL_API_KEY`.
    - `extra_payload` allows passing additional parameters supported by the API.
    """

    if api_key is None:
        api_key = os.getenv("BFL_API_KEY", "9f8ee884-d0e5-41e4-948b-d1e62f837c36")

    # Coerce prompt to a string if a structured object (dict/list) was provided via YAML
    prompt_str: str
    if isinstance(prompt, (dict, list)):
        try:
            import json
            # Prefer a compact description: if dict has scene + subjects, build human prompt
            if isinstance(prompt, dict) and "scene" in prompt and "subjects" in prompt:
                subjects = prompt.get("subjects") or []
                if isinstance(subjects, list):
                    subjects_txt = ", ".join([str(s) for s in subjects if s])
                else:
                    subjects_txt = str(subjects)
                scene_txt = str(prompt.get("scene"))
                prompt_str = f"{scene_txt}\nSubjects: {subjects_txt}" if subjects_txt else scene_txt
            else:
                prompt_str = json.dumps(prompt, ensure_ascii=False)
        except Exception:
            prompt_str = str(prompt)
    else:
        prompt_str = str(prompt)

    payload: Dict[str, Any] = {
        "prompt": prompt_str,
        "aspect_ratio": aspect_ratio,
    }

    if extra_payload:
        payload.update(extra_payload)

    # Add image input if provided (for image-to-image editing)
    if input_image_path and os.path.exists(input_image_path):
        with open(input_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
            payload["input_image"] = image_data

    response = requests.post(
        API_URL,
        headers={
            "accept": "application/json",
            "x-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
    )
    if response.status_code >= 400:
        # Provide more debugging detail before raising
        print("Generation request failed:")
        print("Status:", response.status_code)
        print("Response text:", response.text)
        print("Payload sent:", payload)
    response.raise_for_status()
    data = response.json()
    request_id = data["id"]
    polling_url = data["polling_url"]
    return request_id, polling_url


if __name__ == "__main__":
    # Fallback script behavior for manual runs
    default_prompt = (
        "Industrial Design Visualization Prompt: 2D Computing PCB Board Layout\n\n"
        "Spacing & Alignment: All lines and edges should be perfectly orthogonal or parallel to the board edges. "
        "You are given a starting image, you should keep all the starting components with the correct label and move "
        "them to make them fit closer together, reducing white space but without overlaps.\n\n"
        "Style Modifiers: 2D top-down view, clean lines.\n\n"
        "Constraint: No shadows, gradients, reflections, or any elements that suggest 3D depth. "
        "The focus is on the geometric layout."
    )

    req_id, poll_url = submit_generation(
        prompt=default_prompt,
        aspect_ratio="1:1",
        input_image_path=os.getenv("INPUT_IMAGE_PATH", "data/sample_image1_nonopt.png"),
        api_key=os.getenv("BFL_API_KEY"),
    )

    # Preserve original behavior: write poll info to files
    from pathlib import Path
    poll_results_dir = Path("output/poll_results")
    poll_results_dir.mkdir(exist_ok=True)
    (poll_results_dir / "polling_url.txt").write_text(poll_url)
    (poll_results_dir / "request_id.txt").write_text(req_id)
    print(f"Request ID: {req_id}\nPolling URL: {poll_url}")






