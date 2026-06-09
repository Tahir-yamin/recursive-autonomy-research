"""Benchmark tasks for the RAR extended evaluation.

Task A: the Phase-0-validated synthetic 10-class manifold (learnable + discriminating;
        strong ~91%, weak ~56%, ~35pp dynamic range).
Task B: a real dataset (sklearn digits: 8x8 handwritten digits, 64 features, 10 classes)
        for generality.

Select with the TASK environment variable: TASK=A (default) or TASK=B.
All tasks return (X_train, y_train, X_val, y_val, X_test, y_test), 64-dim, 10-class,
stratified 50/25/25, float32 / int64.
"""
import os
import numpy as np
from sklearn.datasets import make_classification, load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

N_CLASSES = 10
N_FEATURES = 64


def _split(X, y, seed):
    X = X.astype(np.float32); y = y.astype(np.int64)
    Xtv, Xte, ytv, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    Xtr, Xva, ytr, yva = train_test_split(Xtv, ytv, test_size=0.30, random_state=seed, stratify=ytv)
    return Xtr, ytr, Xva, yva, Xte, yte


def make_task_a(n_samples=12000, seed=42):
    """Phase-0-validated 10-class synthetic manifold (capacity-sensitive)."""
    X, y = make_classification(
        n_samples=n_samples, n_features=N_FEATURES, n_informative=55, n_redundant=0,
        n_repeated=0, n_classes=N_CLASSES, n_clusters_per_class=2, class_sep=1.3,
        flip_y=0.02, random_state=seed)
    X = X + 0.4 * np.tanh(0.7 * X) + 0.3 * np.sin(X * np.pi)
    return _split(X, y, seed)


def make_task_b(seed=42):
    """Real dataset: sklearn handwritten digits (8x8 -> 64 features, 10 classes).
    Standardised; the split varies by seed for N independent runs."""
    d = load_digits()
    X = StandardScaler().fit_transform(d.data)  # 1797 x 64
    return _split(X, d.target, seed)


def get_dataset(seed=42):
    task = os.environ.get("TASK", "A").upper()
    if task == "B":
        return make_task_b(seed)
    return make_task_a(seed=seed)
