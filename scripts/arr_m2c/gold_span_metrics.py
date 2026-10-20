"""Gold-span ↔ SHAP word alignment metrics for ARR M2C."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Reuse M2B offset alignment
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "arr_m2"))
from offset_alignment import AlignmentResult, SourceWord, align_record  # noqa: E402


@dataclass
class GoldSpan:
    start: int
    end: int
    bias: str  # lex | inf
    txt: str


def char_mask(text_len: int, spans: Sequence[GoldSpan]) -> np.ndarray:
    m = np.zeros(text_len, dtype=bool)
    for sp in spans:
        a = max(0, sp.start)
        b = min(text_len, sp.end)
        if a < b:
            m[a:b] = True
    return m


def word_overlap_frac(w: SourceWord, gold_chars: np.ndarray) -> float:
    if w.end <= w.start:
        return 0.0
    seg = gold_chars[w.start : w.end]
    return float(seg.mean()) if len(seg) else 0.0


def word_in_gold(w: SourceWord, gold_chars: np.ndarray, thresh: float = 0.5) -> bool:
    """Word counts as gold evidence if ≥ thresh of its characters overlap a gold span."""
    return word_overlap_frac(w, gold_chars) >= thresh


def average_precision(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """AP for ranking gold words by score (higher = more attributed)."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    if y.sum() == 0 or y.sum() == len(y):
        return float("nan")
    order = np.argsort(-s, kind="mergesort")
    y_sorted = y[order]
    tp = 0
    precisions = []
    for i, lab in enumerate(y_sorted, start=1):
        if lab:
            tp += 1
            precisions.append(tp / i)
    return float(np.mean(precisions)) if precisions else float("nan")


def compute_sentence_metrics(
    text: str,
    words: Sequence[SourceWord],
    spans: Sequence[GoldSpan],
    *,
    top_k: int = 5,
    gold_word_thresh: float = 0.5,
) -> Dict:
    """Compute alignment metrics for one (sentence, model explanation)."""
    n = len(text)
    gold = char_mask(n, spans)
    gold_cov = float(gold.mean()) if n else 0.0
    abs_mass = sum(abs(w.shap) for w in words) or 1e-12
    pos_mass = sum(max(w.shap, 0.0) for w in words) or 1e-12

    abs_in = 0.0
    pos_in = 0.0
    for w in words:
        frac = word_overlap_frac(w, gold)
        abs_in += abs(w.shap) * frac
        pos_in += max(w.shap, 0.0) * frac

    labels = [1 if word_in_gold(w, gold, gold_word_thresh) else 0 for w in words]
    scores_abs = [abs(w.shap) for w in words]
    scores_pos = [w.shap for w in words]

    # top-k by |SHAP|
    order = sorted(range(len(words)), key=lambda i: abs(words[i].shap), reverse=True)
    k = min(top_k, len(words))
    top = order[:k]
    top_hit = sum(labels[i] for i in top)
    n_gold_words = sum(labels)
    precision_at_k = top_hit / k if k else float("nan")
    recall_at_k = top_hit / n_gold_words if n_gold_words else float("nan")

    ap_abs = average_precision(labels, scores_abs)
    # ranking by signed positive support: use shap as score
    ap_signed = average_precision(labels, scores_pos)

    # Exclude AP when too few gold or non-gold words
    ap_eligible = int(n_gold_words >= 1 and (len(words) - n_gold_words) >= 1)

    bias_types = sorted({sp.bias for sp in spans}) if spans else []
    if not spans:
        ann_cat = "non_biased"
    elif bias_types == ["lex"]:
        ann_cat = "lex_only"
    elif bias_types == ["inf"]:
        ann_cat = "inf_only"
    else:
        ann_cat = "both"

    return {
        "n_spans": len(spans),
        "ann_category": ann_cat,
        "gold_char_coverage": gold_cov,
        "n_words": len(words),
        "n_gold_words": n_gold_words,
        "abs_mass_in_gold": abs_in / abs_mass,
        "pos_mass_in_gold": pos_in / pos_mass,
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "top_k": k,
        "ap_abs": ap_abs if ap_eligible else float("nan"),
        "ap_signed": ap_signed if ap_eligible else float("nan"),
        "ap_eligible": ap_eligible,
        "has_lex_span": int(any(sp.bias == "lex" for sp in spans)),
        "has_inf_span": int(any(sp.bias == "inf" for sp in spans)),
    }


def random_length_matched_spans(
    text: str,
    spans: Sequence[GoldSpan],
    rng: random.Random,
) -> List[GoldSpan]:
    """Place random spans with same lengths as gold (non-overlapping when possible)."""
    n = len(text)
    lens = [max(1, sp.end - sp.start) for sp in spans]
    placed: List[GoldSpan] = []
    occupied = np.zeros(n, dtype=bool)
    for L in lens:
        if L >= n:
            placed.append(GoldSpan(0, n, "rand", text))
            occupied[:] = True
            continue
        # try several positions
        found = None
        for _ in range(50):
            start = rng.randrange(0, n - L + 1)
            if not occupied[start : start + L].any():
                found = start
                break
        if found is None:
            found = rng.randrange(0, n - L + 1)
        end = found + L
        occupied[found:end] = True
        placed.append(GoldSpan(found, end, "rand", text[found:end]))
    return placed


def random_word_set_metrics(
    words: Sequence[SourceWord],
    labels: Sequence[int],
    n_pick: int,
    rng: random.Random,
) -> Dict[str, float]:
    """Precision/recall if randomly picking n_pick words as 'highlighted'."""
    n = len(words)
    if n == 0 or n_pick <= 0:
        return {"precision_at_k": float("nan"), "recall_at_k": float("nan")}
    k = min(n_pick, n)
    idxs = list(range(n))
    rng.shuffle(idxs)
    pick = idxs[:k]
    hit = sum(labels[i] for i in pick)
    n_gold = sum(labels)
    return {
        "precision_at_k": hit / k,
        "recall_at_k": hit / n_gold if n_gold else float("nan"),
    }


def positional_control_spans(
    text: str,
    spans: Sequence[GoldSpan],
) -> List[GoldSpan]:
    """Shift each span to the opposite half of the sentence when possible (positional control)."""
    n = len(text)
    out = []
    for sp in spans:
        L = sp.end - sp.start
        # try mirror around midpoint
        mid = n // 2
        if sp.start < mid:
            start = min(n - L, mid + (mid - sp.end) % max(mid, 1))
        else:
            start = max(0, mid - L - ((sp.start - mid) % max(n - mid, 1)))
        start = max(0, min(start, n - L))
        out.append(GoldSpan(start, start + L, "pos", text[start : start + L]))
    return out


def bootstrap_mean_ci(values: List[float], n_boot: int = 2000, seed: int = 7):
    vals = [v for v in values if v == v]  # drop nan
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    arr = np.asarray(vals, dtype=float)
    means = sorted(
        float(rng.choice(arr, size=len(arr), replace=True).mean()) for _ in range(n_boot)
    )
    return float(arr.mean()), means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]
