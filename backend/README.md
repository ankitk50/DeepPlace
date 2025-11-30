# Road_to_start_hack

## Multi-generation & Validation Selection

Use `src/multi_generate_select.py` to generate multiple candidate images via the BFL API, run rectangle/empty-space validation on each, and automatically pick the best one.

### Selection Criteria
1. Analyze the original (input) image to determine its rectangle (shape) count.
2. Generate N candidates.
3. Validate each candidate (rectangle count, empty space percentage).
4. Prefer candidates whose rectangle count matches the original; among those choose the one with the lowest empty space percentage.
5. If none match, fall back to globally lowest empty space percentage.

### Usage
```bash
export BFL_API_KEY="<your_api_key>"
python src/multi_generate_select.py --num 6 --aspect 1:1 --input data/your_input.png
```

Optional arguments:
- `--prompt` Override prompt from `config/prompt.yaml`.
- `--sleep` Poll sleep seconds (default 0.75).
- `--timeout` Poll timeout seconds (default 300).
- `--output` Output directory (default `output`).

Results:
- Candidate images saved as `output/flux_candidate_<i>_TIMESTAMP.png`.
- Validation artifacts (mask, labeled rectangles, CSV) saved by `validation.py`.
- Summary JSON: `output/multi_generation_summary.json` containing all candidates and the selected one.

### Single Generation (Legacy)
`src/send_to_model.py` still performs a single generation and saves its output.
