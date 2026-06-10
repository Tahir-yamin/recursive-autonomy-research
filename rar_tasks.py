"""Benchmark tasks for the RAR extended evaluation.

All tasks return (X_train, y_train, X_val, y_val, X_test, y_test): 64-feature, int64
labels, stratified 50/25/25, float32. Real-image tasks are reduced to 64 dimensions by a
LEAK-FREE pipeline (StandardScaler + PCA fit on TRAIN only, then applied to val/test).

Select with the TASK environment variable:
  TASK=A  Synthetic 10-class manifold      (Phase-0 validated; strong ~91% / weak ~56%)
  TASK=B  CIFAR-10 -> PCA-64               (HARDEST: real images, an MLP genuinely struggles;
                                            expect strong ~45-52% / weak ~25-32%, chance 10%)
  TASK=C  Fashion-MNIST -> PCA-64          (real images, moderate; strong ~85% / weak ~65%)
  TASK=D  Forest CoverType (54 feat -> 64) (real tabular; wide search spread ~42-86%)

NOTE: B/C/D download their data once via sklearn.fetch_openml (needs internet; cached after).
Run `python verify_tasks.py` (with TASK set) to measure each task's search-space spread
BEFORE committing GPU/LLM time to a campaign.
"""
import os
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

N_FEATURES = 64


def _split(X, y, seed):
    """Plain stratified 50/25/25 split (no dimensionality reduction)."""
    X = X.astype(np.float32); y = y.astype(np.int64)
    Xtv, Xte, ytv, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    Xtr, Xva, ytr, yva = train_test_split(Xtv, ytv, test_size=0.30, random_state=seed, stratify=ytv)
    return Xtr, ytr, Xva, yva, Xte, yte


def _split_with_pca(X, y, seed, n_comp=N_FEATURES):
    """Leak-free reduction to n_comp dims: split first, then fit Scaler+PCA on TRAIN only
    and apply to val/test. This is the Q1-clean way to tabularise image data."""
    X = X.astype(np.float32); y = y.astype(np.int64)
    Xtv, Xte, ytv, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    Xtr, Xva, ytr, yva = train_test_split(Xtv, ytv, test_size=0.30, random_state=seed, stratify=ytv)
    sc1 = StandardScaler().fit(Xtr)
    pca = PCA(n_components=min(n_comp, Xtr.shape[1]), random_state=seed).fit(sc1.transform(Xtr))
    Xtr_p = pca.transform(sc1.transform(Xtr))
    sc2 = StandardScaler().fit(Xtr_p)
    def tf(A):
        return sc2.transform(pca.transform(sc1.transform(A))).astype(np.float32)
    return (sc2.transform(Xtr_p).astype(np.float32), ytr, tf(Xva), yva, tf(Xte), yte)


# --- Task A: validated synthetic manifold ------------------------------------
def make_task_a(n_samples=12000, seed=42):
    X, y = make_classification(
        n_samples=n_samples, n_features=N_FEATURES, n_informative=55, n_redundant=0,
        n_repeated=0, n_classes=10, n_clusters_per_class=2, class_sep=1.3,
        flip_y=0.02, random_state=seed)
    X = X + 0.4 * np.tanh(0.7 * X) + 0.3 * np.sin(X * np.pi)
    return _split(X, y, seed)


# --- Real hard tasks (downloaded via OpenML, reduced to 64 dims) -------------
def _fetch_openml_subsample(name, version, n, seed):
    from sklearn.datasets import fetch_openml
    d = fetch_openml(name, version=version, as_frame=False)
    X = np.asarray(d.data, dtype=np.float32)
    y = np.asarray(d.target)
    # labels may be strings -> map to 0..k-1
    classes = sorted(set(y.tolist()))
    cmap = {c: i for i, c in enumerate(classes)}
    y = np.array([cmap[v] for v in y], dtype=np.int64)
    if n and n < len(X):
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(X), n, replace=False)
        X, y = X[idx], y[idx]
    return X, y


def make_task_b_cifar(n=12000, seed=42):
    """CIFAR-10 (3072 px) -> leak-free PCA-64. Hardest: MLPs cannot exploit spatial
    structure, so a wide accuracy spread emerges across configs."""
    X, y = _fetch_openml_subsample("CIFAR_10", 1, n, seed)
    return _split_with_pca(X, y, seed)


def make_task_c_fashion(n=12000, seed=42):
    """Fashion-MNIST (784 px) -> leak-free PCA-64. Real, moderate difficulty."""
    X, y = _fetch_openml_subsample("Fashion-MNIST", 1, n, seed)
    return _split_with_pca(X, y, seed)


def make_task_d_covtype(n=12000, seed=42):
    """Forest CoverType (54 real tabular features -> padded to 64). 7 classes.
    Notebook search showed a wide spread (~42-86%) across configs."""
    from sklearn.datasets import fetch_covtype
    d = fetch_covtype()
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(d.data), min(n, len(d.data)), replace=False)
    X = d.data[idx].astype(np.float32)
    X = np.pad(X, ((0, 0), (0, max(0, N_FEATURES - X.shape[1]))))[:, :N_FEATURES]
    X = StandardScaler().fit_transform(X).astype(np.float32)
    y = (d.target[idx] - 1).astype(np.int64)
    return _split(X, y, seed)


_TASKS = {
    "A": make_task_a,
    "B": make_task_b_cifar,
    "C": make_task_c_fashion,
    "D": make_task_d_covtype,
}


def get_dataset(seed=42):
    task = os.environ.get("TASK", "A").upper()
    fn = _TASKS.get(task, make_task_a)
    try:
        return fn(seed=seed)
    except TypeError:
        return fn(seed)
