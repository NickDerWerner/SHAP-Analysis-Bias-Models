"""Shared helpers for BASIL evaluation scripts.

Owns the canonical join logic and view definitions so that
compute_metrics.py, threshold_sweep.py, and future SHAP-side scripts all
operate on identical slices. Any drift in view definitions would silently
corrupt comparisons across outputs, so define them in exactly one place.

Views:
  full           all 7,984 sentences
  lex-only       biased == 0, OR (has_lex == 1 AND has_inf == 0)
  inf-only       biased == 0, OR (has_inf == 1 AND has_lex == 0)
  both-types     biased == 0, OR has_both_types == 1  (only 44 positives —
                 tiny class, expect noisy metric estimates)
  quote-excluded drop positives whose bias is entirely inside a quote.
                 Kept: all negatives + positives with quote_status in
                 {no_quote, mixed}.
  quote-only     drop positives whose bias is at least partly outside a quote.
                 Kept: all negatives + positives with quote_status ==
                 all_in_quote.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "basil_sentences.csv"
OUT_DIR = ROOT / "outputs" / "basil"

MODELS = [
    ("biasdetector", "himel7/bias-detector"),
    ("daroberta", "mediabiasgroup/DA-RoBERTa-BABE-FT"),
    ("deberta", str(ROOT / "models" / "deberta-base-babe-ft")),
]

EXPECTED_ROWS = 7984


def load_joined():
    df = pd.read_csv(CSV_PATH)
    for suffix, _ in MODELS:
        pred_path = OUT_DIR / f"predictions_{suffix}.csv"
        if not pred_path.exists():
            raise SystemExit(
                f"Missing {pred_path}. Run: python run_inference.py "
                f"--model <hf-path> --model_suffix {suffix}"
            )
        pred = pd.read_csv(pred_path).rename(
            columns={"prob_biased": f"prob_{suffix}", "pred": f"pred_{suffix}"}
        )
        df = df.merge(
            pred,
            on=["triplet_uuid", "outlet_idx", "sentence_idx"],
            how="left",
            validate="one_to_one",
        )
        if df[f"pred_{suffix}"].isna().any():
            raise SystemExit(f"predictions for {suffix} don't cover every sentence")
    if len(df) != EXPECTED_ROWS:
        raise SystemExit(f"Joined frame has {len(df)} rows; expected {EXPECTED_ROWS}.")
    return df


def view_filters(df):
    return [
        ("full",           pd.Series(True, index=df.index)),
        ("lex-only",       (df.biased == 0) | ((df.has_lex == 1) & (df.has_inf == 0))),
        ("inf-only",       (df.biased == 0) | ((df.has_inf == 1) & (df.has_lex == 0))),
        ("both-types",     (df.biased == 0) | (df.has_both_types == 1)),
        ("quote-excluded", (df.biased == 0) | (df.quote_status.isin(["no_quote", "mixed"]))),
        ("quote-only",     (df.biased == 0) | (df.quote_status == "all_in_quote")),
    ]
