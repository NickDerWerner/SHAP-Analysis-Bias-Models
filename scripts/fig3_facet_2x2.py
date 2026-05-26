#!/usr/bin/env python3
"""2x2 facet boxplot of per-instance mean |SHAP| (rows = model, cols = corpus).

Layout:
    +----------------------------+----------------------------+
    | bias-detector — BABE       | bias-detector — BASIL      |
    +----------------------------+----------------------------+
    | DA-RoBERTa-BABE-FT — BABE  | DA-RoBERTa-BABE-FT — BASIL |
    +----------------------------+----------------------------+

Each panel: four boxes in fixed order (TP, FP, TN, FN) colored by category.

Data sources:
  BABE  — outputs/shap_samples.jsonl, outputs/shap_samples_daroberta.jsonl
  BASIL — outputs/basil_shap/basil_shap_magnitude.csv

Numbers underlying this figure are documented in
outputs/findings_summary.md sections 3 and 5.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/fig3_facet_2x2.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
OUT_PNG = ROOT / "outputs" / "fig3_facet_2x2.png"
OUT_PDF = ROOT / "outputs" / "fig3_facet_2x2.pdf"

BABE_SAMPLES = {
    "biasdetector": ROOT / "outputs" / "shap_samples.jsonl",
    "daroberta":    ROOT / "outputs" / "shap_samples_daroberta.jsonl",
}
BASIL_MAGNITUDE = ROOT / "outputs" / "basil_shap" / "basil_shap_magnitude.csv"

MODELS = [
    ("biasdetector", "bias-detector"),
    ("daroberta",    "DA-RoBERTa-BABE-FT"),
]
CORPORA = ["BABE", "BASIL"]
CATEGORIES = ["TP", "FP", "TN", "FN"]

COLORS = {"TP": "#2ca02c", "FP": "#d62728", "TN": "#1f77b4", "FN": "#ff7f0e"}
Y_MAX = 0.15


def pred_category(gold, pred):
    if gold == 1 and pred == 1: return "TP"
    if gold == 0 and pred == 1: return "FP"
    if gold == 0 and pred == 0: return "TN"
    return "FN"


def load_babe_means(jsonl_path):
    """dict[category] -> np.array of per-sentence mean_abs_shap."""
    out = {c: [] for c in CATEGORIES}
    if not jsonl_path.exists():
        print(f"[WARN] {jsonl_path} missing")
        return {c: np.array([]) for c in CATEGORIES}
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
    return {c: np.array(v) for c, v in out.items()}


def load_basil_means(model_suffix):
    """dict[category] -> np.array, from the magnitude CSV (already 100/category)."""
    df = pd.read_csv(BASIL_MAGNITUDE)
    sub = df[df.model == model_suffix]
    out = {}
    for c in CATEGORIES:
        out[c] = sub[sub.category == c]["mean_abs_shap"].to_numpy()
    return out


def draw_panel(ax, data_by_cat, title, show_ylabel):
    data = [data_by_cat[c] for c in CATEGORIES]
    bp = ax.boxplot(
        data, positions=range(len(CATEGORIES)), widths=0.6, patch_artist=True,
        tick_labels=CATEGORIES,
        showmeans=True, meanline=True,
        meanprops=dict(linestyle="--", linewidth=1.5, color="black"),
        medianprops=dict(linestyle="-", linewidth=1.5, color="#ff7f0e"),
        flierprops=dict(marker="o", markerfacecolor="none",
                        markeredgecolor="black", markersize=3, linewidth=0.6),
    )
    for patch, cat in zip(bp["boxes"], CATEGORIES):
        patch.set_facecolor(COLORS[cat])
        patch.set_alpha(0.7)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.0)

    # n=X annotation beneath each tick label, bolded only when n < 100
    # so the BABE FP small-sample boxes (n=37 BD, n=12 DR) jump out.
    for i, cat in enumerate(CATEGORIES):
        n = len(data_by_cat[cat])
        weight = "bold" if n < 100 else "normal"
        ax.text(i, -0.10, f"n={n}", ha="center", va="top",
                transform=ax.get_xaxis_transform(),
                fontsize=8, fontweight=weight)

    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_ylim(0, Y_MAX)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    if show_ylabel:
        ax.set_ylabel("Mean |SHAP| per instance", fontsize=11, fontweight="bold")


def main():
    babe = {s: load_babe_means(BABE_SAMPLES[s]) for s, _ in MODELS}
    basil = {s: load_basil_means(s) for s, _ in MODELS}
    data = {"BABE": babe, "BASIL": basil}

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=False, sharey=True)

    for row_i, (suffix, display) in enumerate(MODELS):
        for col_i, corpus in enumerate(CORPORA):
            ax = axes[row_i][col_i]
            panel_data = data[corpus][suffix]
            title = f"{display} — {corpus}"
            draw_panel(ax, panel_data, title, show_ylabel=(col_i == 0))

    # Shared mean/median legend.
    mean_line = plt.Line2D([0], [0], color="black", linestyle="--",
                           linewidth=1.5, label="Mean")
    med_line = plt.Line2D([0], [0], color="#ff7f0e", linestyle="-",
                          linewidth=1.5, label="Median")
    fig.legend(handles=[mean_line, med_line], loc="lower center",
               ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01))

    fig.suptitle("Per-instance mean |SHAP| by prediction category — "
                 "model × corpus", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])

    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")
    print()
    print("Per-panel n + median per category (cross-check vs findings_summary.md §3 and §5):")
    for suffix, display in MODELS:
        for corpus in CORPORA:
            panel_data = data[corpus][suffix]
            print(f"  {display} — {corpus}:")
            for cat in CATEGORIES:
                arr = panel_data[cat]
                n = len(arr)
                if n == 0:
                    print(f"    {cat}: n=0")
                    continue
                med = float(np.median(arr))
                clipped = int((arr > Y_MAX).sum())
                msg = f"    {cat}: n={n:>3}  median={med:.4f}"
                if clipped:
                    msg += f"  (clipped {clipped} outlier(s) above y={Y_MAX})"
                print(msg)


if __name__ == "__main__":
    main()
