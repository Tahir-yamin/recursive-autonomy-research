"""Run ONE seed's full campaign (all 3 conditions) in isolation.

Why this exists: long multi-seed runs in Colab die on runtime disconnects/timeouts.
Running each seed as its own process means a crash on seed N never wipes out the
seeds that already finished — each writes its own pilot_seed_<seed>.json to disk
(and you can commit each to GitHub as it lands).

Usage:
    # one seed
    python run_single_seed.py 101

    # several seeds back to back (still isolated outputs; stops if one raises)
    python run_single_seed.py 101 107 113 127

In a Colab cell:
    !OPENROUTER_API_KEY=$MY_KEY python run_single_seed.py 107

The API-key guard in run_pilot_experiment / run_deep_learning_harness will RAISE
if no key is set (instead of silently faking), so a dropped env var fails loudly.
"""
import os
import sys
import asyncio


def main(seeds):
    import run_pilot_experiment as rpe

    for seed in seeds:
        seed = int(seed)
        print(f"\n############ ISOLATED RUN — SEED {seed} ############")
        # Each seed writes its own file; merge_seeds.py stitches them later.
        os.environ["RAR_OUTPUT_FILE"] = f"pilot_seed_{seed}.json"
        rpe.SEEDS = [seed]
        asyncio.run(rpe.execute_campaign())
        print(f"############ SEED {seed} DONE -> pilot_seed_{seed}.json ############")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_single_seed.py <seed> [<seed> ...]")
        sys.exit(1)
    main(sys.argv[1:])
