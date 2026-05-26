#!/usr/bin/env python3
"""BABE three-way FP partition — port of BASIL §7 onto BABE.

Splits BABE false positives into shared / bd_only / dr_only by sentence text,
runs threshold-based feature selection (global p75 across all 4 cells) on
each (partition, model) cell, and writes category proportions to
outputs/babe_fp_partition.csv.

Mirrors the methodology in basil_shap_analyze.py:build_fp_partition_csv.
No randomness; deterministic.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/babe_fp_partition.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# scripts/ is a sub-directory; add the project root so babe_fig6_confound
# (a module at the project root) can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from babe_fig6_confound import aggregate_words, categorize_word, CATEGORIES


ROOT = Path(__file__).resolve().parent.parent
BD_JSONL = ROOT / "outputs" / "shap_samples.jsonl"
DR_JSONL = ROOT / "outputs" / "shap_samples_daroberta.jsonl"
OUT_CSV  = ROOT / "outputs" / "babe_fp_partition.csv"

PCT_COLS = {
    "Emotional/Evaluative":     "pct_emotional_evaluative",
    "Explicit Bias Terms":      "pct_explicit_bias",
    "Framing/Reporting Verbs":  "pct_framing_reporting",
    "Function/Temporal Words":  "pct_function_temporal",
}


def load_fp_records(path):
    """Read JSONL, keep records with gold=0 & pred=1."""
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["gold"] == 0 and r["pred"] == 1:
                out.append(r)
    return out


def partition_by_text(bd_fps, dr_fps):
    """Three-way set partition keyed on the 'text' field."""
    bd_by_text = {r["text"]: r for r in bd_fps}
    dr_by_text = {r["text"]: r for r in dr_fps}
    bd_texts = set(bd_by_text)
    dr_texts = set(dr_by_text)

    shared_texts  = bd_texts & dr_texts
    bd_only_texts = bd_texts - dr_texts
    dr_only_texts = dr_texts - bd_texts

    return {
        ("shared",  "biasdetector"): [bd_by_text[t] for t in shared_texts],
        ("shared",  "daroberta"):    [dr_by_text[t] for t in shared_texts],
        ("bd_only", "biasdetector"): [bd_by_text[t] for t in bd_only_texts],
        ("dr_only", "daroberta"):    [dr_by_text[t] for t in dr_only_texts],
    }


def main():
    print("=== BABE three-way FP partition ===\n")

    bd_fps = load_fp_records(BD_JSONL)
    dr_fps = load_fp_records(DR_JSONL)
    print(f"Loaded {len(bd_fps)} BD FPs, {len(dr_fps)} DR FPs")

    cells = partition_by_text(bd_fps, dr_fps)
    print("\nPremise counts:")
    print(f"  shared (BD ∩ DR by text): {len(cells[('shared',  'biasdetector')])}")
    print(f"  bd_only:                  {len(cells[('bd_only', 'biasdetector')])}")
    print(f"  dr_only:                  {len(cells[('dr_only', 'daroberta')])}")

    for (partition, model), recs in cells.items():
        n = len(recs)
        if n < 5:
            print(f"  [HARD WARN] {partition} × {model}: n_sentences={n} (<5)")
        elif n < 10:
            print(f"  [soft warn] {partition} × {model}: n_sentences={n} (<10)")

    # Per-cell word aggregation.
    word_dfs = {key: aggregate_words(recs) for key, recs in cells.items()}

    # Global p75 across all 4 cells' words (matches BASIL §7).
    pooled = np.concatenate([
        wdf["mean_abs_shap"].to_numpy() for wdf in word_dfs.values() if len(wdf) > 0
    ])
    threshold_p75 = float(np.percentile(pooled, 75)) if len(pooled) else 0.0
    print(f"\nThreshold pool size: {len(pooled)} unique words across 4 cells")
    print(f"Global p75 threshold: {threshold_p75:.6f}")
    print(f"  (BABE §2 reference threshold from fig6_matched_pools.csv: 0.040638 — "
          f"different because cell composition differs)")

    rows = []
    for (partition, model), wdf in word_dfs.items():
        n_sentences = len(cells[(partition, model)])
        sel = wdf[wdf["mean_abs_shap"] >= threshold_p75].copy()
        n_selected = len(sel)
        sel["category"] = sel["word"].apply(categorize_word)

        cat_props = {}
        for cat in CATEGORIES:
            n_cat = int((sel["category"] == cat).sum())
            cat_props[cat] = (n_cat / n_selected * 100.0) if n_selected else 0.0

        row = {
            "partition": partition,
            "model": model,
            "n_sentences": n_sentences,
            "n_selected_words": n_selected,
            "threshold_p75": round(threshold_p75, 6),
        }
        for cat, col in PCT_COLS.items():
            row[col] = round(cat_props[cat], 2)
        rows.append(row)

    df = pd.DataFrame(rows, columns=[
        "partition", "model", "n_sentences", "n_selected_words", "threshold_p75",
        *PCT_COLS.values(),
    ])

    # Sums-to-100 sanity.
    print("\nSums-to-100 check:")
    for _, r in df.iterrows():
        s = sum(r[c] for c in PCT_COLS.values())
        flag = " ✓" if abs(s - 100.0) < 0.5 or r["n_selected_words"] == 0 else "  [WARN]"
        print(f"  {r['partition']:<8} {r['model']:<14} "
              f"n_selected={int(r['n_selected_words']):>3}  sum={s:6.2f}{flag}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f"\nWrote {OUT_CSV}\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
