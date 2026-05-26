#!/usr/bin/env python3
"""Mann-Whitney U tests on per-instance mean |SHAP| distributions.

Six comparisons matching the Section 4.2 plots:
  TP vs FP within each (corpus, model) cell (4 tests)
  TN: BD vs DR within each corpus              (2 tests)

For each test, prints U, two-sided p, and rank-biserial r = 1 − 2U/(n1·n2).

Sources:
  BABE:  outputs/shap_samples.jsonl,  outputs/shap_samples_daroberta.jsonl
         (per-instance mean |SHAP| computed on the fly from word_attribs)
  BASIL: outputs/basil_shap/basil_shap_magnitude.csv
         (uses the cached `mean_abs_shap` column directly)

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/shap_mannwhitney.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


ROOT = Path(__file__).resolve().parent.parent
BABE_BD = ROOT / "outputs" / "shap_samples.jsonl"
BABE_DR = ROOT / "outputs" / "shap_samples_daroberta.jsonl"
BASIL_MAG = ROOT / "outputs" / "basil_shap" / "basil_shap_magnitude.csv"


def pred_category(gold, pred):
    if gold == 1 and pred == 1: return "TP"
    if gold == 0 and pred == 1: return "FP"
    if gold == 0 and pred == 0: return "TN"
    return "FN"


def load_babe(jsonl_path):
    """{category: np.ndarray of per-instance mean |SHAP|}"""
    out = {"TP": [], "FP": [], "TN": [], "FN": []}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            wa = r.get("word_attribs", [])
            if not wa:
                continue
            cat = pred_category(int(r["gold"]), int(r["pred"]))
            out[cat].append(float(np.mean([abs(x["shap"]) for x in wa])))
    return {k: np.asarray(v, dtype=float) for k, v in out.items()}


def load_basil(csv_path):
    """{(model, category): np.ndarray of mean_abs_shap}"""
    df = pd.read_csv(csv_path)
    out = {}
    for (model, cat), g in df.groupby(["model", "category"]):
        out[(model, cat)] = g["mean_abs_shap"].to_numpy(dtype=float)
    return out


def mwu(a, b):
    """Returns (U1, p_two_sided, rank_biserial r)."""
    res = mannwhitneyu(a, b, alternative="two-sided")
    U = float(res.statistic)
    p = float(res.pvalue)
    n1, n2 = len(a), len(b)
    r = 1.0 - 2.0 * U / (n1 * n2)
    return U, p, r, n1, n2


def fmt_p(p):
    """Compact LaTeX-friendly p-value formatting."""
    if p < 1e-4:
        return f"<10^{{-4}}"
    if p < 1e-3:
        return f"{p:.1e}".replace("e-0", r"\!\times\!10^{-").replace("e-", r"\!\times\!10^{-") + "}"
    return f"{p:.3f}"


def main():
    babe_bd = load_babe(BABE_BD)
    babe_dr = load_babe(BABE_DR)
    basil = load_basil(BASIL_MAG)

    comparisons = [
        ("BD BABE: TP vs FP",   babe_bd["TP"], babe_bd["FP"]),
        ("BD BASIL: TP vs FP",  basil[("biasdetector", "TP")], basil[("biasdetector", "FP")]),
        ("DR BABE: TP vs FP",   babe_dr["TP"], babe_dr["FP"]),
        ("DR BASIL: TP vs FP",  basil[("daroberta",    "TP")], basil[("daroberta",    "FP")]),
        ("BABE TN: BD vs DR",   babe_bd["TN"], babe_dr["TN"]),
        ("BASIL TN: BD vs DR",  basil[("biasdetector", "TN")], basil[("daroberta",    "TN")]),
    ]

    rows = []
    for label, a, b in comparisons:
        U, p, r, n1, n2 = mwu(a, b)
        rows.append({"comparison": label, "n1": n1, "n2": n2,
                     "U": U, "p": p, "r": r})

    # --- Plain readable table ---
    print("Mann-Whitney U (two-sided) on per-instance mean |SHAP|\n")
    print(f"{'Comparison':<24} {'n1':>4} {'n2':>4} {'U':>10} "
          f"{'p (two-sided)':>14} {'r (rb)':>8}")
    print("-" * 70)
    for r in rows:
        p_str = (f"{r['p']:.3e}" if r['p'] < 1e-3 else f"{r['p']:.4f}")
        print(f"{r['comparison']:<24} {r['n1']:>4} {r['n2']:>4} "
              f"{r['U']:>10.1f} {p_str:>14} {r['r']:>+8.3f}")
    print()

    # --- LaTeX booktabs table ---
    print("% --- LaTeX paste-in ---")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\small")
    print(r"\setlength{\tabcolsep}{5pt}")
    print(r"\begin{tabular}{lcccc}")
    print(r"\toprule")
    print(r"Comparison & $n_1, n_2$ & $U$ & $p$ & $r$ \\")
    print(r"\midrule")
    for r in rows:
        if r["p"] < 1e-4:
            p_tex = r"$<\!10^{-4}$"
        elif r["p"] < 1e-3:
            mant, exp = f"{r['p']:.1e}".split("e")
            p_tex = f"${mant}\\!\\times\\!10^{{{int(exp)}}}$"
        else:
            p_tex = f"${r['p']:.3f}$"
        comp_tex = r["comparison"].replace(" vs ", r" vs.\ ")
        print(f"{comp_tex} & ${r['n1']},{r['n2']}$ & "
              f"${r['U']:.1f}$ & {p_tex} & ${r['r']:+.3f}$ \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\caption{Mann--Whitney $U$ tests (two-sided) on per-instance "
          r"mean $|$SHAP$|$. Effect size $r$ is the rank-biserial "
          r"correlation, $r = 1 - 2U / (n_1 n_2)$; positive $r$ indicates "
          r"the first group ranks higher.}")
    print(r"\label{tab:shap_mwu}")
    print(r"\end{table}")


if __name__ == "__main__":
    main()
