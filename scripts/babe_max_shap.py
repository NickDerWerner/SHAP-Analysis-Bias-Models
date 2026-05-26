#!/usr/bin/env python3
"""Per-instance MAX |SHAP| on BABE — counterpart to BASIL §2b.

Computes per-instance max |SHAP| (and re-reports per-instance mean
|SHAP| for direct comparison) over the cached BABE SHAP samples for
both models, grouped by prediction category (TP/FP/TN/FN).

Stdout format matches the BASIL §2b/§2 tables in
`outputs/basil_shap/basil_shap_summary.md` so the two corpora can be
slotted into a cross-corpus appendix table without reformatting.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/babe_max_shap.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SAMPLES = [
    ("biasdetector", "bias-detector", ROOT / "outputs" / "shap_samples.jsonl"),
    ("daroberta",    "DA-RoBERTa",    ROOT / "outputs" / "shap_samples_daroberta.jsonl"),
]
TYPE_ORDER = ["TP", "FP", "TN", "FN"]


def pred_category(gold, pred):
    if gold == 1 and pred == 1: return "TP"
    if gold == 0 and pred == 1: return "FP"
    if gold == 0 and pred == 0: return "TN"
    return "FN"


def load_rows(jsonl_path, suffix, display):
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            wa = r.get("word_attribs", [])
            if not wa:
                continue
            abs_shap = [abs(x["shap"]) for x in wa]
            rows.append({
                "model": suffix,
                "display": display,
                "category": pred_category(int(r["gold"]), int(r["pred"])),
                "mean_abs_shap": float(np.mean(abs_shap)),
                "max_abs_shap":  float(np.max(abs_shap)),
            })
    return rows


def main():
    rows = []
    for suffix, display, path in SAMPLES:
        rows.extend(load_rows(path, suffix, display))
    df = pd.DataFrame(rows)

    # --- BASIL §2b-style: per-instance MAX |SHAP| ---
    print("## 2b. Max |SHAP| by prediction type (BABE counterpart)\n")
    print("Per-instance max |SHAP| from the BABE SHAP caches "
          "(`shap_samples.jsonl`, `shap_samples_daroberta.jsonl`). "
          "Includes the FN partition added by `babe_shap_fn.py`.\n")
    print("| model | category | n | median | mean |")
    print("|---|---|---|---|---|")
    max_summary = {}
    for suffix, display, _ in SAMPLES:
        for pt in TYPE_ORDER:
            sub = df[(df.model == suffix) & (df.category == pt)]
            n = len(sub)
            med = float(sub["max_abs_shap"].median()) if n else float("nan")
            mean = float(sub["max_abs_shap"].mean()) if n else float("nan")
            print(f"| {display} | {pt} | {n} | {med:.4f} | {mean:.4f} |")
            max_summary[(suffix, pt)] = (n, med, mean)
    print()

    # --- BASIL §2-style: per-instance MEAN |SHAP| ---
    print("## 2. Mean |SHAP| by prediction type (BABE — re-reported for comparison)\n")
    print("| model | category | n | median | mean |")
    print("|---|---|---|---|---|")
    mean_summary = {}
    for suffix, display, _ in SAMPLES:
        for pt in TYPE_ORDER:
            sub = df[(df.model == suffix) & (df.category == pt)]
            n = len(sub)
            med = float(sub["mean_abs_shap"].median()) if n else float("nan")
            mean = float(sub["mean_abs_shap"].mean()) if n else float("nan")
            print(f"| {display} | {pt} | {n} | {med:.4f} | {mean:.4f} |")
            mean_summary[(suffix, pt)] = (n, med, mean)
    print()

    # --- FP/TP ratio of medians, max vs mean ---
    print("## FP/TP ratio of medians — max vs mean (per model)\n")
    print("If a model's FP attribution is broadly 'spread thin' (many "
          "moderate-strength words rather than one big spike), the "
          "FP/TP ratio shrinks more under MAX than under MEAN. A "
          "MAX ratio ≪ MEAN ratio supports the 'same mechanism, "
          "different calibration' reading.\n")
    print("| model | mean FP/TP | max FP/TP | max−mean |")
    print("|---|---|---|---|")
    for suffix, display, _ in SAMPLES:
        _, mean_tp_med, _ = mean_summary[(suffix, "TP")]
        _, mean_fp_med, _ = mean_summary[(suffix, "FP")]
        _, max_tp_med,  _ = max_summary[(suffix, "TP")]
        _, max_fp_med,  _ = max_summary[(suffix, "FP")]
        mean_ratio = mean_fp_med / mean_tp_med if mean_tp_med else float("nan")
        max_ratio  = max_fp_med  / max_tp_med  if max_tp_med  else float("nan")
        diff = max_ratio - mean_ratio
        print(f"| {display} | {mean_ratio:.3f} | {max_ratio:.3f} | {diff:+.3f} |")
    print()

    # Cross-corpus crib (BASIL numbers hard-coded from basil_shap_summary.md)
    print("## Cross-corpus crib (BASIL values for side-by-side comparison)\n")
    basil_mean = {  # (median per BASIL §2)
        ("biasdetector", "TP"): 0.0407, ("biasdetector", "FP"): 0.0553,
        ("daroberta",    "TP"): 0.0343, ("daroberta",    "FP"): 0.0432,
    }
    basil_max = {   # (median per BASIL §2b)
        ("biasdetector", "TP"): 0.2203, ("biasdetector", "FP"): 0.2418,
        ("daroberta",    "TP"): 0.1938, ("daroberta",    "FP"): 0.2306,
    }
    print("| corpus | model | mean FP/TP | max FP/TP |")
    print("|---|---|---|---|")
    for suffix, display, _ in SAMPLES:
        b_mean_ratio = basil_mean[(suffix, "FP")] / basil_mean[(suffix, "TP")]
        b_max_ratio  = basil_max[(suffix,  "FP")] / basil_max[(suffix,  "TP")]
        print(f"| BASIL | {display} | {b_mean_ratio:.3f} | {b_max_ratio:.3f} |")
    for suffix, display, _ in SAMPLES:
        _, mean_tp_med, _ = mean_summary[(suffix, "TP")]
        _, mean_fp_med, _ = mean_summary[(suffix, "FP")]
        _, max_tp_med,  _ = max_summary[(suffix, "TP")]
        _, max_fp_med,  _ = max_summary[(suffix, "FP")]
        print(f"| BABE  | {display} | {mean_fp_med/mean_tp_med:.3f} "
              f"| {max_fp_med/max_tp_med:.3f} |")


if __name__ == "__main__":
    main()
