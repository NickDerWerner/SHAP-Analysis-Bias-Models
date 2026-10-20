"""Task A — robustness of M2C gold-span alignment findings."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from stats_utils import (
    bootstrap_mean_ci,
    cluster_bootstrap_mean_ci,
    coverage_matched_pairs,
    ols_coef_ci,
    paired_bootstrap_mean_ci,
)

ROOT = Path(__file__).resolve().parents[2]
M2C_ALIGN = ROOT / "outputs" / "arr_m2c" / "gold_span_alignment.csv"
M2B_RESULTS = ROOT / "outputs" / "arr_m2b" / "medium_results.csv"
OUT = ROOT / "outputs" / "arr_m2d"

METRICS = [
    ("abs_minus_random_span", "abs_minus_rand"),
    ("pos_minus_random_span", "pos_minus_rand"),
    ("abs_mass_in_gold", "abs_mass"),
    ("pos_mass_in_gold", "pos_mass"),
    ("ap_abs", "ap_abs"),
    ("ap_signed", "ap_signed"),
    ("precision_at_k", "prec_at_k"),
    ("abs_minus_coverage_baseline", "abs_minus_coverage"),
]


def load_alignment() -> List[dict]:
    rows = []
    with M2C_ALIGN.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in (
                "prob_pos",
                "n_chars",
                "n_spans",
                "gold_char_coverage",
                "abs_mass_in_gold",
                "pos_mass_in_gold",
                "precision_at_k",
                "recall_at_k",
                "ap_abs",
                "ap_signed",
                "abs_minus_random_span",
                "pos_minus_random_span",
                "prec_minus_random_words",
                "abs_minus_positional",
                "abs_minus_coverage_baseline",
                "baseline_abs_mass_mean",
            ):
                if k in r and r[k] not in ("", None):
                    try:
                        r[k] = float(r[k])
                    except ValueError:
                        pass
            r["ap_eligible"] = int(r.get("ap_eligible") in (1, "1", True, "True"))
            r["n_spans"] = int(float(r["n_spans"])) if r.get("n_spans") not in ("", None) else 0
            r["n_chars"] = int(float(r["n_chars"])) if r.get("n_chars") not in ("", None) else 0
            rows.append(r)
    return rows


def load_faithfulness_apos(budget: int = 2) -> Dict[Tuple[str, str], float]:
    """Map (canonical_id, model) -> A_pos delta_prob (signed; more negative = stronger)."""
    out = {}
    if not M2B_RESULTS.exists():
        return out
    with M2B_RESULTS.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["condition"] != "A_pos" or int(r["budget"]) != budget:
                continue
            # medium has one row per sentence×model for A_pos (no random_rep)
            key = (r["canonical_id"], r["model"])
            out[key] = float(r["delta_prob"])
    return out


def _metric_vals(rows: Sequence[dict], field: str) -> List[float]:
    vals = []
    for r in rows:
        if field in ("ap_abs", "ap_signed") and not r.get("ap_eligible"):
            continue
        v = r.get(field)
        if v is None or v != v:
            continue
        vals.append(float(v))
    return vals


def _row(
    section: str,
    model: str,
    stratum: str,
    metric: str,
    vals: Sequence[float],
    clusters: Optional[Sequence[str]] = None,
    extra: Optional[dict] = None,
) -> dict:
    mean, lo, hi = bootstrap_mean_ci(vals)
    d = {
        "section": section,
        "model": model,
        "stratum": stratum,
        "metric": metric,
        "n": len(vals),
        "mean": mean,
        "ci95_lo": lo,
        "ci95_hi": hi,
    }
    if clusters is not None and len(clusters) == len(vals):
        cm, clo, chi = cluster_bootstrap_mean_ci(vals, clusters)
        d["cluster_mean"] = cm
        d["cluster_ci95_lo"] = clo
        d["cluster_ci95_hi"] = chi
        d["n_clusters"] = len(set(clusters))
    if extra:
        d.update(extra)
    return d


def stratify_outcome(rows: List[dict]) -> List[dict]:
    """TP / FN on gold-positive; FP / TN on non-biased (mass metrics only for reference)."""
    out = []
    models = sorted({r["model"] for r in rows})
    for model in models:
        for outcome in ("TP", "FN", "FP", "TN"):
            for cat in ("lex_only", "inf_only", "both", "ALL_POSITIVE", "non_biased"):
                if cat == "ALL_POSITIVE":
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["pred_type"] == outcome
                        and r["ann_category"] != "non_biased"
                    ]
                elif cat == "non_biased":
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["pred_type"] == outcome
                        and r["ann_category"] == "non_biased"
                    ]
                else:
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["pred_type"] == outcome
                        and r["ann_category"] == cat
                    ]
                if len(sub) < 15:
                    continue
                # For non-biased / FP/TN: abs_mass is ~0 by construction; still report excess if any
                fields = METRICS if cat != "non_biased" else [
                    ("abs_mass_in_gold", "abs_mass"),
                    ("pos_mass_in_gold", "pos_mass"),
                ]
                for field, name in fields:
                    vals = _metric_vals(sub, field)
                    if len(vals) < 15:
                        continue
                    clusters = [r["triplet_uuid"] for r in sub if _include_for_metric(r, field)]
                    # align clusters length to vals
                    clusters = []
                    for r in sub:
                        if field in ("ap_abs", "ap_signed") and not r.get("ap_eligible"):
                            continue
                        v = r.get(field)
                        if v is None or v != v:
                            continue
                        clusters.append(r["triplet_uuid"])
                    out.append(
                        _row(
                            "by_outcome",
                            model,
                            f"{cat}|{outcome}",
                            name,
                            vals,
                            clusters,
                        )
                    )
    return out


def _include_for_metric(r: dict, field: str) -> bool:
    if field in ("ap_abs", "ap_signed") and not r.get("ap_eligible"):
        return False
    v = r.get(field)
    return v is not None and v == v


def probability_bands(rows: List[dict]) -> List[dict]:
    """Alignment by predicted P(biased) bands on gold-positive sentences."""
    out = []
    bands = [(0.0, 0.25, "p00_25"), (0.25, 0.5, "p25_50"), (0.5, 0.75, "p50_75"), (0.75, 1.01, "p75_100")]
    models = sorted({r["model"] for r in rows})
    for model in models:
        for cat in ("lex_only", "inf_only", "ALL_POSITIVE"):
            for lo_b, hi_b, label in bands:
                if cat == "ALL_POSITIVE":
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] != "non_biased"
                        and lo_b <= float(r["prob_pos"]) < hi_b
                    ]
                else:
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] == cat
                        and lo_b <= float(r["prob_pos"]) < hi_b
                    ]
                if len(sub) < 15:
                    continue
                for field, name in (
                    ("abs_minus_random_span", "abs_minus_rand"),
                    ("pos_minus_random_span", "pos_minus_rand"),
                    ("ap_abs", "ap_abs"),
                ):
                    vals = _metric_vals(sub, field)
                    if len(vals) < 15:
                        continue
                    out.append(_row("prob_band", model, f"{cat}|{label}", name, vals))
    return out


def coverage_matched_lex_vs_inf(rows: List[dict]) -> List[dict]:
    """Does lex>inf persist when gold coverage is matched within ±5pp?"""
    out = []
    models = sorted({r["model"] for r in rows})
    for model in models:
        lex = [r for r in rows if r["model"] == model and r["ann_category"] == "lex_only"]
        inf = [r for r in rows if r["model"] == model and r["ann_category"] == "inf_only"]
        pairs = coverage_matched_pairs(lex, inf, tol=0.05, seed=7)
        if len(pairs) < 15:
            # try looser tolerance
            pairs = coverage_matched_pairs(lex, inf, tol=0.10, seed=7)
            tol_used = 0.10
        else:
            tol_used = 0.05
        if len(pairs) < 10:
            out.append(
                {
                    "section": "coverage_matched",
                    "model": model,
                    "stratum": "lex_minus_inf",
                    "metric": "abs_minus_rand",
                    "n": len(pairs),
                    "mean": float("nan"),
                    "ci95_lo": float("nan"),
                    "ci95_hi": float("nan"),
                    "tol": tol_used,
                    "note": "insufficient_matches",
                }
            )
            continue
        for field, name in (
            ("abs_minus_random_span", "abs_minus_rand"),
            ("pos_minus_random_span", "pos_minus_rand"),
            ("ap_abs", "ap_abs"),
            ("abs_mass_in_gold", "abs_mass"),
        ):
            diffs = []
            for lr, ir in pairs:
                if field in ("ap_abs", "ap_signed"):
                    if not (lr.get("ap_eligible") and ir.get("ap_eligible")):
                        continue
                va, vb = lr.get(field), ir.get(field)
                if va != va or vb != vb:
                    continue
                diffs.append(float(va) - float(vb))
            mean, lo, hi = paired_bootstrap_mean_ci(diffs)
            cov_lex = np.mean([float(p[0]["gold_char_coverage"]) for p in pairs])
            cov_inf = np.mean([float(p[1]["gold_char_coverage"]) for p in pairs])
            out.append(
                {
                    "section": "coverage_matched",
                    "model": model,
                    "stratum": "lex_minus_inf",
                    "metric": name,
                    "n": len(diffs),
                    "mean": mean,
                    "ci95_lo": lo,
                    "ci95_hi": hi,
                    "tol": tol_used,
                    "mean_cov_lex": cov_lex,
                    "mean_cov_inf": cov_inf,
                    "n_pairs": len(pairs),
                }
            )
    return out


def regression_controls(rows: List[dict]) -> List[dict]:
    """OLS: excess alignment ~ lex indicator + coverage + length + n_spans + prob.

    Interprets whether lex vs inf gap remains after linear controls.
    """
    out = []
    models = sorted({r["model"] for r in rows})
    for model in models:
        sub = [
            r
            for r in rows
            if r["model"] == model and r["ann_category"] in ("lex_only", "inf_only")
        ]
        if len(sub) < 40:
            continue
        y = np.array([float(r["abs_minus_random_span"]) for r in sub], dtype=float)
        is_lex = np.array([1.0 if r["ann_category"] == "lex_only" else 0.0 for r in sub])
        cov = np.array([float(r["gold_char_coverage"]) for r in sub])
        length = np.array([float(r["n_chars"]) for r in sub]) / 100.0  # scale
        nsp = np.array([float(r["n_spans"]) for r in sub])
        prob = np.array([float(r["prob_pos"]) for r in sub])
        X = np.column_stack([np.ones(len(sub)), is_lex, cov, length, nsp, prob])
        coefs = ols_coef_ci(y, X, n_boot=1500, seed=7)
        names = ["intercept", "is_lex", "coverage", "length_per100", "n_spans", "prob_pos"]
        for j, name in enumerate(names):
            mean, lo, hi = coefs[f"b{j}"]
            out.append(
                {
                    "section": "regression",
                    "model": model,
                    "stratum": "lex_inf_pooled",
                    "metric": f"coef_{name}",
                    "n": len(sub),
                    "mean": mean,
                    "ci95_lo": lo,
                    "ci95_hi": hi,
                    "outcome": "abs_minus_rand",
                }
            )
        # also without coverage (to show attenuation)
        X2 = np.column_stack([np.ones(len(sub)), is_lex, length, nsp, prob])
        coefs2 = ols_coef_ci(y, X2, n_boot=1500, seed=7)
        mean, lo, hi = coefs2["b1"]
        out.append(
            {
                "section": "regression",
                "model": model,
                "stratum": "lex_inf_no_coverage_control",
                "metric": "coef_is_lex",
                "n": len(sub),
                "mean": mean,
                "ci95_lo": lo,
                "ci95_hi": hi,
                "outcome": "abs_minus_rand",
            }
        )
    return out


def multi_annotation_sensitivity(rows: List[dict]) -> List[dict]:
    """Compare single-span vs multi-span sentences; cluster bootstrap by triplet."""
    out = []
    models = sorted({r["model"] for r in rows})
    for model in models:
        for cat in ("lex_only", "inf_only", "ALL_POSITIVE"):
            for multi_flag, label in ((False, "single_span"), (True, "multi_span")):
                if cat == "ALL_POSITIVE":
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] != "non_biased"
                        and ((r["n_spans"] > 1) if multi_flag else (r["n_spans"] == 1))
                    ]
                else:
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] == cat
                        and ((r["n_spans"] > 1) if multi_flag else (r["n_spans"] == 1))
                    ]
                if len(sub) < 15:
                    continue
                vals = _metric_vals(sub, "abs_minus_random_span")
                clusters = []
                for r in sub:
                    v = r.get("abs_minus_random_span")
                    if v is not None and v == v:
                        clusters.append(r["triplet_uuid"])
                out.append(
                    _row(
                        "multi_annotation",
                        model,
                        f"{cat}|{label}",
                        "abs_minus_rand",
                        vals,
                        clusters,
                    )
                )
    return out


def paired_model_comparison(rows: List[dict]) -> List[dict]:
    out = []
    by = defaultdict(dict)
    for r in rows:
        if r["ann_category"] == "non_biased":
            continue
        by[r["model"]][r["canonical_id"]] = r

    pairs = [
        ("biasdetector", "daroberta"),
        ("biasdetector", "deberta"),
        ("daroberta", "deberta"),
    ]
    for a, b in pairs:
        common = sorted(set(by[a]) & set(by[b]))
        for cat in ("ALL_POSITIVE", "lex_only", "inf_only"):
            ids = common
            if cat != "ALL_POSITIVE":
                ids = [cid for cid in common if by[a][cid]["ann_category"] == cat]
            for field, name in (
                ("abs_minus_random_span", "abs_minus_rand"),
                ("pos_minus_random_span", "pos_minus_rand"),
                ("ap_abs", "ap_abs"),
                ("precision_at_k", "prec_at_k"),
            ):
                diffs = []
                for cid in ids:
                    ra, rb = by[a][cid], by[b][cid]
                    if field in ("ap_abs", "ap_signed"):
                        if not (ra.get("ap_eligible") and rb.get("ap_eligible")):
                            continue
                    va, vb = ra.get(field), rb.get(field)
                    if va != va or vb != vb:
                        continue
                    diffs.append(float(va) - float(vb))
                if len(diffs) < 10:
                    continue
                mean, lo, hi = paired_bootstrap_mean_ci(diffs)
                out.append(
                    {
                        "section": "paired_model",
                        "model": f"{a}_minus_{b}",
                        "stratum": cat,
                        "metric": name,
                        "n": len(diffs),
                        "mean": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                        "n_shared_ids": len(ids),
                    }
                )
    return out


def lex_vs_inf_unmatched(rows: List[dict]) -> List[dict]:
    """Baseline unmatched lex vs inf means (for reference next to matched)."""
    out = []
    models = sorted({r["model"] for r in rows})
    for model in models:
        for cat in ("lex_only", "inf_only"):
            sub = [r for r in rows if r["model"] == model and r["ann_category"] == cat]
            for field, name in (
                ("abs_minus_random_span", "abs_minus_rand"),
                ("pos_minus_random_span", "pos_minus_rand"),
                ("ap_abs", "ap_abs"),
                ("gold_char_coverage", "coverage"),
            ):
                vals = _metric_vals(sub, field) if field != "gold_char_coverage" else [
                    float(r["gold_char_coverage"]) for r in sub
                ]
                out.append(_row("unmatched_ref", model, cat, name, vals))
        # unpaired difference of means is not causal; report paired-style only via matched
        lex_v = _metric_vals(
            [r for r in rows if r["model"] == model and r["ann_category"] == "lex_only"],
            "abs_minus_random_span",
        )
        inf_v = _metric_vals(
            [r for r in rows if r["model"] == model and r["ann_category"] == "inf_only"],
            "abs_minus_random_span",
        )
        # Welch-style bootstrap of mean difference (independent samples)
        if len(lex_v) >= 15 and len(inf_v) >= 15:
            rng = np.random.default_rng(7)
            diffs = []
            for _ in range(2000):
                diffs.append(
                    float(rng.choice(lex_v, len(lex_v), replace=True).mean())
                    - float(rng.choice(inf_v, len(inf_v), replace=True).mean())
                )
            diffs.sort()
            out.append(
                {
                    "section": "unmatched_ref",
                    "model": model,
                    "stratum": "lex_minus_inf_indep",
                    "metric": "abs_minus_rand",
                    "n": min(len(lex_v), len(inf_v)),
                    "mean": float(np.mean(lex_v) - np.mean(inf_v)),
                    "ci95_lo": diffs[int(0.025 * 2000)],
                    "ci95_hi": diffs[int(0.975 * 2000)],
                    "n_lex": len(lex_v),
                    "n_inf": len(inf_v),
                }
            )
    return out


def faithfulness_join_summary(rows: List[dict], faith: Dict[Tuple[str, str], float]) -> List[dict]:
    """On M2B∩M2C sentences: correlation of |A_pos ΔP| with alignment excess."""
    out = []
    joined = []
    for r in rows:
        if r["ann_category"] == "non_biased":
            continue
        key = (r["canonical_id"], r["model"])
        if key not in faith:
            continue
        joined.append({**r, "a_pos_delta": faith[key], "a_pos_abs": abs(faith[key])})
    models = sorted({r["model"] for r in joined})
    for model in models:
        sub = [r for r in joined if r["model"] == model]
        if len(sub) < 15:
            continue
        # tertiles of faithfulness strength
        abs_d = sorted(r["a_pos_abs"] for r in sub)
        t1, t2 = abs_d[len(abs_d) // 3], abs_d[(2 * len(abs_d)) // 3]
        for label, pred in (
            ("faith_low", lambda x: x["a_pos_abs"] <= t1),
            ("faith_mid", lambda x: t1 < x["a_pos_abs"] <= t2),
            ("faith_high", lambda x: x["a_pos_abs"] > t2),
        ):
            s = [r for r in sub if pred(r)]
            vals = _metric_vals(s, "abs_minus_random_span")
            out.append(_row("faith_join", model, label, "abs_minus_rand", vals, extra={"n_join": len(sub)}))
        # Spearman-like via rank correlation (Pearson on ranks)
        if len(sub) >= 20:
            x = np.array([r["a_pos_abs"] for r in sub])
            y = np.array([float(r["abs_minus_random_span"]) for r in sub])
            rx = np.argsort(np.argsort(x)).astype(float)
            ry = np.argsort(np.argsort(y)).astype(float)
            corr = float(np.corrcoef(rx, ry)[0, 1])
            out.append(
                {
                    "section": "faith_join",
                    "model": model,
                    "stratum": "ALL_POSITIVE",
                    "metric": "spearman_faith_abs_vs_align",
                    "n": len(sub),
                    "mean": corr,
                    "ci95_lo": "",
                    "ci95_hi": "",
                }
            )
        for cat in ("lex_only", "inf_only"):
            s = [r for r in sub if r["ann_category"] == cat]
            if len(s) < 10:
                continue
            vals = _metric_vals(s, "abs_minus_random_span")
            out.append(_row("faith_join", model, f"{cat}|m2b_overlap", "abs_minus_rand", vals))
    return out


def run_robustness() -> List[dict]:
    rows = load_alignment()
    faith = load_faithfulness_apos()
    summary: List[dict] = []
    summary.extend(stratify_outcome(rows))
    summary.extend(probability_bands(rows))
    summary.extend(coverage_matched_lex_vs_inf(rows))
    summary.extend(regression_controls(rows))
    summary.extend(multi_annotation_sensitivity(rows))
    summary.extend(paired_model_comparison(rows))
    summary.extend(lex_vs_inf_unmatched(rows))
    summary.extend(faithfulness_join_summary(rows, faith))
    return summary


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
