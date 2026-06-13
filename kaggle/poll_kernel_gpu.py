"""Poll the Kaggle kernel via kernels_logs (no bulk output download) until it
finishes, then report success/failure. Exits on completion -> one notification."""
import os, time, json, sys

from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi(); api.authenticate()
KERNEL = "tahiryamin2050/rar-taskb-fullgpu"

MAX_HOURS = 10
deadline = time.time() + MAX_HOURS * 3600
poll = 0
while time.time() < deadline:
    poll += 1
    try:
        raw = api.kernels_logs(KERNEL)
        ev = json.loads(raw)
        text = "".join(e.get("data", "") for e in ev)
    except Exception as e:
        print(f"[poll {poll}] log err: {str(e)[:80]} — {time.strftime('%H:%M:%S')}", flush=True)
        time.sleep(600); continue

    seeds_done = text.count("complete and checkpointed")
    props = text.count("Proposed:")
    if "CAMPAIGN COMPLETE" in text:
        print(f"RESULT: SUCCESS — campaign complete ({seeds_done} seeds, {props} proposals).", flush=True)
        sys.exit(0)
    if "PapermillExecutionError" in text or "raise error" in text:
        print("RESULT: FAILED — kernel errored. Tail:\n" + text[-1500:], flush=True)
        sys.exit(2)
    print(f"[poll {poll}] running — {seeds_done}/10 seeds, {props} proposals — {time.strftime('%H:%M:%S')}", flush=True)
    time.sleep(600)
print("RESULT: TIMEOUT after %d hours (data recoverable from log)." % MAX_HOURS, flush=True)
sys.exit(3)
