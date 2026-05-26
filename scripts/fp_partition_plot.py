#!/usr/bin/env python3
"""Combined BABE+BASIL FP-partition stacked bar chart (figure* size).

Single horizontal panel with 8 stacked bars: 4 BABE bars on the left,
4 BASIL bars on the right, separated by a visible gap. Each bar is a
4-category lexical composition (Em/Eval, Explicit, Fr/Rep, Fu/Temp).
Each bar is annotated with "n=N" so small-sample BABE cells are
visible in the figure itself. Sized for ACL `figure*` (two-column span,
~16 × 5 cm).

Outputs:
  outputs/fig7_fp_partition_combined.png
  outputs/paperReady/fig7_fp_partition_combined.pdf

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/fp_partition_plot.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
PAPER_DIR = OUT_DIR / "paperReady"
BABE_CSV  = OUT_DIR / "babe_fp_partition.csv"
BASIL_CSV = OUT_DIR / "basil_shap" / "basil_shap_fp_partition.csv"

CATEGORIES = [
    "Emotional/Evaluative",
    "Explicit Bias Terms",
    "Framing/Reporting Verbs",
    "Function/Temporal Words",
]
CAT_LABELS = ["Em/Eval", "Explicit", "Fr/Rep", "Fu/Temp"]
COLORS = {
    "Emotional/Evaluative":     "#2ca02c",  # green
    "Explicit Bias Terms":      "#d62728",  # red
    "Framing/Reporting Verbs":  "#1f77b4",  # blue
    "Function/Temporal Words":  "#ff7f0e",  # orange
}

# Fixed order of bars within each block.
BAR_SPEC = [
    ("shared",  "biasdetector", "BD\nshared"),
    ("shared",  "daroberta",    "DR\nshared"),
    ("bd_only", "biasdetector", "BD\nonly"),
    ("dr_only", "daroberta",    "DR\nonly"),
]


def load_babe(path):
    df = pd.read_csv(path)
    col_map = {
        "Emotional/Evaluative":     "pct_emotional_evaluative",
        "Explicit Bias Terms":      "pct_explicit_bias",
        "Framing/Reporting Verbs":  "pct_framing_reporting",
        "Function/Temporal Words":  "pct_function_temporal",
    }
    out = {}
    for _, r in df.iterrows():
        out[(r["partition"], r["model"])] = {
            "n_sentences": int(r["n_sentences"]),
            "n_selected":  int(r["n_selected_words"]),
            "props":       {c: float(r[col_map[c]]) for c in CATEGORIES},
        }
    return out


def load_basil(path):
    df = pd.read_csv(path)
    summary = df[df["level"] == "summary"].copy()
    summary["proportion"] = pd.to_numeric(summary["proportion"], errors="coerce")
    out = {}
    for (partition, model), g in summary.groupby(["partition", "model"]):
        props = {row["category"]: float(row["proportion"]) * 100.0
                 for _, row in g.iterrows()}
        for c in CATEGORIES:
            props.setdefault(c, 0.0)
        out[(partition, model)] = {
            "n_sentences": 100,  # BASIL FP partition sampled at 100/cell
            "n_selected":  int(g["n_selected_words"].iloc[0]),
            "props":       props,
        }
    return out


def assemble_bars(babe, basil):
    """Return ordered list of (label, n, props) for the 8 bars."""
    bars = []
    for partition, model, label in BAR_SPEC:
        cell = babe[(partition, model)]
        bars.append((label, cell["n_sentences"], cell["props"]))
    for partition, model, label in BAR_SPEC:
        cell = basil[(partition, model)]
        bars.append((label, cell["n_sentences"], cell["props"]))
    return bars


def draw(bars, out_png, out_pdf):
    """Render the combined figure at ACL `figure*` size (~16 × 5 cm)."""
    # Positions: 0..3 for BABE, gap, 5..8 for BASIL.
    positions = [0, 1, 2, 3, 5, 6, 7, 8]
    width = 0.72

    fig, ax = plt.subplots(figsize=(6.30, 1.97))

    # Stacked bars.
    for x, (_, _, props) in zip(positions, bars):
        bottom = 0.0
        for cat in CATEGORIES:
            p = props[cat]
            ax.bar(x, p, width, bottom=bottom,
                   color=COLORS[cat], edgecolor="black", linewidth=0.4)
            bottom += p

    # Per-bar n annotations.
    for x, (_, n, _) in zip(positions, bars):
        ax.text(x, 103.0, f"n={n}",
                ha="center", va="bottom", fontsize=7.0)

    # Corpus block labels.
    babe_center = sum(positions[:4]) / 4
    basil_center = sum(positions[4:]) / 4
    ax.text(babe_center,  122.0, "BABE",
            ha="center", va="bottom", fontsize=10.0, fontweight="bold")
    ax.text(basil_center, 122.0, "BASIL",
            ha="center", va="bottom", fontsize=10.0, fontweight="bold")

    # Block separator (subtle vertical gridline in the gap).
    ax.axvline(4.0, color="#bbbbbb", linestyle=":", linewidth=0.7)

    # Axes.
    ax.set_xticks(positions)
    ax.set_xticklabels([b[0] for b in bars], fontsize=7.5)
    ax.set_ylim(0, 138)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"], fontsize=8.0)
    ax.set_ylabel("Percentage of selected words (%)",
                  fontsize=9.0, fontweight="bold")
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(-0.7, 8.7)

    # Legend.
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=COLORS[c],
                             edgecolor="black", linewidth=0.4) for c in CATEGORIES]
    ax.legend(handles, CAT_LABELS, loc="lower center",
              ncol=4, fontsize=7.5, frameon=False,
              bbox_to_anchor=(0.5, -0.32),
              columnspacing=1.0, handlelength=1.2, handletextpad=0.3)

    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    babe = load_babe(BABE_CSV)
    basil = load_basil(BASIL_CSV)
    bars = assemble_bars(babe, basil)

    draw(bars,
         out_png=OUT_DIR / "fig7_fp_partition_combined.png",
         out_pdf=PAPER_DIR / "fig7_fp_partition_combined.pdf")

    print("Wrote:")
    print(f"  {OUT_DIR / 'fig7_fp_partition_combined.png'}")
    print(f"  {PAPER_DIR / 'fig7_fp_partition_combined.pdf'}")

    # Stdout dump for cross-checking against the paper prose.
    print("\n=== Per-bar composition ===")
    print(f"{'corpus':<6} {'bar':<12} {'n':>4} | "
          f"{'Em/Eval':>7} {'Explicit':>8} {'Fr/Rep':>7} {'Fu/Temp':>7}")
    print("-" * 60)
    for corpus_name, corpus_bars in [("BABE",  bars[:4]), ("BASIL", bars[4:])]:
        for label, n, props in corpus_bars:
            label_flat = label.replace("\n", " ")
            print(f"{corpus_name:<6} {label_flat:<12} {n:>4} | "
                  f"{props['Emotional/Evaluative']:>7.2f} "
                  f"{props['Explicit Bias Terms']:>8.2f} "
                  f"{props['Framing/Reporting Verbs']:>7.2f} "
                  f"{props['Function/Temporal Words']:>7.2f}")


if __name__ == "__main__":
    main()
