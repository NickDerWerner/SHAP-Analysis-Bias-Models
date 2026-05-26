#!/usr/bin/env python3
"""BABE Figure 3 with FN — mean |SHAP| by prediction type, all four categories.

Mirrors basil_fig3_counterpart.py exactly (same layout, palette, separator,
mean/median lines) but reads BABE's JSONL caches directly and computes the
per-sentence mean |SHAP| on the fly. Adds the FN category that the original
BABE Fig 3 omitted (analysis.py only sampled TP/FP/TN).

Run babe_shap_fn.py first to populate the FN records in the JSONL caches.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python babe_fig3_with_fn.py

Reads:  outputs/shap_samples.jsonl
        outputs/shap_samples_daroberta.jsonl
Writes: outputs/babe_fig3_with_fn.png  (300 DPI)
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "outputs" / "babe_fig3_with_fn.png"
OUT_PDF  = ROOT / "outputs" / "paperReady" / "babe_fig3_with_fn.pdf"
SAMPLES = [
    ("biasdetector", "bias-detector", ROOT / "outputs" / "shap_samples.jsonl"),
    ("daroberta",    "DA-RoBERTa",    ROOT / "outputs" / "shap_samples_daroberta.jsonl"),
]

COLORS = {"TP": "#2ecc71", "FP": "#e74c3c", "TN": "#3498db", "FN": "#f39c12"}
TYPE_ORDER = ["TP", "FP", "TN", "FN"]
# Match the y-axis range of the original BABE Fig 3 / basil_fig3_counterpart
# so all three figures are directly visually comparable. Outliers clipped.
Y_MAX = 0.15


def pred_category(gold, pred):
    if gold == 1 and pred == 1: return "TP"
    if gold == 0 and pred == 1: return "FP"
    if gold == 0 and pred == 0: return "TN"
    return "FN"


def load_means(jsonl_path):
    """Returns dict[category] -> list[mean_abs_shap]."""
    out = {c: [] for c in TYPE_ORDER}
    if not jsonl_path.exists():
        print(f"[WARN] {jsonl_path} missing")
        return out
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
            m = float(np.mean([abs(x["shap"]) for x in wa]))
            out[cat].append(m)
    return out


def main():
    per_model = {suffix: load_means(p) for suffix, _, p in SAMPLES}

    data_list = []
    labels_list = []
    positions = []
    pos = 0.0
    for suffix, display, _ in SAMPLES:
        for pt in TYPE_ORDER:
            data = np.array(per_model[suffix][pt], dtype=float)
            data_list.append(data)
            labels_list.append((display, pt))
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

    for patch, (_, pt) in zip(bp["boxes"], labels_list):
        patch.set_facecolor(COLORS[pt])
        patch.set_alpha(0.7)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.2)

    ax.set_ylabel("Mean |SHAP| per Instance", fontsize=13, fontweight="bold")
    ax.set_xlabel("Model × Prediction Type", fontsize=13, fontweight="bold")
    ax.set_title("SHAP Magnitude Distributions by Prediction Type (BABE)",
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
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Wrote {OUT_PATH}")
    for (disp, pt), data in zip(labels_list, data_list):
        n = len(data)
        med = float(np.median(data)) if n else float("nan")
        mean = float(np.mean(data)) if n else float("nan")
        clipped = int((data > Y_MAX).sum()) if n else 0
        print(f"  {disp:>14} {pt}: n={n:>3}  median={med:.4f}  mean={mean:.4f}"
              + (f"  (clipped {clipped} outlier(s) above y={Y_MAX})" if clipped else ""))


if __name__ == "__main__":
    main()
