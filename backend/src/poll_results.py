import os
import time
import requests
from typing import Callable, Optional, Dict, Any


def poll_until_ready(
    polling_url: str,
    request_id: str,
    api_key: Optional[str] = None,
    sleep_seconds: float = 0.5,
    timeout_seconds: Optional[float] = 300.0,
    on_progress: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Poll the API until the result is ready or fails.

    Returns the JSON response dict when status == "Ready" or raises an exception on failure/timeout.
    `on_progress(status, data)` is called on each poll iteration if provided.
    """

    if api_key is None:
        api_key = os.getenv("BFL_API_KEY", "9f8ee884-d0e5-41e4-948b-d1e62f837c36")

    start_time = time.time()
    while True:
        if timeout_seconds is not None and (time.time() - start_time) > timeout_seconds:
            raise TimeoutError("Polling timed out before result was ready.")

        time.sleep(sleep_seconds)
        response = requests.get(
            polling_url,
            headers={
                "accept": "application/json",
                "x-key": api_key,
            },
            params={
                "id": request_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        status = data.get("status", "Unknown")

        if on_progress:
            on_progress(status, data)

        if status == "Ready":
            return data
        if status in {"Error", "Failed"}:
            raise RuntimeError(f"Generation failed: {data}")


if __name__ == "__main__":
    # Backwards compatible CLI behavior: read from files and print progress
    from pathlib import Path
    poll_results_dir = Path("output/poll_results")
    polling_url = (poll_results_dir / "polling_url.txt").read_text().strip()
    request_id = (poll_results_dir / "request_id.txt").read_text().strip()

    def _print_progress(status: str, _data: Dict[str, Any]):
        print(f"Status: {status}")

    try:
        result = poll_until_ready(polling_url, request_id, on_progress=_print_progress)
        print(f"Result: {result['result']['sample']}")
    except Exception as e:
        print(f"Generation failed: {e}")