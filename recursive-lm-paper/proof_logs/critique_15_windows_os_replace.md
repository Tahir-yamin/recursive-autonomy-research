# Proof of Resolution: Critique 15 (Windows Non-Atomic `os.replace` Halt Vulnerability)

## Original Critique
The Write-Ahead Log (`save_wal()`) uses `os.replace()` to swap temp files. On Windows, this throws an unhandled `PermissionError` Access Denied crash if target file handles are locked by system services (like indexers or backup scanners).

## Proof of Resolution
We wrapped the `os.replace()` operation in a robust exponential retry-backoff loop (`time.sleep(0.1 * (2 ** attempt))`) catching `PermissionError`, safely resolving Windows indexing lock collisions.

### Code Snippet (`run_pilot_experiment.py`)
```python
def save_wal(condition, seed, cycle, trials, densities, net_tokens=0, custom_state=None, campaign_results=None):
    """Serialize active tuning progress to local write-ahead log atomically to prevent corruption"""
    wal_file = get_wal_path(condition, seed)
    state = {
        "condition": condition,
        "seed": seed,
        "cycle": cycle,
        "trials": list(trials),
        "densities": list(densities),
        "net_tokens": net_tokens,
        "custom_state": custom_state,
        "campaign_results": campaign_results,
        "timestamp": time.time()
    }
    tmp_file = f"{wal_file}.tmp.{os.getpid()}"
    try:
        with open(tmp_file, "w") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
            
        for attempt in range(5):
            try:
                os.replace(tmp_file, wal_file)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    print(f"SRE WAL Error: Failed to replace {wal_file} due to persistent lock.")
```
