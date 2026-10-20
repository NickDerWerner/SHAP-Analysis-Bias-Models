"""Shared bootstrap / regression helpers for M2D."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


def bootstrap_mean_ci(
    values: Sequence[float],
    n_boot: int = 2000,
    seed: int = 7,
) -> Tuple[float, float, float]:
    vals = [float(v) for v in values if v == v]
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    arr = np.asarray(vals, dtype=float)
    means = sorted(
        float(rng.choice(arr, size=len(arr), replace=True).mean()) for _ in range(n_boot)
    )
    return float(arr.mean()), means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def paired_bootstrap_mean_ci(
    diffs: Sequence[float],
    n_boot: int = 2000,
    seed: int = 7,
) -> Tuple[float, float, float]:
    """Sentence-level paired bootstrap on already-computed differences."""
    return bootstrap_mean_ci(diffs, n_boot=n_boot, seed=seed)


def cluster_bootstrap_mean_ci(
    values: Sequence[float],
    clusters: Sequence[str],
    n_boot: int = 2000,
    seed: int = 7,
) -> Tuple[float, float, float]:
    """Resample clusters (e.g. triplet_uuid) with replacement; keep all members.

    Accounts for correlated sentences within an article/triplet.
    """
    vals = np.asarray(list(values), dtype=float)
    clus = np.asarray(list(clusters))
    mask = np.array([v == v for v in vals])
    vals, clus = vals[mask], clus[mask]
    if len(vals) == 0:
        return float("nan"), float("nan"), float("nan")
    uniq = np.unique(clus)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        draw = rng.choice(uniq, size=len(uniq), replace=True)
        pieces = [vals[clus == c] for c in draw]
        pooled = np.concatenate(pieces) if pieces else np.array([])
        if len(pooled) == 0:
            continue
        means.append(float(pooled.mean()))
    means.sort()
    if not means:
        return float("nan"), float("nan"), float("nan")
    return float(vals.mean()), means[int(0.025 * len(means))], means[int(0.975 * len(means))]


def ols_coef_ci(
    y: np.ndarray,
    X: np.ndarray,
    n_boot: int = 1500,
    seed: int = 7,
) -> Dict[str, Tuple[float, float, float]]:
    """Simple OLS with bootstrap CIs on coefficients. X includes intercept column."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    y, X = y[ok], X[ok]
    n, p = X.shape
    if n < p + 2:
        return {f"b{j}": (float("nan"), float("nan"), float("nan")) for j in range(p)}
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        b, *_ = np.linalg.lstsq(X[idx], y[idx], rcond=None)
        boots.append(b)
    boots = np.asarray(boots)
    out = {}
    for j in range(p):
        col = sorted(boots[:, j])
        out[f"b{j}"] = (
            float(beta[j]),
            float(col[int(0.025 * n_boot)]),
            float(col[int(0.975 * n_boot)]),
        )
    return out


def coverage_matched_pairs(
    lex_rows: List[dict],
    inf_rows: List[dict],
    cov_key: str = "gold_char_coverage",
    tol: float = 0.05,
    seed: int = 7,
) -> List[Tuple[dict, dict]]:
    """Greedy 1:1 match of lex and inf sentences with similar gold coverage."""
    rng = np.random.default_rng(seed)
    lex = list(lex_rows)
    inf = list(inf_rows)
    rng.shuffle(lex)
    used = set()
    pairs = []
    for lr in lex:
        lc = float(lr[cov_key])
        best = None
        best_d = 1e9
        for i, ir in enumerate(inf):
            if i in used:
                continue
            d = abs(float(ir[cov_key]) - lc)
            if d < best_d and d <= tol:
                best_d = d
                best = i
        if best is not None:
            used.add(best)
            pairs.append((lr, inf[best]))
    return pairs
