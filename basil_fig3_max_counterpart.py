#!/usr/bin/env python3
"""BASIL Figure 3 max-counterpart — per-instance max |SHAP| by prediction type.

Mirrors `basil_fig3_counterpart.py` exactly (same layout, palette, separator,
mean/median lines) but plots per-sentence max |SHAP| instead of mean |SHAP|.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python basil_fig3_max_counterpart.py

Reads:  outputs/basil_shap/basil_shap_magnitude.csv  (must have max_abs_shap column)
Writes: outputs/basil_shap/basil_fig3_max_counterpart.png  (300 DPI)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "outputs" / "basil_shap" / "basil_shap_magnitude.csv"
OUT_PATH = ROOT / "outputs" / "basil_shap" / "basil_fig3_max_counterpart.png"

COLORS = {"TP": "#2ecc71", "FP": "#e74c3c", "TN": "#3498db", "FN": "#f39c12"}
TYPE_ORDER = ["TP", "FP", "TN", "FN"]
MODEL_ORDER = [
    ("biasdetector", "bias-detector"),
    ("daroberta", "DA-RoBERTa"),
]
# Max |SHAP| reaches ~0.5 on individual bias words (e.g. "pounced", "bombshell"),
# so the y-axis is set higher than the mean-figure's 0.15. Outliers above this
# are clipped and counted in the printout below.
Y_MAX = 0.6


def main():
    df = pd.read_csv(CSV_PATH)
    if "max_abs_shap" not in df.columns:
        raise SystemExit(
            f"{CSV_PATH} has no 'max_abs_shap' column. "
            "Re-run basil_shap_analyze.py to regenerate the CSV."
        )

    data_list = []
    labels_list = []
    positions = []
    pos = 0.0
    for suffix, display in MODEL_ORDER:
        for pred_type in TYPE_ORDER:
            data = df[(df.model == suffix) & (df.category == pred_type)]["max_abs_shap"].values
            data_list.append(data)
            labels_list.append((display, pred_type))
            positions.append(pos)
            pos += 1
        pos += 0.5  # gap between models
    x_labels = [f"{disp}\n{pt}" for disp, pt in labels_list]
    n_per_model = len(TYPE_ORDER)
    mid_point = (positions[n_per_model - 1] + positions[n_per_model]) / 2

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    bp = ax.boxplot(
        data_list, positions=positions, widths=0.6, patch_artist=True,
        tick_labels=x_labels,
        showmeans=True, meanline=True,
        meanprops=dict(linestyle="--", linewidth=1.5, color="black"),
        medianprops=dict(linestyle="-", linewidth=1.5, color="#ff7f0e"),
        flierprops=dict(marker="o", markerfacecolor="none",
                        markeredgecolor="black", markersize=4, linewidth=0.8),
    )

    for patch, (_, pred_type) in zip(bp["boxes"], labels_list):
        patch.set_facecolor(COLORS[pred_type])
        patch.set_alpha(0.7)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.2)

    ax.set_ylabel("Max |SHAP| per Instance", fontsize=13, fontweight="bold")
    ax.set_xlabel("Model × Prediction Type", fontsize=13, fontweight="bold")
    ax.set_title("SHAP Max Magnitude Distributions by Prediction Type (BASIL)",
                 fontsize=14, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_ylim(0, Y_MAX)

    ax.axvline(x=mid_point, color="gray", linestyle="--", linewidth=1.5, alpha=0.6)

    legend_elements = [
        Patch(facecolor=COLORS["TP"], alpha=0.7, label="True Positives (TP)"),
        Patch(facecolor=COLORS["FP"], alpha=0.7, label="False Positives (FP)"),
        Patch(facecolor=COLORS["TN"], alpha=0.7, label="True Negatives (TN)"),
        Patch(facecolor=COLORS["FN"], alpha=0.7, label="False Negatives (FN)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right",
              frameon=True, fancybox=True, shadow=True)

    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Wrote {OUT_PATH}")
    for (disp, pt), data in zip(labels_list, data_list):
        n = len(data)
        med = float(pd.Series(data).median()) if n else float("nan")
        mean = float(pd.Series(data).mean()) if n else float("nan")
        clipped = int((data > Y_MAX).sum()) if n else 0
        print(f"  {disp:>14} {pt}: n={n:>3}  median={med:.4f}  mean={mean:.4f}"
              + (f"  (clipped {clipped} outlier(s) above y={Y_MAX})" if clipped else ""))


if __name__ == "__main__":
    main()
