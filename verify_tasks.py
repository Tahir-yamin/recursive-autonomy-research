"""Standalone task-difficulty verifier (no LLM, no tokens, CPU-only).

For the task selected by the TASK env var, this:
  1. trains a STRONG and a WEAK hand-picked config (reference gap), and
  2. samples K random configs from the campaign SEARCH_SPACE and reports the
     min / max / mean / RANGE of test accuracy across them.

The meaningful gate for the RAR experiment is the SEARCH-SPACE RANGE: if good and bad
configs differ by >= 20 points, search quality (and therefore memory) can register in
accuracy. A single weak config can be misleading (see covtype), so range is what counts.

USAGE (run locally or in Colab; nothing is sent anywhere):
    TASK=A python verify_tasks.py
    TASK=B VERIFY_K=8 VERIFY_EPOCHS=25 python verify_tasks.py
Tasks: A synthetic | B CIFAR-10->PCA64 | C Fashion-MNIST->PCA64 | D covtype
"""
import os, math, time, numpy as np, torch
import torch.nn as nn, torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import rar_tasks

torch.set_num_threads(max(1, torch.get_num_threads() or 2))

# Campaign search space (must match run_pilot_experiment.py SEARCH_SPACE)
SEARCH_SPACE = {
    "num_conv_layers": [2, 3, 4, 5, 7],
    "filters_2": [32, 64, 128, 256, 512],
    "activation": ["ReLU", "ELU", "LeakyReLU"],
    "dropout_rate": [0.0, 0.05, 0.1, 0.2],
    "optimizer": ["AdamW", "SGD"],
    "lr": [0.0001, 0.001, 0.01],
    "batch_size": [32, 64, 128],
}
STRONG = {"num_conv_layers": 5, "filters_2": 256, "activation": "LeakyReLU", "dropout_rate": 0.05,
          "optimizer": "AdamW", "lr": 0.01, "batch_size": 64, "weight_decay": 1e-4, "label_smoothing": 0.05}
WEAK = {"num_conv_layers": 2, "filters_2": 32, "activation": "ReLU", "dropout_rate": 0.2,
        "optimizer": "SGD", "lr": 0.0001, "batch_size": 128, "weight_decay": 1e-2, "label_smoothing": 0.0}


def set_seed(s):
    np.random.seed(s); torch.manual_seed(s)


class MLP(nn.Module):
    def __init__(self, blocks, hidden, act, dropout, n_classes):
        super().__init__()
        A = {"ReLU": nn.ReLU, "ELU": nn.ELU, "LeakyReLU": nn.LeakyReLU}.get(act, nn.ReLU)
        self.inp = nn.Sequential(nn.Linear(64, hidden), nn.BatchNorm1d(hidden), A())
        self.blocks = nn.ModuleList([nn.Sequential(
            nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden), A(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden)) for _ in range(blocks)])
        self.act = A(); self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, n_classes))
    def forward(self, x):
        x = self.inp(x)
        for b in self.blocks: x = self.act(x + b(x))
        return self.head(x)


def train_eval(cfg, data, seed=42, epochs=25, warmup=2, patience=6):
    Xtr, ytr, Xva, yva, Xte, yte = data
    set_seed(seed); dev = torch.device("cpu")
    n_classes = int(np.max(ytr)) + 1
    bs = int(cfg["batch_size"]); base_lr = float(cfg["lr"])
    wd = float(cfg.get("weight_decay", 1e-4)); ls = float(cfg.get("label_smoothing", 0.05))
    model = MLP(int(cfg["num_conv_layers"]), int(cfg["filters_2"]), cfg["activation"],
                float(cfg["dropout_rate"]), n_classes).to(dev)
    crit = nn.CrossEntropyLoss(label_smoothing=ls)
    opt = (optim.AdamW(model.parameters(), lr=base_lr, weight_decay=wd)
           if cfg.get("optimizer", "AdamW") == "AdamW"
           else optim.SGD(model.parameters(), lr=base_lr, momentum=0.9, weight_decay=wd))
    tl = DataLoader(TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr)), batch_size=bs, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xva), torch.from_numpy(yva)), batch_size=256)
    tel = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(yte)), batch_size=256)
    def lr_mult(ep):
        if ep < warmup: return (ep + 1) / warmup
        p = (ep - warmup) / max(1, epochs - warmup); return 0.5 * (1 + math.cos(math.pi * p))
    def acc(loader):
        model.eval(); c = t = 0
        with torch.no_grad():
            for bx, by in loader:
                c += (model(bx).argmax(1) == by).sum().item(); t += by.size(0)
        return c / t
    best, best_state, bad = 0.0, None, 0
    for ep in range(epochs):
        for g in opt.param_groups: g["lr"] = base_lr * lr_mult(ep)
        model.train()
        for bx, by in tl:
            opt.zero_grad(); crit(model(bx), by).backward(); opt.step()
        va = acc(vl)
        if va > best: best, best_state, bad = va, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience: break
    if best_state: model.load_state_dict(best_state)
    return acc(tel)


def sample_config(rng):
    return {k: (rng.choice(v).item() if not isinstance(v[0], str) else str(rng.choice(v)))
            for k, v in SEARCH_SPACE.items()}


if __name__ == "__main__":
    task = os.environ.get("TASK", "A").upper()
    K = int(os.environ.get("VERIFY_K", "8"))
    EP = int(os.environ.get("VERIFY_EPOCHS", "25"))
    print(f"=== Verifying TASK={task} (K={K} random configs, {EP} epochs each, CPU) ===")
    t0 = time.time()
    data = rar_tasks.get_dataset(seed=42)
    print("Loaded. train/val/test =", [len(data[i]) for i in (0, 2, 4)],
          "| classes =", int(np.max(data[1])) + 1, "| dim =", data[0].shape[1])

    s = train_eval(STRONG, data, epochs=EP); w = train_eval(WEAK, data, epochs=EP)
    print(f"Hand-picked:  STRONG={s*100:.1f}%   WEAK={w*100:.1f}%   gap={ (s-w)*100:.1f}pp")

    rng = np.random.default_rng(0)
    accs = []
    for i in range(K):
        cfg = sample_config(rng)
        a = train_eval(cfg, data, epochs=EP)
        accs.append(a)
        print(f"  sample {i+1}/{K}: {a*100:5.1f}%  ({cfg['num_conv_layers']}L x {cfg['filters_2']}W, "
              f"lr={cfg['lr']}, {cfg['optimizer']}, drop={cfg['dropout_rate']})")
    accs = np.array(accs) * 100
    rng_pp = accs.max() - accs.min()
    print("\n--- SEARCH-SPACE SPREAD (the meaningful metric) ---")
    print(f"min={accs.min():.1f}%  max={accs.max():.1f}%  mean={accs.mean():.1f}%  RANGE={rng_pp:.1f}pp")
    verdict = "PASS (search spread >= 20pp -> hypothesis testable)" if rng_pp >= 20 else \
              "WEAK (spread < 20pp -> search quality may not register in accuracy)"
    print("VERDICT:", verdict)
    print(f"(elapsed {time.time()-t0:.0f}s)")
