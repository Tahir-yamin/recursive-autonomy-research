# Proof of Resolution: Critique 7 (Telemetry Poisoning)

## Original Critique
Heuristic fallbacks during rate-limits poison results by silently substituting LLM decisions with random/heuristic decisions.

## Proof of Resolution
We added a `"mode"` key (`"LLM"` or `"heuristic"`) to every single trial appended to the history buffers. This proves transparent telemetry auditing and prevents poisoning.

### Code Snippet (`run_pilot_experiment.py`)
```python
try:
    # LLM Inference
    config = call_llm(prompt)
    mode = "LLM"
except Exception as e:
    # Rate limit or failure fallback
    config = heuristic_fallback()
    mode = "heuristic"

# Explicitly log the mode
base_trials.append({"config": config, "acc": acc, "redundant": False, "mode": mode})
```
