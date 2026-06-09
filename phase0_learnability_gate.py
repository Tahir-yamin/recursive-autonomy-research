"""Phase 0 learnability gate (RAR v2).

Validates that Task A is learnable AND discriminating BEFORE any campaign:
a strong config must reach high accuracy and a weak config must lag well behind.
If this gate fails, no amount of memory/search can show an accuracy effect.

Training procedure (the one the campaign will use):
  AdamW + linear warmup (2 ep) + cosine annealing, 40 epochs, early stopping on val.

GATE: strong_test >= 0.75  AND  (strong_test - weak_test) >= 0.20
"""
import math, numpy as np, torch
import torch.nn as nn, torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

torch.set_num_threads(max(1, (torch.get_num_threads() or 2)))

def set_seed(s):
    np.random.seed(s); torch.manual_seed(s)

# ---- Task A: harder 10-class manifold, learnable but discriminating ----------
def make_task_a(n_samples=12000, seed=42):
    X, y = make_classification(
        n_samples=n_samples, n_features=64, n_informative=55, n_redundant=0,
        n_repeated=0, n_classes=10, n_clusters_per_class=2, class_sep=1.3,
        flip_y=0.02, random_state=seed)
    # non-linear warp -> not linearly separable; needs real capacity to fit
    X = X + 0.4*np.tanh(0.7*X) + 0.3*np.sin(X*np.pi)
    X = X.astype(np.float32); y = y.astype(np.int64)
    Xtv, Xte, ytv, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    Xtr, Xva, ytr, yva = train_test_split(Xtv, ytv, test_size=0.30, random_state=seed, stratify=ytv)
    return Xtr, ytr, Xva, yva, Xte, yte

class DynamicMLP(nn.Module):
    def __init__(self, n_classes=10, num_blocks=2, hidden=32, act="ReLU", dropout=0.2):
        super().__init__()
        A = {"ReLU": nn.ReLU, "ELU": nn.ELU, "LeakyReLU": nn.LeakyReLU}.get(act, nn.ReLU)
        self.inp = nn.Sequential(nn.Linear(64, hidden), nn.BatchNorm1d(hidden), A())
        blocks = []
        for _ in range(num_blocks):
            blocks.append(nn.Sequential(nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden),
                                        A(), nn.Dropout(dropout), nn.Linear(hidden, hidden),
                                        nn.BatchNorm1d(hidden)))
        self.blocks = nn.ModuleList(blocks); self.act = A()
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, n_classes))
    def forward(self, x):
        x = self.inp(x)
        for b in self.blocks:
            x = self.act(x + b(x))
        return self.head(x)

def train_eval(cfg, data, seed=42, epochs=40, warmup=2, patience=8):
    Xtr, ytr, Xva, yva, Xte, yte = data
    set_seed(seed)
    dev = torch.device("cpu")
    label_smooth = float(cfg.get("label_smoothing", 0.0))
    bs = int(cfg["batch_size"]); base_lr = float(cfg["lr"]); wd = float(cfg.get("weight_decay", 1e-4))
    model = DynamicMLP(10, int(cfg["num_conv_layers"]), int(cfg["filters_2"]),
                       cfg["activation"], float(cfg["dropout_rate"])).to(dev)
    crit = nn.CrossEntropyLoss(label_smoothing=label_smooth)
    if cfg.get("optimizer", "AdamW") == "AdamW":
        opt = optim.AdamW(model.parameters(), lr=base_lr, weight_decay=wd)
    else:
        opt = optim.SGD(model.parameters(), lr=base_lr, momentum=0.9, weight_decay=wd)
    tl = DataLoader(TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr)), batch_size=bs, shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xva), torch.from_numpy(yva)), batch_size=256)
    tel = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(yte)), batch_size=256)
    steps = len(tl)
    def lr_at(ep):  # warmup then cosine to 0
        if ep < warmup: return (ep + 1) / warmup
        p = (ep - warmup) / max(1, (epochs - warmup))
        return 0.5 * (1 + math.cos(math.pi * p))
    def acc(loader):
        model.eval(); c = t = 0
        with torch.no_grad():
            for bx, by in loader:
                p = model(bx).argmax(1); c += (p == by).sum().item(); t += by.size(0)
        return c / t
    best_va, best_state, bad = 0.0, None, 0
    for ep in range(epochs):
        for g in opt.param_groups: g["lr"] = base_lr * lr_at(ep)
        model.train()
        for bx, by in tl:
            opt.zero_grad(); loss = crit(model(bx), by); loss.backward(); opt.step()
        va = acc(vl)
        if va > best_va: best_va, best_state, bad = va, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience: break
    if best_state: model.load_state_dict(best_state)
    return acc(tel), best_va

STRONG = {"num_conv_layers": 3, "filters_2": 128, "activation": "LeakyReLU", "dropout_rate": 0.1,
          "optimizer": "AdamW", "lr": 1e-3, "batch_size": 64, "weight_decay": 1e-4, "label_smoothing": 0.05}
WEAK   = {"num_conv_layers": 1, "filters_2": 16, "activation": "ReLU", "dropout_rate": 0.5,
          "optimizer": "SGD", "lr": 0.05, "batch_size": 256, "weight_decay": 1e-2, "label_smoothing": 0.0}

if __name__ == "__main__":
    data = make_task_a(seed=42)
    print("Task A: 10-class, train/val/test =", [len(data[i]) for i in (0, 2, 4)])
    s_test, s_val = train_eval(STRONG, data); print(f"STRONG: test={s_test*100:.1f}%  val={s_val*100:.1f}%")
    w_test, w_val = train_eval(WEAK, data);   print(f"WEAK:   test={w_test*100:.1f}%  val={w_val*100:.1f}%")
    gap = s_test - w_test
    print(f"GAP: {gap*100:.1f} points")
    ok = (s_test >= 0.75) and (gap >= 0.20)
    print("GATE:", "PASS" if ok else "FAIL", f"(need strong>=75% and gap>=20pp)")
