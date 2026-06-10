import os
import json
import time
import asyncio
import aiohttp
import collections
import re
import logging
import numpy as np
import networkx as nx
from networkx.algorithms.community import louvain_communities
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from typing import Dict, Any, Optional

# Configure structured logger — replaces bare print() for error/warning paths
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("rar_orchestrator")

# Ensure outputs go strictly to the workspace directory containing the script
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- API Setup ----------------------------------------------------------------
API_KEY_DEFAULT = os.environ.get("OPENROUTER_API_KEY", "")

_SIM_MODE_WARNED = False
def _warn_simulation_mode(where: str) -> None:
    """Emit a prominent one-time warning whenever the synthetic simulation fallback
    activates, so keyless runs can never silently masquerade as physical experiments."""
    global _SIM_MODE_WARNED
    if not _SIM_MODE_WARNED:
        log.warning("=" * 64)
        log.warning("SIMULATION MODE ACTIVE (%s): no LLM API key detected.", where)
        log.warning("Outputs are SYNTHETIC arithmetic stubs, NOT real LLM/PyTorch results.")
        log.warning("Set OPENROUTER_API_KEY to run physical experiments.")
        log.warning("=" * 64)
        _SIM_MODE_WARNED = True

async def call_llm(prompt, session=None, system_prompt="You are a precise machine learning assistant."):
    """Async HTTP client utilizing a shared aiohttp ClientSession for serving-safe, non-blocking requests"""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY_DEFAULT
    # Generic OpenAI-compatible local endpoint (e.g. Ollama/vLLM on a notebook GPU).
    # When set, this is a *real* inference backend, so simulation must NOT engage.
    local_url = os.environ.get("LLM_BASE_URL")

    # SRE Fast Simulation Mode (only if NO real backend of any kind is configured)
    if not gemini_key and not deepseek_key and not openrouter_key and not local_url:
        _warn_simulation_mode("call_llm")
        if "recursively consolidating" in prompt or "You are recursively consolidating" in prompt:
            return "The optimal parameters occupy wider dimensions (filters_2=64) and depth num_conv_layers=3 with LeakyReLU and AdamW (lr=0.01). Failed configurations consistently use SGD and high dropout (0.5)."
        else:
            is_rar_late = "Lossless Summary" in prompt
            is_rar_early = "Recent Trial Logs" in prompt
            is_rag = "Vector RAG Match" in prompt
            
            # Count standard trials in the prompt
            num_trials = prompt.count("- Trial:")
            
            if is_rar_late:
                # Late cycles of RAR: propose the optimal 3-block model
                cfg = {"num_conv_layers": 3, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32}
            elif is_rar_early:
                # Early cycles of RAR
                rar_early_seq = [
                    {"num_conv_layers": 1, "filters_2": 16, "activation": "ReLU", "dropout_rate": 0.5, "optimizer": "SGD", "lr": 0.05, "batch_size": 64},
                    {"num_conv_layers": 2, "filters_2": 32, "activation": "ELU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.001, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32}
                ]
                cfg = rar_early_seq[min(num_trials, len(rar_early_seq) - 1)]
            elif is_rag:
                # Vector RAG: explores but gets stuck on local optima
                rag_seq = [
                    {"num_conv_layers": 1, "filters_2": 16, "activation": "ReLU", "dropout_rate": 0.5, "optimizer": "SGD", "lr": 0.05, "batch_size": 64},
                    {"num_conv_layers": 2, "filters_2": 32, "activation": "ELU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.001, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 1, "filters_2": 32, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "SGD", "lr": 0.01, "batch_size": 16},
                    {"num_conv_layers": 3, "filters_2": 16, "activation": "ELU", "dropout_rate": 0.0, "optimizer": "AdamW", "lr": 0.0001, "batch_size": 64},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.5, "optimizer": "SGD", "lr": 0.05, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 32, "activation": "ReLU", "dropout_rate": 0.0, "optimizer": "AdamW", "lr": 0.001, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 16, "activation": "ReLU", "dropout_rate": 0.2, "optimizer": "SGD", "lr": 0.001, "batch_size": 32},
                    {"num_conv_layers": 1, "filters_2": 32, "activation": "ELU", "dropout_rate": 0.0, "optimizer": "AdamW", "lr": 0.001, "batch_size": 64},
                    {"num_conv_layers": 2, "filters_2": 16, "activation": "LeakyReLU", "dropout_rate": 0.5, "optimizer": "SGD", "lr": 0.01, "batch_size": 16}
                ]
                cfg = rag_seq[min(num_trials, len(rag_seq) - 1)]
            else:
                # Stateless baseline: gets stuck in a redundant loop
                base_seq = [
                    {"num_conv_layers": 1, "filters_2": 16, "activation": "ReLU", "dropout_rate": 0.5, "optimizer": "SGD", "lr": 0.05, "batch_size": 64},
                    {"num_conv_layers": 2, "filters_2": 32, "activation": "ELU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.001, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32},
                    {"num_conv_layers": 2, "filters_2": 64, "activation": "LeakyReLU", "dropout_rate": 0.2, "optimizer": "AdamW", "lr": 0.01, "batch_size": 32}
                ]
                cfg = base_seq[min(num_trials, len(base_seq) - 1)]
            return json.dumps(cfg)

    is_gemini = False
    is_deepseek = False

    if gemini_key:
        is_gemini = True
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.2}
        }
    elif deepseek_key:
        is_deepseek = True
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {deepseek_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
    else:
        # OpenAI-compatible path: OpenRouter by default, or a local endpoint
        # (Ollama/vLLM) when LLM_BASE_URL is set. Same request schema for both.
        url = local_url or "https://openrouter.ai/api/v1/chat/completions"
        auth_key = openrouter_key or os.environ.get("LLM_API_KEY", "local")
        headers = {
            "Authorization": f"Bearer {auth_key}",
            "Content-Type": "application/json"
        }
        model_name = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-nano-9b-v2:free")
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            # Reasoning-capable free models (e.g. nemotron-nano) spend tokens on a
            # reasoning trace before emitting content; budget generously so the JSON
            # answer is not truncated (finish_reason=length with null content).
            "max_tokens": int(os.environ.get("OPENROUTER_MAX_TOKENS", "4000"))
        }
        
    actual_session = session or aiohttp.ClientSession()
    # Explicit socket-level timeouts so a server that accepts the connection but
    # never streams a body (common on free-tier queueing) cannot hang us forever.
    req_timeout = aiohttp.ClientTimeout(total=120, connect=30, sock_connect=30, sock_read=90)

    async def _do_request():
        async with actual_session.post(url, headers=headers, json=payload,
                                       timeout=req_timeout) as response:
            status = response.status
            if status == 200:
                return status, await response.json()
            return status, await response.text()

    try:
        for attempt in range(5):
            try:
                # Hard ceiling independent of aiohttp's internal timer (belt and
                # suspenders against any concurrency-related stall).
                status, body = await asyncio.wait_for(_do_request(), timeout=130)
                if status == 200:
                    res_data = body
                    if is_gemini:
                        return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Reasoning models may return content=None when the token budget
                    # is exhausted by the reasoning trace; treat as transient failure.
                    content = res_data["choices"][0]["message"].get("content")
                    if content:
                        return content.strip()
                    log.warning("LLM returned empty content (likely reasoning-token "
                                "exhaustion); retrying with backoff.")
                    await asyncio.sleep((1.0 * (2 ** attempt)) + np.random.uniform(0.1, 1.0))
                elif status == 429:
                    backoff = 2.0 * (2 ** attempt) + np.random.uniform(0.1, 1.0)
                    log.warning("Rate limited (429). Retrying after %.2fs backoff...", backoff)
                    await asyncio.sleep(backoff)
                else:
                    log.error("API Error %s: %s", status, str(body)[:200])
                    await asyncio.sleep((1.0 * (2 ** attempt)) + np.random.uniform(0.1, 1.0))
            except asyncio.TimeoutError:
                log.warning("LLM call timed out (attempt %d/5); backing off.", attempt + 1)
                await asyncio.sleep((1.0 * (2 ** attempt)) + np.random.uniform(0.1, 1.0))
            except Exception as e:
                log.error("Connection error: %s", e)
                await asyncio.sleep((1.0 * (2 ** attempt)) + np.random.uniform(0.1, 1.0))
    finally:
        if session is None:
            await actual_session.close()
    return None

def parse_json_response(response_text):
    """Extract hyperparameter JSON securely using a nesting-depth bracket matching parser"""
    try:
        text = response_text.strip()
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        depth = 0
        end_idx = -1
        for idx in range(start_idx, len(text)):
            char = text[idx]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end_idx = idx
                    break
        
        if end_idx != -1:
            json_str = text[start_idx:end_idx+1]
            json_str = re.sub(r'//.*', '', json_str)
            return json.loads(json_str)
    except Exception as e:
        print(f"Brace-matching JSON parsing failed: {e}")
    return None

def is_valid_config(config):
    """Harden parser by validating hyperparameter types and ranges to prevent runtime execution failures"""
    if not isinstance(config, dict):
        return False
    required_keys = ["num_conv_layers", "filters_2", "activation", "dropout_rate", "optimizer", "lr", "batch_size"]
    for key in required_keys:
        if key not in config:
            return False
    try:
        if int(config["num_conv_layers"]) not in SEARCH_SPACE["num_conv_layers"]: return False
        if int(config["filters_2"]) not in SEARCH_SPACE["filters_2"]: return False
        if str(config["activation"]) not in SEARCH_SPACE["activation"]: return False
        if float(config["dropout_rate"]) not in SEARCH_SPACE["dropout_rate"]: return False
        if str(config["optimizer"]) not in SEARCH_SPACE["optimizer"]: return False
        if float(config["lr"]) not in SEARCH_SPACE["lr"]: return False
        if int(config["batch_size"]) not in SEARCH_SPACE["batch_size"]: return False
    except (ValueError, TypeError):
        return False
    return True

# Pre-compiled instruction-override patterns for input-boundary sanitization.
# These guard the LLM *input* surface (free-text summaries re-injected into the
# recursive prompt), complementing is_valid_config which guards the *output*.
_INJECTION_PATTERNS = [
    re.compile(r'(?i)(ignore|forget|disregard|override)\b.{0,40}\b(instruction|above|prior|previous|system|prompt)'),
    re.compile(r'(?i)\b(system|developer)\s*prompt\b'),
    re.compile(r'(?i)\byou\s+are\s+now\b'),
    re.compile(r'(?i)\b(execute|run|call)\b.{0,20}\b(api|command|shell|code)\b'),
]

def sanitize_log_entry(entry: str, max_len: int = 600) -> str:
    """Strip instruction-override patterns from free text before it re-enters the
    LLM context. This closes the indirect prompt-injection vector where a crafted
    trial summary could hijack the recursive consolidation prompt.

    Args:
        entry: Raw free text (e.g. an LLM-generated knowledge-map summary).
        max_len: Hard cap on returned length to bound prompt growth.
    Returns:
        Sanitized, length-bounded string safe to inline into a prompt.
    """
    if not isinstance(entry, str):
        return ""
    sanitized = entry
    for pat in _INJECTION_PATTERNS:
        sanitized = pat.sub("[SANITIZED]", sanitized)
    return sanitized[:max_len]

def save_failed_payload(prompt, error_msg="Timeout or API Error"):
    """SRE Hardening: Persist the exact prompt that caused API timeouts or parsing failures for root-cause analysis"""
    import datetime
    log_path = os.path.join(OUTPUT_DIR, "failed_prompts.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"=== FAILED PAYLOAD at {datetime.datetime.now().isoformat()} ===\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"Prompt:\n{prompt}\n")
            f.write("=" * 80 + "\n\n")
    except Exception as e:
        print(f"Failed to log failed payload: {e}")

# --- Search Space and Constants (Ghost Parameters Purged) ---------------------
# CYCLES and SEEDS are env-overridable for smoke-testing (e.g. RAR_CYCLES=3
# RAR_SEEDS=42) without touching the statistically rigorous N=10 default campaign.
CYCLES = int(os.environ.get("RAR_CYCLES", "10"))
_DEFAULT_SEEDS = [42, 7, 13, 23, 88, 99, 101, 107, 113, 127]  # N=10 independent seeds
_seeds_env = os.environ.get("RAR_SEEDS", "")
SEEDS = [int(s) for s in _seeds_env.split(",") if s.strip()] if _seeds_env else _DEFAULT_SEEDS
MAX_TRIAL_MEMORY = 50  # Parent state-eviction sliding window to prevent linear heap fragmentation

# Expanded to the Phase-0-validated ranges: depth/width reach the high-accuracy region
# (~91% ceiling) so search quality is visible; lr capped at 1e-2 (5e-2 was unstable).
SEARCH_SPACE = {
    "num_conv_layers": [2, 3, 4, 5, 7],
    "filters_2": [32, 64, 128, 256, 512],
    "activation": ["ReLU", "ELU", "LeakyReLU"],
    "dropout_rate": [0.0, 0.05, 0.1, 0.2],
    "optimizer": ["AdamW", "SGD"],
    "lr": [0.0001, 0.001, 0.01],
    "batch_size": [32, 64, 128]
}

SEARCH_SPACE_PROMPT = """
Residual MLP Hyperparameter Search Space (10-class classification):
- num_conv_layers: [2, 3, 4, 5, 7] (number of residual MLP blocks; deeper fits the harder manifold)
- filters_2: [32, 64, 128, 256, 512] (hidden width; larger needed for high accuracy)
- activation: ['ReLU', 'ELU', 'LeakyReLU']
- dropout_rate: [0.0, 0.05, 0.1, 0.2]
- optimizer: ['AdamW', 'SGD']
- lr: [0.0001, 0.001, 0.01] (peak LR under a warmup+cosine schedule; 0.01 is typically best)
- batch_size: [32, 64, 128]

Training uses warmup + cosine annealing, 40 epochs, early stopping. Weight decay and
label smoothing are fixed. Propose a new, untried configuration that maximizes validation
accuracy. Good solutions reach ~85-91%; weak ones stay near 55-60%.
"""

# --- Context budget & verbose logging (saturation mechanism) ------------------
# The stateless baseline truncates its accumulated log to C_MAX characters, so at long
# horizons it genuinely forgets older trials (the context-rot mechanism the paper studies).
# Verbose per-trial entries make the log pressure the budget realistically.
C_MAX = int(os.environ.get("RAR_CMAX", "4000"))

def format_trial_verbose(t):
    """Verbose per-trial log entry (~300-400 chars) so accumulated history realistically
    pressures the context window, inducing genuine saturation in the stateless baseline."""
    c = t["config"]
    region = "strong region" if t["acc"] >= 0.75 else ("weak region" if t["acc"] < 0.60 else "mid region")
    return (f"- Trial: arch(blocks={c.get('num_conv_layers')}, width={c.get('filters_2')}, "
            f"act={c.get('activation')}, dropout={c.get('dropout_rate')}), "
            f"optim={c.get('optimizer')}, lr={c.get('lr')}, batch={c.get('batch_size')} "
            f"-> val_acc={t['acc']:.4f}{' [REDUNDANT]' if t.get('redundant') else ''}. "
            f"Note: evaluated on the 10-class manifold; result falls in the {region}.\n")

def truncate_to_budget(header, entries, budget):
    """Keep the most-recent entries that fit within `budget` chars (after header),
    mimicking a hard context-window truncation. Returns (text, n_kept, n_total)."""
    kept, used = [], len(header)
    for e in reversed(entries):
        if used + len(e) > budget:
            break
        kept.append(e); used += len(e)
    kept.reverse()
    text = header + "".join(kept)
    if len(kept) < len(entries):
        text += f"[... {len(entries) - len(kept)} older trials truncated (context window full) ...]\n"
    return text, len(kept), len(entries)

# --- SRE Write-Ahead Logging (WAL) State Machine (Isolative Filenames) ---------
def get_wal_path(condition, seed):
    """Isolate WAL storage by condition and seed to prevent multi-process data contamination"""
    return os.path.join(OUTPUT_DIR, f"wal_store_{condition}_{seed}.json")

def save_wal(condition, seed, cycle, trials, densities, net_tokens=0, custom_state=None, campaign_results=None):
    """Serialize active tuning progress to local write-ahead log atomically with SHA-256 integrity checksum verification"""
    import hashlib
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
    
    # Calculate checksum of base state
    state_str = json.dumps(state, sort_keys=True)
    state["checksum"] = hashlib.sha256(state_str.encode('utf-8')).hexdigest()
    
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
            except (PermissionError, OSError):
                if attempt < 4:
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    print(f"SRE WAL Error: Failed to replace {wal_file} due to persistent lock.")
    except Exception as e:
        print(f"Failed to write WAL atomically: {e}")
    finally:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except:
                pass

def load_wal(wal_file):
    """Load cached state from write-ahead log and verify SHA-256 integrity checksum"""
    import hashlib
    if os.path.exists(wal_file):
        try:
            with open(wal_file, "r") as f:
                state = json.load(f)
            checksum = state.pop("checksum", None)
            if not checksum:
                print("WAL file has no checksum. Discarding state.")
                return None
            state_str = json.dumps(state, sort_keys=True)
            computed = hashlib.sha256(state_str.encode('utf-8')).hexdigest()
            if computed != checksum:
                print("WAL integrity verification failed! Checksum mismatch.")
                return None
            return state
        except Exception as e:
            print(f"Failed to read WAL: {e}")
    return None

def clear_wal(wal_file):
    """Remove WAL file upon successful campaign completion"""
    if os.path.exists(wal_file):
        try:
            os.remove(wal_file)
        except Exception as e:
            print(f"Failed to clear WAL: {e}")


# --- Random Hyperparameter Fallback ------------------------------------------
def get_random_config():
    return {
        "num_conv_layers": int(np.random.choice(SEARCH_SPACE["num_conv_layers"])),
        "filters_2": int(np.random.choice(SEARCH_SPACE["filters_2"])),
        "activation": str(np.random.choice(SEARCH_SPACE["activation"])),
        "dropout_rate": float(np.random.choice(SEARCH_SPACE["dropout_rate"])),
        "optimizer": str(np.random.choice(SEARCH_SPACE["optimizer"])),
        "lr": float(np.random.choice(SEARCH_SPACE["lr"])),
        "batch_size": int(np.random.choice(SEARCH_SPACE["batch_size"]))
    }

# --- Standardized Vector representation for Similarity Retrieval (Vector RAG) ---
def config_to_vector(config):
    """
    Standardizes hyperparameters to a continuous-categorical vector space
    using Z-score normalization boundaries and One-Hot Encoding.
    Prevents ordinal geometry bias in similarity calculations.
    """
    layers_norm = (float(config.get("num_conv_layers", 2)) - 1.0) / 2.0
    filters_2_norm = (float(config.get("filters_2", 32)) - 16.0) / 48.0
    dropout_norm = float(config.get("dropout_rate", 0.2)) / 0.5
    
    lr_val = float(config.get("lr", 1e-3))
    lr_log = np.log10(lr_val)
    lr_norm = (lr_log - np.log10(0.0001)) / (np.log10(0.05) - np.log10(0.0001))
    
    batch_norm = (float(config.get("batch_size", 32)) - 16.0) / 48.0
    
    activation = config.get("activation", "ReLU")
    act_oh = [
        1.0 if activation == "ReLU" else 0.0,
        1.0 if activation == "ELU" else 0.0,
        1.0 if activation == "LeakyReLU" else 0.0
    ]
    
    optimizer = config.get("optimizer", "AdamW")
    opt_oh = [
        1.0 if optimizer == "AdamW" else 0.0,
        1.0 if optimizer == "SGD" else 0.0
    ]
    
    vec = [
        layers_norm,
        filters_2_norm,
        dropout_norm,
        lr_norm,
        batch_norm
    ] + act_oh + opt_oh
    
    return np.array(vec).reshape(1, -1)

# --- Compute-Matched Vector RAG Baseline Condition ---------------------------
def retrieve_vector_rag_context(trials, current_config_candidate, budget_limit=2000):
    """
    Vectorized similarity retrieval. Standardizes vector representation,
    computes cosine similarity batched in NumPy, and retrieves top-k results
    capped under the expanded budget limit (2000 chars) to ensure a fair comparison baseline.
    """
    if not trials:
        return "No prior trial records found."
        
    candidate_vec = config_to_vector(current_config_candidate)
    history_vectors = np.vstack([config_to_vector(t["config"]) for t in trials])
    
    similarities = cosine_similarity(candidate_vec, history_vectors)[0]
    similarities_and_trials = list(zip(similarities, trials))
    similarities_and_trials.sort(key=lambda x: x[0], reverse=True)
    
    retrieved_str = "### Retrieved Prior Trial Context (Vector RAG Match):\n"
    current_len = len(retrieved_str)
    
    for sim, t in similarities_and_trials:
        entry = f"- Trial: {t['config']}, Accuracy: {t['acc']:.4f} (Similarity: {sim:.3f})\n"
        if current_len + len(entry) <= budget_limit:
            retrieved_str += entry
            current_len += len(entry)
        else:
            break
            
    return retrieved_str

# --- Asynchronous GraphRAG Louvain Memory Consolidator -------------------------
def _cpu_louvain_partition(all_trials):
    """CPU-bound graph building, pairwise similarity, and Louvain clustering"""
    G = nx.Graph()
    for i, t in enumerate(all_trials):
        G.add_node(i, config=t["config"], acc=t["acc"])
        
    vectors = np.vstack([config_to_vector(t["config"]) for t in all_trials])
    sim_matrix = cosine_similarity(vectors)
    
    n = len(all_trials)
    # Sparse k-NN Graph Construction (k=3, gated at similarity > 0.3) to prevent dense collapse and control complexity
    k = min(3, n - 1)
    if k > 0:
        for i in range(n):
            sims = sim_matrix[i].copy()
            sims[i] = -1.0  # Exclude self-loop similarity
            nearest_neighbors = np.argsort(sims)[-k:]
            for idx in nearest_neighbors:
                if sims[idx] > 0.3:
                    G.add_edge(i, int(idx), weight=float(sims[idx]))
        
    try:
        if G.number_of_edges() > 0:
            communities = list(louvain_communities(G, weight='weight', seed=42))

            # Verify modularity maximization axiom (must be positive)
            mod_val = nx.community.modularity(G, communities, weight='weight')
            if mod_val <= 0.0:
                # Modularity gain is not positive; fallback to treating each node as a community to maintain search diversity
                communities = [{i} for i in range(n)]
        else:
            communities = [{i} for i in range(n)]
    except Exception:
        communities = [set(comp) for comp in nx.connected_components(G)]
        
    graph_summary = "### GraphRAG Hyperparameter Community Manifold Map:\n"
    for c_idx, community in enumerate(communities):
        c_trials = [all_trials[node_id] for node_id in community]
        best_t = max(c_trials, key=lambda x: x["acc"])
        worst_t = min(c_trials, key=lambda x: x["acc"])
        
        graph_summary += f"Community {c_idx + 1} (Size: {len(community)}):\n"
        graph_summary += f"  - Local Optima: {best_t['config']} -> Accuracy: {best_t['acc']:.4f}\n"
        graph_summary += f"  - Failed Boundary: {worst_t['config']} -> Accuracy: {worst_t['acc']:.4f}\n"
        
    global_best = max(all_trials, key=lambda x: x["acc"])
    global_worst = min(all_trials, key=lambda x: x["acc"])
    graph_summary += f"Global Search Extrema:\n"
    graph_summary += f"  - Peak Success: {global_best['config']} -> Accuracy: {global_best['acc']:.4f}\n"
    graph_summary += f"  - Nadir Failure: {global_worst['config']} -> Accuracy: {global_worst['acc']:.4f}\n"
    
    return graph_summary

class AsyncMemoryConsolidator:
    def __init__(self):
        import threading
        self.task = None
        self.result = ""
        self.is_running = False
        self.error_status = None
        self.success = False
        self.consolidated_count = 0
        self.cancel_event = threading.Event()

    def start_consolidation(self, compressed_history, raw_history_buffer, session):
        """Spawns non-blocking async task to consolidate memory (resolves thread leak & blocking I/O)"""
        self.is_running = True
        self.error_status = None
        self.success = False
        self.cancel_event.clear()
        self.consolidated_count = len(raw_history_buffer)
        self.task = asyncio.create_task(self._consolidate_worker(compressed_history, list(raw_history_buffer), session))

    async def _consolidate_worker(self, compressed_history, raw_history_buffer, session):
        print("SRE Background Worker: Starting asynchronous GraphRAG memory consolidation (Louvain)...")
        start_time = time.time()
        
        try:
            all_trials = list(raw_history_buffer)
            
            if len(all_trials) < 2:
                summary = compressed_history
                if all_trials:
                    summary += f"\n- Trial: {all_trials[-1]['config']}, Accuracy: {all_trials[-1]['acc']:.4f}"
                self.result = summary
                self.success = True
                return
                
            graph_summary = await asyncio.to_thread(_cpu_louvain_partition, all_trials)

            compression_prompt = f"""
You are recursively consolidating hyperparameter search memory.

Here is the summary of prior knowledge accumulated so far:
{compressed_history if compressed_history else "No prior history."}

Here are the new mathematically grouped hyperparameter search communities from the latest trials:
{graph_summary}

Provide an updated, highly condensed summary that merges the prior knowledge with the new insights.
Your summary MUST contain:
1. The exact values of the best-performing hyperparameters and the regions where they reside.
2. The exact values of parameters that consistently failed (negative boundaries) and should be avoided.
"""
            summary = await call_llm(
                compression_prompt,
                session=session,
                system_prompt="You are a data scientist. Provide extremely dense, direct insights. Limit your summary output to exactly 2 concise sentences (max 180 characters total) to capture the absolute best hyperparameter boundaries and failed regions. Do not use AI slop words."
            )
            
            if summary:
                self.result = summary
                self.success = True
            else:
                self.result = compressed_history
                self.success = False
            duration = time.time() - start_time
            print(f"SRE Background Worker: Finished async Louvain consolidation in {duration:.2f}s.")
        except asyncio.CancelledError:
            print("SRE Background Worker: Worker task cancelled.")
            self.success = False
            self.result = compressed_history
            raise
        except Exception as e:
            print(f"SRE Background Worker Crash: {e}")
            self.error_status = str(e)
            self.success = False
            self.result = compressed_history
        finally:
            self.is_running = False

    def get_result(self):
        return self.result

def perturb_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *config* with one randomly mutated hyperparameter.

    Randomly selects a parameter key from SEARCH_SPACE and replaces its
    current value with a uniformly sampled alternative from the allowed set.
    Type coercion is applied to keep all values in their expected Python types
    (int, float, str) so that downstream model constructors remain type-safe.

    Args:
        config: A valid hyperparameter configuration mapping.

    Returns:
        A new configuration dict with exactly one field mutated.
    """
    cfg = config.copy()
    param_to_change = np.random.choice(list(SEARCH_SPACE.keys()))
    cfg[param_to_change] = np.random.choice(SEARCH_SPACE[param_to_change])
    if param_to_change in ["num_conv_layers", "filters_2", "batch_size"]:
        cfg[param_to_change] = int(cfg[param_to_change])
    elif param_to_change == "dropout_rate" or param_to_change == "lr":
        cfg[param_to_change] = float(cfg[param_to_change])
    else:
        cfg[param_to_change] = str(cfg[param_to_change])
    return cfg

def perturb_config_guided(config, best_acc):
    cfg = config.copy()
    param = np.random.choice(["lr", "filters_2", "num_conv_layers", "dropout_rate"])
    if param == "lr":
        current_lr = cfg.get("lr", 0.001)
        lr_options = SEARCH_SPACE["lr"]
        try:
            idx = lr_options.index(current_lr)
            if best_acc < 0.7:
                cfg["lr"] = float(np.random.choice(lr_options))
            else:
                step = np.random.choice([-1, 1])
                new_idx = max(0, min(len(lr_options) - 1, idx + step))
                cfg["lr"] = float(lr_options[new_idx])
        except ValueError:
            cfg["lr"] = float(np.random.choice(lr_options))
    elif param == "filters_2":
        options = SEARCH_SPACE["filters_2"]
        val = cfg.get("filters_2")
        try:
            idx = options.index(val)
            step = np.random.choice([-1, 1])
            new_idx = max(0, min(len(options) - 1, idx + step))
            cfg["filters_2"] = int(options[new_idx])
        except ValueError:
            cfg["filters_2"] = int(np.random.choice(options))
    elif param == "num_conv_layers":
        options = SEARCH_SPACE["num_conv_layers"]
        val = cfg.get("num_conv_layers", 2)
        try:
            idx = options.index(val)
            step = np.random.choice([-1, 1])
            new_idx = max(0, min(len(options) - 1, idx + step))
            cfg["num_conv_layers"] = int(options[new_idx])
        except ValueError:
            cfg["num_conv_layers"] = int(np.random.choice(options))
    else:
        cfg["dropout_rate"] = float(np.random.choice(SEARCH_SPACE["dropout_rate"]))
    return cfg

def propose_heuristic_config(condition, trials):
    """
    Unified robust heuristic fallback.
    Avoids bias by standardizing the fallback strategy when API generation fails.
    """
    if not trials:
        return {
            "num_conv_layers": 2,
            "filters_2": 32,
            "activation": "ReLU",
            "dropout_rate": 0.2,
            "optimizer": "AdamW",
            "lr": 0.001,
            "batch_size": 32
        }
    
    evaluated_configs = [t["config"] for t in trials]
    best_trial = max(trials, key=lambda t: t["acc"])
    best_cfg = best_trial["config"]
    
    for _ in range(100):
        cfg = perturb_config_guided(best_cfg, best_trial["acc"])
        if cfg not in evaluated_configs:
            return cfg
            
    return get_random_config()

# --- Main Run Campaign Orchestration -----------------------------------------
async def execute_campaign():
    from run_deep_learning_harness import train_and_evaluate, evaluate_test_vault
    resumed_seed = None
    resumed_condition = None
    resumed_cycle = None
    
    campaign_results = {
        "dataset": "Dynamic Synthetic Manifold (PyTorch Residual MLP)",
        "SEEDS": SEEDS,
        "CYCLES": CYCLES,
        "conditions": {
            "stateless_baseline": {},
            "vector_rag": {},
            "rar_compressed": {}
        }
    }
    
    for cond in campaign_results["conditions"]:
        campaign_results["conditions"][cond] = {
            "val_accuracies": [],
            "test_accuracies": [],
            "redundancies": [],
            "prompt_densities": [],
            "wall_clock_latencies": [],
            "net_tokens": [],
            "generalization_gaps": [],
            "llm_proposal_counts": [],   # per-seed: # of proposals that came from the LLM
            "heuristic_proposal_counts": [],  # per-seed: # of heuristic fallbacks
            "best_found_trajectories": [],    # per-seed: best-found val acc per cycle (Phase 2)
            "best_in_context_trajectories": []  # per-seed: global-best visible in prompt? (rot)
        }

    # --- Cross-run accumulation (per-seed checkpointing) ----------------------
    # Free-tier daily caps mean a full campaign may span several runs. We persist
    # each completed seed to partial_results.json and skip seeds already done, so
    # results accumulate across runs/keys/days instead of restarting from scratch.
    PARTIAL_PATH = os.path.join(OUTPUT_DIR, "partial_results.json")
    completed_seeds = set()
    if os.path.exists(PARTIAL_PATH):
        try:
            with open(PARTIAL_PATH, "r", encoding="utf-8") as f:
                _partial = json.load(f)
            if _partial.get("conditions"):
                campaign_results = _partial["conditions"] and {
                    **campaign_results, "conditions": _partial["conditions"]}
                # Backfill any metric keys missing from older checkpoints
                for _cd in campaign_results["conditions"].values():
                    for _k in ("llm_proposal_counts", "heuristic_proposal_counts",
                               "best_found_trajectories", "best_in_context_trajectories"):
                        _cd.setdefault(_k, [])
            completed_seeds = set(_partial.get("completed_seeds", []))
            log.info("Resuming from %d completed seeds: %s",
                     len(completed_seeds), sorted(completed_seeds))
        except Exception as e:
            log.warning("Could not load partial_results.json (%s); starting fresh.", e)

    def _save_partial():
        with open(PARTIAL_PATH, "w", encoding="utf-8") as f:
            json.dump({"completed_seeds": sorted(completed_seeds),
                       "conditions": campaign_results["conditions"]}, f, indent=2)

    # SRE Hardening: Maintain a single ClientSession with persistent TCPConnector keep-alive pooling to prevent socket exhaustion
    connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
    async with aiohttp.ClientSession(connector=connector) as session:
        for seed in SEEDS:
            if seed in completed_seeds:
                log.info("Seed %s already complete (checkpoint); skipping.", seed)
                continue
            print(f"\n========================================================")
            print(f"> STARTING SEED CAMPAIGN: {seed}")
            print(f"========================================================")

            conditions_list = ["stateless_baseline", "vector_rag", "rar_compressed"]
            for cond_idx, cond in enumerate(conditions_list):
                wal_path = get_wal_path(cond, seed)
                wal = load_wal(wal_path)
                
                trials = collections.deque(maxlen=MAX_TRIAL_MEMORY)
                densities = []
                net_tokens = 0
                start_cycle = 1
                # Phase-2 instrumentation: per-cycle best-found accuracy, and whether the
                # current global-best trial's entry survived into this cycle's prompt
                # (False = the agent has "forgotten" its best result -> direct rot evidence).
                best_found_traj = []
                best_in_context_traj = []
                
                compressed_history = ""
                raw_history_buffer = []
                
                # Check for resumption state
                if wal:
                    print(f"WAL FOUND: Resumed campaign from checkpoint! Active Seed: {seed}, Condition: {cond}, Cycle: {wal['cycle']}")
                    campaign_results = wal["campaign_results"]
                    trials.extend(wal["trials"])
                    densities = wal.get("densities", [])
                    net_tokens = wal.get("net_tokens", 0)
                    
                    # SRE Hardening: Retry interrupted cycle without skipping it
                    start_cycle = wal["cycle"]
                    if cond == "rar_compressed":
                        custom = wal.get("custom_state", {})
                        compressed_history = custom.get("compressed_history", "")
                        raw_history_buffer = custom.get("raw_history_buffer", [])
                    print(f"Hydrated state. Resuming cycle from {start_cycle}...")
                else:
                    clear_wal(wal_path)
                    
                if start_cycle > CYCLES:
                    continue
                    
                start_time = time.time()
                consolidator = AsyncMemoryConsolidator()
                
                try:
                    for cycle in range(start_cycle, CYCLES + 1):
                        print(f"{cond.upper()} Cycle {cycle}/{CYCLES}...")
                        
                        # Process completed background consolidations
                        if cond == "rar_compressed" and consolidator.task and consolidator.task.done():
                            if consolidator.success:
                                compressed_history = consolidator.get_result()
                                raw_history_buffer = raw_history_buffer[consolidator.consolidated_count:]
                                print("SRE Main Loop: Hydrated GraphRAG memory and sliced buffer safely.")
                            else:
                                print("SRE Main Loop: Async consolidation failed. History buffer kept intact.")
                            consolidator.task = None
                        
                        # Build context
                        if cond == "stateless_baseline":
                            if trials:
                                # Verbose log truncated to C_MAX: at long horizons the oldest
                                # trials (incl. an early global best) fall out of context -> rot.
                                entries = [format_trial_verbose(t) for t in trials]
                                history_str, _kept, _total = truncate_to_budget(
                                    "### Prior Trials Evaluated:\n", entries, C_MAX)
                            else:
                                history_str = "This is the very first trial. You have no previous history.\n"
                        elif cond == "vector_rag":
                            if trials:
                                best_known = max(trials, key=lambda x: x["acc"])
                                candidate_dummy = best_known["config"]
                                history_str = retrieve_vector_rag_context(list(trials), candidate_dummy, budget_limit=2000)
                            else:
                                history_str = "This is the very first trial. You have no previous history.\n"
                        else: # rar_compressed
                            history_str = ""
                            if compressed_history:
                                # Input-boundary sanitization: the summary is LLM-generated
                                # free text re-entering the recursive prompt — sanitize it.
                                safe_summary = sanitize_log_entry(compressed_history)
                                history_str += f"### Lossless Summary of Prior Knowledge Map:\n{safe_summary}\n\n"
                            if raw_history_buffer:
                                history_str += "### Recent Trial Logs:\n"
                                for t in raw_history_buffer:
                                    history_str += format_trial_verbose(t)
                            elif not compressed_history:
                                history_str = "This is the very first trial. You have no previous history.\n"
                        
                        prompt = f"""
{SEARCH_SPACE_PROMPT}

Propose a configuration that has NOT been evaluated yet. Review the prior trial logs carefully to avoid redundancy.
Your response MUST contain a single, clean JSON block in the format:
{{
  "num_conv_layers": <int>,
  "filters_2": <int>,
  "activation": <"ReLU" or "ELU" or "LeakyReLU">,
  "dropout_rate": <float>,
  "optimizer": <"AdamW" or "SGD">,
  "lr": <float>,
  "batch_size": <int>
}}

{history_str}
"""
                        net_tokens += len(prompt) + 200
                        
                        # Save WAL checkpoint before LLM call
                        # SRE Hardening: Disk operations offloaded to background threads to prevent event loop blocks
                        await asyncio.to_thread(
                            save_wal, cond, seed, cycle, list(trials), densities, net_tokens, {
                                "compressed_history": compressed_history,
                                "raw_history_buffer": raw_history_buffer
                            } if cond == "rar_compressed" else None, campaign_results
                        )
                        
                        response = await call_llm(prompt, session=session)
                        config = parse_json_response(response) if response else None
                        mode = "LLM"
                        
                        if not config or not is_valid_config(config):
                            err_msg = "API Timeout/Failure" if not response else "JSON Parse/Validation Failure"
                            save_failed_payload(prompt, err_msg)
                            config = propose_heuristic_config(cond, list(trials))
                            mode = "heuristic"

                            
                        # Offload PyTorch training execution to threadpool
                        acc = await asyncio.to_thread(train_and_evaluate, config, seed, 15)
                        
                        is_redundant = any(t['config'] == config for t in trials)
                        trial_entry = {"config": config, "acc": acc, "redundant": is_redundant, "mode": mode}

                        # Phase-2 instrumentation (computed BEFORE appending this trial):
                        # was the best-so-far trial's record visible in the prompt just used?
                        if trials:
                            prev_best = max(trials, key=lambda t: t["acc"])
                            best_in_context_traj.append(
                                format_trial_verbose(prev_best) in history_str
                                or f"{prev_best['acc']:.4f}" in history_str)
                        else:
                            best_in_context_traj.append(True)  # first cycle: nothing to forget

                        trials.append(trial_entry)
                        best_found_traj.append(max(t["acc"] for t in trials)
                                               if len(best_found_traj) == 0
                                               else max(best_found_traj[-1], acc))
                        if cond == "rar_compressed":
                            raw_history_buffer.append(trial_entry)

                        densities.append(len(prompt) / float(C_MAX))
                        print(f"  Proposed: {config} -> Val Acc: {acc:.4f} (Redundant: {is_redundant})")
                        
                        # Trigger consolidator background task
                        if cond == "rar_compressed" and cycle % 3 == 0 and not consolidator.is_running:
                            consolidator.start_consolidation(compressed_history, raw_history_buffer, session)
                            
                        await asyncio.sleep(0.01)
                        
                    # Clean up pending consolidator tasks at completion
                    if cond == "rar_compressed" and consolidator.task:
                        try:
                            await consolidator.task
                            if consolidator.success:
                                compressed_history = consolidator.get_result()
                        except Exception as e:
                            print(f"Error awaiting final consolidator task: {e}")
                            
                finally:
                    # SRE Hardening: Ensure background tasks are cleanly terminated on exceptions/crashes
                    if consolidator.task and not consolidator.task.done():
                        print("SRE Clean: Cancelling active background memory consolidator...")
                        consolidator.task.cancel()
                        try:
                            await consolidator.task
                        except asyncio.CancelledError:
                            pass
                        except Exception as e:
                            print(f"SRE Clean: Error during worker cancellation: {e}")
                            
                cond_duration = time.time() - start_time
                val_accs = [t["acc"] for t in trials]
                redundancy = sum(1 for t in trials if t["redundant"])
                
                best_idx = np.argmax(val_accs)
                best_config = list(trials)[best_idx]["config"]
                
                # Locked Test Vault Evaluator (runs exactly once per condition/seed)
                test_acc = await asyncio.to_thread(evaluate_test_vault, best_config, seed, 15)
                print(f"{cond.upper()} Seed {seed} Final Val Acc: {max(val_accs):.4f}, Test Vault Acc: {test_acc:.4f}")
                
                campaign_results["conditions"][cond]["val_accuracies"].append(max(val_accs))
                campaign_results["conditions"][cond]["test_accuracies"].append(test_acc)
                campaign_results["conditions"][cond]["redundancies"].append(redundancy)
                campaign_results["conditions"][cond]["prompt_densities"].append(np.mean(densities))
                campaign_results["conditions"][cond]["wall_clock_latencies"].append(cond_duration)
                campaign_results["conditions"][cond]["net_tokens"].append(net_tokens)
                campaign_results["conditions"][cond]["generalization_gaps"].append(abs(max(val_accs) - test_acc))
                campaign_results["conditions"][cond]["llm_proposal_counts"].append(
                    sum(1 for t in trials if t.get("mode") == "LLM"))
                campaign_results["conditions"][cond]["heuristic_proposal_counts"].append(
                    sum(1 for t in trials if t.get("mode") == "heuristic"))
                campaign_results["conditions"][cond]["best_found_trajectories"].append(
                    [round(float(a), 4) for a in best_found_traj])
                campaign_results["conditions"][cond]["best_in_context_trajectories"].append(
                    [bool(b) for b in best_in_context_traj])
                
                # Clear isolated WAL logs on success
                clear_wal(wal_path)

            # Seed fully complete (all 3 conditions) — checkpoint to disk so the
            # campaign can resume here on the next run (free-tier daily cap).
            completed_seeds.add(seed)
            _save_partial()
            log.info("Seed %s complete and checkpointed (%d seeds done so far).",
                     seed, len(completed_seeds))

    # --- STATISTICAL AUDIT & RESULTS SERIALIZATION ----------------------------
    try:
        w_stat, p_val = wilcoxon(
            campaign_results["conditions"]["rar_compressed"]["test_accuracies"],
            campaign_results["conditions"]["stateless_baseline"]["test_accuracies"],
            alternative="greater"
        )
        p_val_str = f"{p_val:.4f}"
    except Exception as e:
        # Do NOT emit a "n.s."-style string that reads like a real statistical
        # outcome; mark it explicitly as an error and log the cause (BL-11.2).
        log.error("Wilcoxon test failed: %s", e, exc_info=True)
        p_val_str = "STAT_ERROR"

    all_seeds = sorted(completed_seeds) if completed_seeds else SEEDS
    results_to_save = {
        "meta": "Upgrade campaign with PyTorch Residual MLP hyperparameter search on dynamic synthetic manifold",
        "SEEDS": all_seeds,
        "CYCLES": CYCLES,
        "wilcoxon_p_value_RAR_vs_Baseline": p_val_str,
        "data": campaign_results
    }
    
    with open(os.path.join(OUTPUT_DIR, "pilot_results.json"), "w") as f:
        json.dump(results_to_save, f, indent=2)
        
    print(f"\nVerification Success: Upgraded campaign logs written to pilot_results.json")
    
    # --- HIGH-FIDELITY PLOTTING -----------------------------------------------
    plt.rcParams['mathtext.fontset'] = 'dejavuserif'
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 10
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left Plot: Test accuracy boxplots
    ax1.grid(True, linestyle='--', alpha=0.6)
    data_to_plot = [
        campaign_results["conditions"]["stateless_baseline"]["test_accuracies"],
        campaign_results["conditions"]["vector_rag"]["test_accuracies"],
        campaign_results["conditions"]["rar_compressed"]["test_accuracies"]
    ]
    ax1.boxplot(data_to_plot, labels=['Baseline', 'Vector RAG', 'RAR (Compressed)'])
    ax1.set_title(rf"$\mathbf{{Test\ Vault\ Accuracies\ (N={len(SEEDS)}\ Seeds)}}$", fontweight='bold')
    ax1.set_ylabel("Strict Test Accuracy", fontweight='bold')
    
    # Right Plot: Context densities and Net Tokens Dual-Axis
    ax2.grid(True, linestyle='--', alpha=0.6)
    x = np.arange(3)
    densities_mean = [
        np.mean(campaign_results["conditions"]["stateless_baseline"]["prompt_densities"]),
        np.mean(campaign_results["conditions"]["vector_rag"]["prompt_densities"]),
        np.mean(campaign_results["conditions"]["rar_compressed"]["prompt_densities"])
    ]
    tokens_mean = [
        np.mean(campaign_results["conditions"]["stateless_baseline"]["net_tokens"]),
        np.mean(campaign_results["conditions"]["vector_rag"]["net_tokens"]),
        np.mean(campaign_results["conditions"]["rar_compressed"]["net_tokens"])
    ]
    
    ax2.bar(x - 0.2, densities_mean, width=0.35, label="Context Density", color='#1c4f8a')
    ax2.set_ylabel(r"Mean Context Density ($\delta$)", fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Baseline', 'Vector RAG', 'RAR'])
    ax2.set_title(r"$\mathbf{Context\ and\ Token\ Tradeoffs}$", fontweight='bold')
    
    ax2_twin = ax2.twinx()
    ax2_twin.bar(x + 0.2, tokens_mean, width=0.35, label="Net Tokens", color='#b41e1e')
    ax2_twin.set_ylabel("Net Tokens (chars)", fontweight='bold')
    
    ax2.legend(loc='upper left', bbox_to_anchor=(0.0, -0.15))
    ax2_twin.legend(loc='upper right', bbox_to_anchor=(1.0, -0.15))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "fig2_crs_trajectory.png"), dpi=300)
    plt.close()
    
    # Re-plot density comparisons alone
    plt.figure(figsize=(7, 4.5))
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.bar(['Baseline', 'Vector RAG', 'RAR'], densities_mean, color=['#b41e1e', '#1c4f8a', '#2ca02c'])
    plt.ylabel(r"Mean Context Density ($\delta$)", fontweight='bold')
    plt.title(r"$\mathbf{Empirical\ Context\ Density\ comparison}$", fontweight='bold')
    plt.savefig(os.path.join(OUTPUT_DIR, "fig3_density.png"), dpi=300)
    plt.close()
    
    print("Scientific visual assets saved directly to the workspace.")

if __name__ == "__main__":
    asyncio.run(execute_campaign())
