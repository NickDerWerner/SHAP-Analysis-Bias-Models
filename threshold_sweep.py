"""Threshold sweep + PR curves over the BASIL eval.

Uses cached prob_biased from outputs/basil/predictions_*.csv — no re-inference.

Three outputs in outputs/basil/:
  threshold_sweep_table.csv  Discrete sweep at {0.3, 0.4, 0.5, 0.6}. Drops
                             into the paper as the "what about other
                             thresholds?" table (Reviewer Ax3B).
  auprc_table.csv            AUPRC per (view, model). Threshold-independent —
                             this is what tells us whether the lex-vs-inf gap
                             is a structural model property or a 0.5-threshold
                             artifact.
  pr_curve_<view>.png        One curve per view, both models overlaid.
                             Diagnostic, not for the paper.
"""

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    precision_recall_fscore_support,
)

from basil_eval import MODELS, OUT_DIR, load_joined, view_filters

THRESHOLDS = [0.3, 0.4, 0.5, 0.6]


def metrics_at(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "P": p, "R": r, "F1": f1,
        "TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn),
    }


def main():
    df = load_joined()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sweep_rows = []
    auprc_rows = []

    for view_name, mask in view_filters(df):
        sub = df[mask]
        y_true = sub.biased.values
        n = len(sub)
        pos = int(sub.biased.sum())

        for suffix, _ in MODELS:
            y_prob = sub[f"prob_{suffix}"].values

            for t in THRESHOLDS:
                sweep_rows.append({
                    "view": view_name, "model": suffix, "threshold": t,
                    "n": n, "pos": pos,
                    **metrics_at(y_true, y_prob, t),
                })

            auprc_rows.append({
                "view": view_name, "model": suffix,
                "n": n, "pos": pos,
                "auprc": average_precision_score(y_true, y_prob),
                "baseline": pos / n,
            })

    sweep_df = pd.DataFrame(sweep_rows)
    auprc_df = pd.DataFrame(auprc_rows)

    sweep_path = OUT_DIR / "threshold_sweep_table.csv"
    auprc_path = OUT_DIR / "auprc_table.csv"
    sweep_df.to_csv(sweep_path, index=False)
    auprc_df.to_csv(auprc_path, index=False)

    # PR curves — one PNG per view, both models overlaid
    for view_name, mask in view_filters(df):
        sub = df[mask]
        y_true = sub.biased.values
        fig, ax = plt.subplots(figsize=(6, 5))
        for suffix, _ in MODELS:
            y_prob = sub[f"prob_{suffix}"].values
            precision, recall, _ = precision_recall_curve(y_true, y_prob)
            auprc = average_precision_score(y_true, y_prob)
            ax.plot(recall, precision, label=f"{suffix} (AUPRC={auprc:.3f})")
        pos_rate = y_true.mean()
        ax.axhline(
            pos_rate, linestyle="--", color="gray", linewidth=1,
            label=f"baseline (pos rate={pos_rate:.3f})",
        )
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title(
            f"PR curve — {view_name} (n={len(sub)}, pos={int(sub.biased.sum())})"
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(OUT_DIR / f"pr_curve_{view_name}.png", dpi=150)
        plt.close(fig)

    pd.options.display.float_format = "{:.3f}".format

    print("=== AUPRC (threshold-independent) ===")
    print(auprc_df.to_string(index=False))
    print()

    print("=== F1 by threshold ===")
    f1_pivot = sweep_df.pivot_table(
        index=["view", "model"], columns="threshold", values="F1"
    )
    print(f1_pivot.to_string(float_format="{:.3f}".format))
    print()

    print("=== Recall by threshold ===")
    r_pivot = sweep_df.pivot_table(
        index=["view", "model"], columns="threshold", values="R"
    )
    print(r_pivot.to_string(float_format="{:.3f}".format))
    print()

    print("=== Precision by threshold ===")
    p_pivot = sweep_df.pivot_table(
        index=["view", "model"], columns="threshold", values="P"
    )
    print(p_pivot.to_string(float_format="{:.3f}".format))
    print()

    print(f"Wrote {sweep_path}")
    print(f"Wrote {auprc_path}")
    print(f"Wrote {len(list(view_filters(df)))} PR curves to {OUT_DIR}")


if __name__ == "__main__":
    main()
