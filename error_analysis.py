"""Pre-SHAP error analysis on the BASIL eval.

Two analyses, both reading the cached joined frame (no re-inference):

  1. FP overlap Venn: do biasdetector and daroberta make the same false
     positives, or different ones? High overlap = shared shortcut learning.
     Disjoint FPs = independent error patterns.

  2. Lex-only FN spot-check: ~20 sentences where the lex-only positives were
     missed at threshold 0.5. Stratified by which model(s) missed it.
     Sorted by probability (closest-to-threshold first) so it's easy to see
     whether failures are marginal calls or confident misses.

Run: python error_analysis.py
"""

import pandas as pd

from basil_eval import MODELS, load_joined

DEFAULT_THRESHOLD = 0.5
N_PER_CATEGORY = 7

BD = MODELS[0][0]  # "biasdetector"
DR = MODELS[1][0]  # "daroberta"


def fp_overlap(df, threshold=DEFAULT_THRESHOLD):
    neg = df[df.biased == 0]
    bd_fp_mask = neg[f"prob_{BD}"] >= threshold
    dr_fp_mask = neg[f"prob_{DR}"] >= threshold

    bd_total = int(bd_fp_mask.sum())
    dr_total = int(dr_fp_mask.sum())
    both = int((bd_fp_mask & dr_fp_mask).sum())
    bd_only = int((bd_fp_mask & ~dr_fp_mask).sum())
    dr_only = int((dr_fp_mask & ~bd_fp_mask).sum())
    union = bd_total + dr_total - both
    jaccard = both / union if union else 0.0

    return {
        "threshold": threshold,
        "negatives_total": len(neg),
        f"{BD}_FP_total": bd_total,
        f"{DR}_FP_total": dr_total,
        "shared_FPs": both,
        f"{BD}_only_FPs": bd_only,
        f"{DR}_only_FPs": dr_only,
        "jaccard": round(jaccard, 3),
        f"shared/{BD}_total": round(both / bd_total, 3) if bd_total else 0.0,
        f"shared/{DR}_total": round(both / dr_total, 3) if dr_total else 0.0,
    }


def print_overlap(overlap):
    for k, v in overlap.items():
        print(f"  {k:<28} {v}")


def lex_only_fn_categories(df, threshold=DEFAULT_THRESHOLD):
    lex_pos = df[
        (df.has_lex == 1) & (df.has_inf == 0) & (df.biased == 1)
    ].copy()
    lex_pos["bd_missed"] = lex_pos[f"prob_{BD}"] < threshold
    lex_pos["dr_missed"] = lex_pos[f"prob_{DR}"] < threshold

    both = lex_pos[lex_pos.bd_missed & lex_pos.dr_missed]
    bd_only = lex_pos[lex_pos.bd_missed & ~lex_pos.dr_missed]
    dr_only = lex_pos[~lex_pos.bd_missed & lex_pos.dr_missed]

    # Sort so closest-to-threshold misses come first (most informative for
    # "marginal vs confident miss" question).
    both = both.sort_values(f"prob_{BD}", ascending=False)
    bd_only = bd_only.sort_values(f"prob_{BD}", ascending=False)
    dr_only = dr_only.sort_values(f"prob_{DR}", ascending=False)

    return {
        "total_lex_only_positives": len(lex_pos),
        "both_missed": both,
        f"only_{BD}_missed": bd_only,
        f"only_{DR}_missed": dr_only,
    }


def print_fn_sample(label, rows, n):
    print(f"\n--- {label} — {len(rows)} total, showing top {min(n, len(rows))} by prob ---")
    for _, r in rows.head(n).iterrows():
        ref = f"{r.source} {r.year} {r.triplet_uuid[:8]}/{int(r.outlet_idx)}:{int(r.sentence_idx):>2}"
        bd = r[f"prob_{BD}"]
        dr = r[f"prob_{DR}"]
        print(f"\n  [{ref}]  bd={bd:.3f}  dr={dr:.3f}")
        print(f"  {r.text}")


def main():
    df = load_joined()

    print("=" * 78)
    print(f"PART 1 — False-positive overlap between models (threshold {DEFAULT_THRESHOLD})")
    print("=" * 78)
    print_overlap(fp_overlap(df))

    print()
    print("=" * 78)
    print(f"PART 2 — Lex-only false negatives at threshold {DEFAULT_THRESHOLD}")
    print("         (sentences with ONLY lexical bias that the model failed to flag)")
    print("=" * 78)
    cats = lex_only_fn_categories(df)
    print(f"\nTotal lex-only positives: {cats['total_lex_only_positives']}")
    print_fn_sample("Both models missed", cats["both_missed"], N_PER_CATEGORY)
    print_fn_sample(f"Only {BD} missed ({DR} caught it)",  cats[f"only_{BD}_missed"], N_PER_CATEGORY)
    print_fn_sample(f"Only {DR} missed ({BD} caught it)",  cats[f"only_{DR}_missed"], N_PER_CATEGORY)


if __name__ == "__main__":
    main()
