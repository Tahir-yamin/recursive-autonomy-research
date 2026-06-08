# Running the RAR N=10 campaign on Kaggle (free GPU, no API cap)

`RAR_N10_GPU_campaign.ipynb` runs the full campaign with a **local** orchestrator
LLM (Ollama + Nemotron-Nano-9B on the notebook GPU), so there is **no API rate
limit** and PyTorch training runs on a real **T4 GPU**.

## Steps
1. Go to <https://www.kaggle.com/code> → **New Notebook** → **File → Import Notebook**
   and upload `RAR_N10_GPU_campaign.ipynb` (or import this repo's URL).
2. In the right sidebar **Settings**:
   - **Accelerator → GPU T4 x2**
   - **Internet → On**  (required for installs + model pull)
3. **Recommended for an unattended run:** click **Save Version → Save & Run All
   (Commit)**. This runs headless (up to ~9–12 h) and persists outputs even if you
   close the tab. (Interactive "Run All" also works if you keep the tab open.)
4. When it finishes, open the version's **Output** tab and download
   **`pilot_results.json`** — send that file back here and it gets integrated into
   the paper (Table 1, Wilcoxon, abstract) automatically.

## Notes
- **Timing:** ≈ 2–4 h (the orchestrator is a reasoning model). To gauge timing
  first, edit cell 6 to uncomment the 2-seed line, run it, then run the full N=10.
- **Model fidelity:** the notebook pulls `nemotron-nano-9b-v2` (the paper's model)
  as a community GGUF. If that arch fails to load on the installed Ollama build, it
  falls back to `gemma2:9b` and prints which model was used — tell me which one so
  the paper's model name stays truthful.
- **Resuming:** each completed seed is checkpointed to `partial_results.json`; in an
  interactive session, re-running cell 6 resumes from the last completed seed.
- **Output verification:** the final cell prints per-condition test accuracy and the
  count of real-LLM vs heuristic proposals — confirm `heuristic=0` for a fully clean
  run.
