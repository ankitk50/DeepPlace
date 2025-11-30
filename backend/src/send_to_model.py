import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import yaml
from src.flux_generate import submit_generation
from src.poll_results import poll_until_ready


def _load_prompt_from_yaml(yaml_path: Path) -> Optional[str]:

	if not yaml_path.exists():
		return None
	data = yaml.safe_load(yaml_path.read_text())
	return data.get("prompt") if isinstance(data, dict) else None

def _load_image_from_yaml(yaml_path: Path) -> Optional[str]:

    if not yaml_path.exists():
        return None
    data = yaml.safe_load(yaml_path.read_text())
    return data.get("image") if isinstance(data, dict) else None

def _save_image(sample: str, output_dir: Path, filename_prefix: str = "flux_result") -> Path:
	"""Save the returned sample (URL or base64 image) to output_dir and return the path."""
	output_dir.mkdir(exist_ok=True)
	ts = time.strftime("%Y%m%d_%H%M%S")
	out_path = output_dir / f"{filename_prefix}_{ts}.png"

	if sample.startswith("http://") or sample.startswith("https://"):
		resp = requests.get(sample)
		resp.raise_for_status()
		out_path.write_bytes(resp.content)
		return out_path

	# Assume base64-encoded image data
	import base64
	try:
		out_path.write_bytes(base64.b64decode(sample))
		return out_path
	except Exception:
		# Fallback: write raw string for debug
		out_path = output_dir / f"{filename_prefix}_{ts}.txt"
		out_path.write_text(sample)
		return out_path


def main():
	workspace_root = Path(__file__).resolve().parents[1]
	config_prompt_path = workspace_root / "config" / "prompt.yaml"
	data_image_default = workspace_root / "data" / f"{_load_image_from_yaml(config_prompt_path)}"
	output_dir = workspace_root / "output"

	prompt = _load_prompt_from_yaml(config_prompt_path) or (
		"Edit the input image to reduce occupied area while preserving recognizability and topology."
	)

	input_image_path = data_image_default if data_image_default.exists() else None
	api_key = os.getenv("BFL_API_KEY")
	print("input_image_path:", input_image_path)
	print("Prompt:", prompt)
	print("Submitting generation request…")
	request_id, polling_url = submit_generation(
		prompt=prompt,
		input_image_path=input_image_path,
		api_key=api_key,
	)
	print(f"Request ID: {request_id}")
	print("Polling for results (progress shown below)…")

	def progress_cb(status: str, _data):
		print(f"Status: {status}")

	result = poll_until_ready(
		polling_url=polling_url,
		request_id=request_id,
		api_key=api_key,
		sleep_seconds=0.75,
		timeout_seconds=300,
		on_progress=progress_cb,
	)

	sample = result.get("result", {}).get("sample")
	if not sample:
		print("No sample returned in result; full payload written to output for debugging.")
		debug_path = output_dir / "flux_result_payload.json"
		debug_path.write_text(str(result))
		print(f"Saved payload: {debug_path}")
		return

	saved_path = _save_image(sample, output_dir)
	print(f"Image saved to: {saved_path}")


if __name__ == "__main__":
	sys.exit(main())
