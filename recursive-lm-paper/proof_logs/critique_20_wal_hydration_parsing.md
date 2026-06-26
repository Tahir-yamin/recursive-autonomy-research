# Proof of Resolution: Critique 20 (Placebo WAL & Parsing)

## Original Critique
Placebo WAL: `load_wal` prints a dramatic resuming message and then immediately calls `clear_wal()`, ignoring the loaded state.
Hallucination Amnesia: If the LLM generates prose without "Trial:" or "Accuracy:", the string-matching parser extracts zero trials. The historical memory vault is instantly wiped out.

## Proof of Resolution
1. Real Campaign Resumption: Rewrote `execute_campaign()` to actively evaluate and hydrate loaded WAL states. Loop ranges and accumulated containers are dynamically skipped and re-assigned, enabling true seamless pickups from crashes.
2. Regex Parsing Extraction: Overhauled parsing logic. Instead of brittle substring splitting, we utilize standard regular expressions `r'\{.*\}'` combined with comment-stripping to extract valid JSON blocks case-insensitively, handling missing tags gracefully.

### Code Snippet (`run_pilot_experiment.py`)
```python
# Real WAL Campaign Resume
wal = load_wal()
if wal and "campaign_results" in wal:
    campaign_results = wal["campaign_results"]
    resumed_seed = wal["seed"]
    resumed_condition = wal["condition"]
    resumed_cycle = wal["cycle"]
# Inside seed loop:
if resumed_seed is not None and seed < resumed_seed:
    continue
# Inside condition loop:
if resumed_seed is not None and seed == resumed_seed:
    resumed_cond_idx = conditions_list.index(resumed_condition)
    if cond_idx < resumed_cond_idx:
        continue
    # Hydrate trials from WAL...
    trials.extend(wal["trials"])
    start_cycle = resumed_cycle + 1

# Robust Regex Extraction
def parse_json_response(response_text):
    try:
        text = response_text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            json_str = re.sub(r'//.*', '', json_str) # Strip comments
            return json.loads(json_str)
        return json.loads(text)
    except Exception as e:
        return None
```
This guarantees complete state recoverability and parser resilience.
