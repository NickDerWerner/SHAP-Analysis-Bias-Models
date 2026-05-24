"""Compute zero-shot metrics for both bias models over BASIL.

Reads the master CSV + per-model prediction sidecars, joins, then computes
metrics for each evaluation view as a boolean filter on the joined frame.
No re-inference, no subset materialization. View definitions live in
basil_eval.py so threshold_sweep.py uses identical slices.

Outputs:
  - Stdout: human-readable table
  - outputs/basil/basil_metrics_table.csv: machine-readable version
"""

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from basil_eval import MODELS, OUT_DIR, load_joined, view_filters


def metrics_for(y_true, y_pred):
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    acc = accuracy_score(y_true, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "acc": acc, "P": p, "R": r, "F1": f1,
        "TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn),
    }


def main():
    df = load_joined()
    rows = []
    for view_name, mask in view_filters(df):
        sub = df[mask]
        n = len(sub)
        pos = int(sub.biased.sum())
        for suffix, _ in MODELS:
            m = metrics_for(
                sub.biased.values,
                sub[f"pred_{suffix}"].astype(int).values,
            )
            rows.append({
                "view": view_name,
                "model": suffix,
                "n": n,
                "pos": pos,
                "pos_rate": pos / n,
                **m,
            })

    table = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "basil_metrics_table.csv"
    table.to_csv(out_path, index=False)

    pd.options.display.float_format = "{:.3f}".format
    print(table.to_string(index=False))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
