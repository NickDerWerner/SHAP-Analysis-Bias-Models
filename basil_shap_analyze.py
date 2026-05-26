#!/usr/bin/env python3
"""Fast analysis pass over the BASIL SHAP cache.

Reads outputs/basil_shap/samples_*.jsonl + manifest.csv (produced by
basil_shap_generate.py) and writes the four analysis CSVs, diagnostic
plots, and a brief outcome summary. Seconds to run; re-run any time.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python basil_shap_analyze.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from babe_fig6_confound import CATEGORIES, aggregate_words, categorize_word


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs" / "basil_shap"
DIAG_DIR = OUT_DIR / "diagnostics"
MANIFEST_PATH = OUT_DIR / "manifest.csv"

SUFFIXES = ["biasdetector", "daroberta"]
MODEL_DISPLAY = {"biasdetector": "bias-detector", "daroberta": "DA-RoBERTa"}
TOP_N = 20
KEY_COLS = ["triplet_uuid", "outlet_idx", "sentence_idx"]
FIG3_Y_MAX = 0.15  # y-axis cap used in basil_fig3_counterpart.py
FIG3_MAX_Y_MAX = 0.6  # y-axis cap used in basil_fig3_max_counterpart.py


# ----------------------------------------------------------------- helpers

def load_samples(suffix):
    path = OUT_DIR / f"samples_{suffix}.jsonl"
    out = []
    if not path.exists():
        print(f"[WARN] {path} missing")
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out


def record_key(r):
    return (r["triplet_uuid"], int(r["outlet_idx"]), int(r["sentence_idx"]))


def pred_category(gold, pred):
    if gold == 1 and pred == 1: return "TP"
    if gold == 0 and pred == 1: return "FP"
    if gold == 0 and pred == 0: return "TN"
    return "FN"


def mean_abs_shap(r):
    wa = r["word_attribs"]
    if not wa:
        return 0.0
    return float(np.mean([abs(x["shap"]) for x in wa]))


def max_abs_shap(r):
    wa = r["word_attribs"]
    if not wa:
        return 0.0
    return float(np.max([abs(x["shap"]) for x in wa]))


def top_n_pairs(r, n=TOP_N):
    return sorted(r["word_attribs"], key=lambda x: abs(x["shap"]), reverse=True)[:n]


def top_n_str(r, n=TOP_N):
    return ";".join(f"{x['word']}|{x['shap']:.4f}" for x in top_n_pairs(r, n))


def parse_top_n_words(s):
    if pd.isna(s) or not s:
        return set()
    return {p.split("|", 1)[0].lower().strip() for p in s.split(";") if p}


def df_to_md(df, index=False, floatfmt=".4f"):
    """Render a DataFrame as a GitHub-flavored markdown table without tabulate."""
    if df is None or len(df) == 0:
        return "(empty)"

    def fmt(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            return format(v, floatfmt)
        return str(v)

    if index:
        idx_names = list(df.index.names)
        idx_names = [n if n is not None else "" for n in idx_names]
        headers = idx_names + [str(c) for c in df.columns]
        rows = []
        for idx, row in df.iterrows():
            idx_vals = list(idx) if isinstance(idx, tuple) else [idx]
            rows.append([fmt(v) for v in idx_vals] + [fmt(v) for v in row.values])
    else:
        headers = [str(c) for c in df.columns]
        rows = [[fmt(v) for v in row.values] for _, row in df.iterrows()]

    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def median_pairwise_jaccard(paired_df, model_a="biasdetector", model_b="daroberta"):
    """Per-sentence Jaccard of top-N word types between the two models."""
    wide = paired_df.pivot_table(
        index=KEY_COLS, columns="model", values="top20_tokens", aggfunc="first"
    ).reset_index()
    if model_a not in wide.columns or model_b not in wide.columns:
        return float("nan"), 0
    wide = wide.dropna(subset=[model_a, model_b])
    js = []
    for _, r in wide.iterrows():
        sa = parse_top_n_words(r[model_a])
        sb = parse_top_n_words(r[model_b])
        u = sa | sb
        if not u:
            continue
        js.append(len(sa & sb) / len(u))
    return (float(np.median(js)) if js else float("nan")), len(js)


# ----------------------------------------------------------------- outputs

def build_magnitude_csv(manifest, cache):
    rows = []
    sub = manifest[manifest.stratum.str.startswith("magnitude_")]
    for _, m in sub.iterrows():
        r = cache.get((m.model, (m.triplet_uuid, int(m.outlet_idx), int(m.sentence_idx))))
        if r is None:
            continue
        rows.append({
            "model": m.model,
            "triplet_uuid": r["triplet_uuid"],
            "outlet_idx": r["outlet_idx"],
            "sentence_idx": r["sentence_idx"],
            "category": pred_category(r["gold"], r["pred"]),
            "biased": r["biased"],
            "has_lex": r["has_lex"],
            "has_inf": r["has_inf"],
            "has_both_types": r["has_both_types"],
            "quote_status": r["quote_status"],
            "mean_abs_shap": mean_abs_shap(r),
            "max_abs_shap": max_abs_shap(r),
            "n_tokens": len(r["tokens"]),
            "n_word_attribs": len(r["word_attribs"]),
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["model"] + KEY_COLS)
    df.to_csv(OUT_DIR / "basil_shap_magnitude.csv", index=False)
    return df


def build_bias_type_csv(manifest, cache):
    stratum_to_type = {
        "bias_type_lex": "lex_only",
        "bias_type_inf": "inf_only",
        "bias_type_both": "both",
    }
    rows = []
    sub = manifest[manifest.stratum.isin(stratum_to_type)]
    for _, m in sub.iterrows():
        r = cache.get((m.model, (m.triplet_uuid, int(m.outlet_idx), int(m.sentence_idx))))
        if r is None:
            continue
        rows.append({
            "model": m.model,
            "triplet_uuid": r["triplet_uuid"],
            "outlet_idx": r["outlet_idx"],
            "sentence_idx": r["sentence_idx"],
            "bias_type": stratum_to_type[m.stratum],
            "mean_abs_shap": mean_abs_shap(r),
            "top20_tokens": top_n_str(r),
        })
    df = pd.DataFrame(rows).drop_duplicates(subset=["model"] + KEY_COLS)
    df.to_csv(OUT_DIR / "basil_shap_bias_type.csv", index=False)
    return df


def build_fp_partition_csv(manifest, cache):
    partition_strata = {
        "fp_shared": "shared",
        "fp_bd_only": "bd_only",
        "fp_dr_only": "dr_only",
    }

    aggregated = {}  # (partition, model) -> aggregated word DataFrame
    for stratum, partition in partition_strata.items():
        sub = manifest[manifest.stratum == stratum]
        for model in SUFFIXES:
            sub_m = sub[sub.model == model]
            recs = []
            seen = set()
            for _, m in sub_m.iterrows():
                key = (m.triplet_uuid, int(m.outlet_idx), int(m.sentence_idx))
                if key in seen:
                    continue
                r = cache.get((model, key))
                if r is not None:
                    recs.append(r)
                    seen.add(key)
            if recs:
                aggregated[(partition, model)] = aggregate_words(recs)

    pooled = []
    for df_agg in aggregated.values():
        pooled.extend(df_agg["mean_abs_shap"].tolist())
    threshold_global = float(np.percentile(pooled, 75)) if pooled else 0.0
    print(f"  threshold_global (p75 of {len(pooled)} pooled word means) = {threshold_global:.4f}")

    rows = []
    for (partition, model), df_agg in aggregated.items():
        sel = df_agg[df_agg["mean_abs_shap"] >= threshold_global].copy()
        sel["category"] = sel["word"].apply(categorize_word)
        n_sel = len(sel)

        for _, w in sel.iterrows():
            rows.append({
                "level": "feature",
                "partition": partition,
                "model": model,
                "word": w["word"],
                "mean_abs_shap": round(float(w["mean_abs_shap"]), 6),
                "count": int(w["count"]),
                "category": w["category"],
                "proportion": "",
                "n_selected_words": "",
            })
        for cat in CATEGORIES:
            n_cat = int((sel["category"] == cat).sum())
            prop = n_cat / n_sel if n_sel else 0.0
            rows.append({
                "level": "summary",
                "partition": partition,
                "model": model,
                "word": "",
                "mean_abs_shap": "",
                "count": n_cat,
                "category": cat,
                "proportion": round(prop, 4),
                "n_selected_words": n_sel,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "basil_shap_fp_partition.csv", index=False)
    return df, threshold_global


def build_paired_csv(manifest, cache, stratum, filename):
    sub = manifest[manifest.stratum == stratum][KEY_COLS].drop_duplicates()
    rows = []
    for _, m in sub.iterrows():
        key = (m.triplet_uuid, int(m.outlet_idx), int(m.sentence_idx))
        for model in SUFFIXES:
            r = cache.get((model, key))
            if r is None:
                continue
            rows.append({
                "triplet_uuid": m.triplet_uuid,
                "outlet_idx": int(m.outlet_idx),
                "sentence_idx": int(m.sentence_idx),
                "model": model,
                "mean_abs_shap": mean_abs_shap(r),
                "top20_tokens": top_n_str(r),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / filename, index=False)
    return df


# ----------------------------------------------------------------- plots

def plot_magnitude_boxplot(mag_df):
    if mag_df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    cats = ["TP", "FP", "TN", "FN"]
    for ax, model in zip(axes, SUFFIXES):
        sub = mag_df[mag_df.model == model]
        data = [sub[sub.category == c]["mean_abs_shap"].values for c in cats]
        ax.boxplot(data, tick_labels=cats)
        ax.set_title(model)
        ax.set_ylabel("mean |SHAP| per sentence")
        ax.grid(alpha=0.3)
    fig.suptitle("Per-sentence mean |SHAP| by category")
    fig.tight_layout()
    fig.savefig(DIAG_DIR / "magnitude_boxplot.png", dpi=150)
    plt.close(fig)


def plot_magnitude_by_bias_type(bt_df):
    if bt_df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    types = ["lex_only", "inf_only", "both"]
    for ax, model in zip(axes, SUFFIXES):
        sub = bt_df[bt_df.model == model]
        data = [sub[sub.bias_type == t]["mean_abs_shap"].values for t in types]
        ax.boxplot(data, tick_labels=types)
        ax.set_title(model)
        ax.set_ylabel("mean |SHAP| per sentence")
        ax.grid(alpha=0.3)
    fig.suptitle("TP per-sentence mean |SHAP| by bias type")
    fig.tight_layout()
    fig.savefig(DIAG_DIR / "magnitude_by_bias_type.png", dpi=150)
    plt.close(fig)


def plot_fp_partition_composition(fp_df):
    summary = fp_df[fp_df.level == "summary"].copy()
    if summary.empty:
        return
    summary["proportion"] = pd.to_numeric(summary["proportion"], errors="coerce")

    partitions = ["shared", "bd_only", "dr_only"]
    pairs = []
    for p in partitions:
        for m in SUFFIXES:
            if not summary[(summary.partition == p) & (summary.model == m)].empty:
                pairs.append((p, m))
    if not pairs:
        return

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(pairs))
    bottom = np.zeros(len(pairs))
    colors = {"Emotional/Evaluative": "#e74c3c", "Explicit Bias Terms": "#8e44ad",
              "Framing/Reporting Verbs": "#3498db", "Function/Temporal Words": "#95a5a6"}
    for cat in CATEGORIES:
        vals = []
        for p, m in pairs:
            sel = summary[(summary.partition == p) & (summary.model == m) & (summary.category == cat)]
            vals.append(float(sel.proportion.iloc[0]) if not sel.empty else 0.0)
        ax.bar(x, vals, bottom=bottom, label=cat, color=colors[cat])
        bottom += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}\n{m}" for p, m in pairs])
    ax.set_ylabel("Proportion of threshold-selected words")
    ax.set_title("FP partition composition (threshold-based selection)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(DIAG_DIR / "fp_partition_composition.png", dpi=150)
    plt.close(fig)


def plot_paired_scatter(df, filename, title):
    if df.empty:
        return
    wide = df.pivot_table(index=KEY_COLS, columns="model", values="mean_abs_shap").reset_index()
    if "biasdetector" not in wide.columns or "daroberta" not in wide.columns:
        return
    wide = wide.dropna(subset=["biasdetector", "daroberta"])
    if wide.empty:
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(wide["biasdetector"], wide["daroberta"], alpha=0.5)
    lim = float(max(wide["biasdetector"].max(), wide["daroberta"].max())) * 1.05
    ax.plot([0, lim], [0, lim], "--", color="gray", linewidth=1)
    ax.set_xlabel("BD mean |SHAP|")
    ax.set_ylabel("DR mean |SHAP|")
    ax.set_title(title)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(DIAG_DIR / filename, dpi=150)
    plt.close(fig)


# ----------------------------------------------------------------- summary

def write_summary(manifest, mag_df, bt_df, fp_df, fp_paired_df, fn_df,
                  threshold_global, missing_count):
    L = []
    L.append("# BASIL SHAP analysis — outcome summary")
    L.append("")

    # 1. Sample sizes
    L.append("## 1. Sample sizes (unique sentences per (model, stratum))")
    L.append("")
    counts = (manifest
              .groupby(["model", "stratum"])
              .apply(lambda g: g[KEY_COLS].drop_duplicates().shape[0],
                     include_groups=False)
              .reset_index(name="n_sentences"))
    L.append(df_to_md(counts, index=False))
    L.append("")

    # 2. SHAP magnitude by prediction type (BASIL Fig 3 counterpart)
    L.append("## 2. SHAP magnitude by prediction type (BASIL Fig 3 counterpart)")
    L.append("")
    L.append(f"Per-instance mean |SHAP| from `magnitude_TP/FP/TN` strata. "
             f"These are the numbers underlying `basil_fig3_counterpart.png`. "
             f"Clipped-outlier counts refer to the figure's y-axis cap "
             f"(y={FIG3_Y_MAX}, matched to the original BABE Fig 3).")
    L.append("")
    if mag_df.empty:
        L.append("(no magnitude records)")
    else:
        mag_rows = []
        for suffix in SUFFIXES:
            for pt in ["TP", "FP", "TN", "FN"]:
                sub = mag_df[(mag_df.model == suffix) & (mag_df.category == pt)]
                n = len(sub)
                med = float(sub["mean_abs_shap"].median()) if n else float("nan")
                mean = float(sub["mean_abs_shap"].mean()) if n else float("nan")
                clipped = int((sub["mean_abs_shap"] > FIG3_Y_MAX).sum()) if n else 0
                mag_rows.append({
                    "model": MODEL_DISPLAY[suffix],
                    "category": pt,
                    "n": n,
                    "median": med,
                    "mean": mean,
                    f"clipped (>{FIG3_Y_MAX})": clipped,
                })
        L.append(df_to_md(pd.DataFrame(mag_rows), index=False, floatfmt=".4f"))
    L.append("")

    # 2b. Max |SHAP| per prediction type (BASIL Fig 3 max counterpart)
    L.append("## 2b. Max |SHAP| by prediction type (BASIL Fig 3 max counterpart)")
    L.append("")
    L.append(f"Per-instance max |SHAP| from `magnitude_TP/FP/TN/FN` strata. "
             f"These are the numbers underlying `basil_fig3_max_counterpart.png`. "
             f"Clipped-outlier counts refer to the figure's y-axis cap "
             f"(y={FIG3_MAX_Y_MAX}).")
    L.append("")
    if mag_df.empty or "max_abs_shap" not in mag_df.columns:
        L.append("(no max-magnitude records)")
    else:
        max_rows = []
        for suffix in SUFFIXES:
            for pt in ["TP", "FP", "TN", "FN"]:
                sub = mag_df[(mag_df.model == suffix) & (mag_df.category == pt)]
                n = len(sub)
                med = float(sub["max_abs_shap"].median()) if n else float("nan")
                mean = float(sub["max_abs_shap"].mean()) if n else float("nan")
                clipped = int((sub["max_abs_shap"] > FIG3_MAX_Y_MAX).sum()) if n else 0
                max_rows.append({
                    "model": MODEL_DISPLAY[suffix],
                    "category": pt,
                    "n": n,
                    "median": med,
                    "mean": mean,
                    f"clipped (>{FIG3_MAX_Y_MAX})": clipped,
                })
        L.append(df_to_md(pd.DataFrame(max_rows), index=False, floatfmt=".4f"))
    L.append("")

    # 3. Hypothesis A — bias-type independence
    L.append("## 3. Hypothesis A — bias-type independence at SHAP level")
    L.append("")
    if bt_df.empty:
        L.append("(no bias-type records)")
        L.append("")
    else:
        for model in SUFFIXES:
            sub = bt_df[bt_df.model == model]
            if sub.empty:
                continue
            L.append(f"**{model}**")
            for t in ["lex_only", "inf_only", "both"]:
                ss = sub[sub.bias_type == t]["mean_abs_shap"]
                if not ss.empty:
                    L.append(f"- {t}: n={len(ss)}, median mean_abs_shap = {ss.median():.4f}")
            top_words = {}
            for t in ["lex_only", "inf_only", "both"]:
                tokens = set()
                for s in sub[sub.bias_type == t]["top20_tokens"]:
                    tokens |= parse_top_n_words(s)
                top_words[t] = tokens
            if top_words["lex_only"] and top_words["inf_only"]:
                u = top_words["lex_only"] | top_words["inf_only"]
                jac = len(top_words["lex_only"] & top_words["inf_only"]) / len(u)
                L.append(f"- top-20 vocabulary Jaccard(lex_only, inf_only) = {jac:.3f}  "
                         f"(|lex|={len(top_words['lex_only'])}, |inf|={len(top_words['inf_only'])})")
            L.append("")

    # 4. Hypothesis B — FP partition composition
    L.append("## 4. Hypothesis B — same mechanism, different calibration (FP partition)")
    L.append("")
    L.append(f"Threshold (p75 of pooled mean_abs_shap across all FP partitions × models): "
             f"**{threshold_global:.4f}**")
    L.append("")
    summary = fp_df[fp_df.level == "summary"].copy()
    if not summary.empty:
        summary["proportion"] = pd.to_numeric(summary["proportion"], errors="coerce")
        pivot = (summary.pivot_table(index=["partition", "model"], columns="category",
                                     values="proportion", aggfunc="first")
                 .reindex(columns=CATEGORIES))
        L.append("**Category proportions among threshold-selected words:**")
        L.append("")
        L.append(df_to_md(pivot, index=True, floatfmt=".3f"))
        L.append("")

        nsel = (summary.groupby(["partition", "model"])
                .agg(n_selected_words=("n_selected_words", "first"))
                .reset_index())
        L.append("**Selected-word counts per (partition, model):**")
        L.append("")
        L.append(df_to_md(nsel, index=False))
        L.append("")

    # 5. FP paired
    L.append("## 5. FP paired mechanism check (shared FPs, both models)")
    L.append("")
    if fp_paired_df.empty:
        L.append("(no shared-FP paired records)")
        L.append("")
    else:
        js, n = median_pairwise_jaccard(fp_paired_df)
        med_bd = fp_paired_df[fp_paired_df.model == "biasdetector"]["mean_abs_shap"].median()
        med_dr = fp_paired_df[fp_paired_df.model == "daroberta"]["mean_abs_shap"].median()
        L.append(f"- Median per-sentence Jaccard of top-{TOP_N} tokens (BD ∩ DR / BD ∪ DR): "
                 f"**{js:.3f}** (n={n} sentences)")
        L.append(f"- Median per-sentence mean_abs_shap — BD: {med_bd:.4f}, DR: {med_dr:.4f}")
        L.append("")

    # 6. FN paired
    L.append("## 6. FN paired calibration check (shared lex-only FNs, both models)")
    L.append("")
    if fn_df.empty:
        L.append("(no shared-FN paired records)")
        L.append("")
    else:
        js, n = median_pairwise_jaccard(fn_df)
        med_bd = fn_df[fn_df.model == "biasdetector"]["mean_abs_shap"].median()
        med_dr = fn_df[fn_df.model == "daroberta"]["mean_abs_shap"].median()
        L.append(f"- Median per-sentence Jaccard of top-{TOP_N} tokens (BD ∩ DR / BD ∪ DR): "
                 f"**{js:.3f}** (n={n} sentences)")
        L.append(f"- Median per-sentence mean_abs_shap — BD: {med_bd:.4f}, DR: {med_dr:.4f}")
        L.append("")

    # 7. Sanity checks
    L.append("## 7. Sanity checks")
    L.append("")
    if not mag_df.empty:
        overall_mean = mag_df["mean_abs_shap"].mean()
        in_range = 0.02 <= overall_mean <= 0.08
        L.append(f"- **Magnitude scale**: overall mean mean_abs_shap = {overall_mean:.4f}. "
                 f"In BABE range [0.02, 0.08]? **{'YES' if in_range else 'NO — investigate'}**")
    L.append(f"- **Cache integrity**: {missing_count} manifest entries missing from JSONL caches")
    L.append("")

    # Known-bias attribution spot check
    L.append("### Known-bias attribution spot check (3 random lex-only TPs per model)")
    L.append("")
    for model in SUFFIXES:
        L.append(f"**{model}**:")
        sub = bt_df[(bt_df.model == model) & (bt_df.bias_type == "lex_only")]
        if sub.empty:
            L.append("- (no records)")
        else:
            picks = sub.sample(min(3, len(sub)), random_state=42)
            for _, p in picks.iterrows():
                top3 = p["top20_tokens"].split(";")[:3] if p["top20_tokens"] else []
                L.append(f"- {p['triplet_uuid'][:8]}.../{p['sentence_idx']}: "
                         f"top3 = {' | '.join(top3)}")
        L.append("")

    # 8. Key numbers (placeholder for user)
    L.append("## 8. Key numbers worth citing")
    L.append("")
    L.append("(Pull from the tables and plots above once reviewed.)")
    L.append("")

    # 9. Unexpected (placeholder)
    L.append("## 9. Unexpected findings")
    L.append("")
    L.append("(Note anything off-pattern after inspecting diagnostics/*.png.)")
    L.append("")

    (OUT_DIR / "basil_shap_summary.md").write_text("\n".join(L))


# ----------------------------------------------------------------- main

def main():
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing {MANIFEST_PATH}. Run basil_shap_generate.py first.")

    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(MANIFEST_PATH)
    cache = {}
    for suffix in SUFFIXES:
        for r in load_samples(suffix):
            cache[(suffix, record_key(r))] = r
    print(f"[load] {len(cache)} cached (model, sentence) records across {len(SUFFIXES)} models")

    # Cache integrity
    missing = 0
    for _, m in manifest.iterrows():
        key = (m.model, (m.triplet_uuid, int(m.outlet_idx), int(m.sentence_idx)))
        if key not in cache:
            missing += 1
    if missing:
        print(f"[CHECK] WARN: {missing} manifest entries not in cache "
              "(generate may be incomplete)")
    else:
        print(f"[CHECK] OK: all {len(manifest)} manifest entries present in cache")

    print("[1/5] basil_shap_magnitude.csv")
    mag_df = build_magnitude_csv(manifest, cache)

    print("[2/5] basil_shap_bias_type.csv")
    bt_df = build_bias_type_csv(manifest, cache)

    print("[3/5] basil_shap_fp_partition.csv")
    fp_df, threshold_global = build_fp_partition_csv(manifest, cache)

    print("[4/5] basil_shap_fp_shared_paired.csv")
    fp_paired_df = build_paired_csv(manifest, cache, "fp_shared", "basil_shap_fp_shared_paired.csv")

    print("[5/5] basil_shap_fn_shared.csv")
    fn_df = build_paired_csv(manifest, cache, "fn_shared_lex", "basil_shap_fn_shared.csv")

    print("[plots] diagnostics/*.png")
    plot_magnitude_boxplot(mag_df)
    plot_magnitude_by_bias_type(bt_df)
    plot_fp_partition_composition(fp_df)
    plot_paired_scatter(fp_paired_df, "fp_shared_paired.png", "Shared FP — BD vs DR (mean |SHAP|)")
    plot_paired_scatter(fn_df, "fn_shared_paired.png", "Shared FN (lex-only) — BD vs DR (mean |SHAP|)")

    print("[summary] basil_shap_summary.md")
    write_summary(manifest, mag_df, bt_df, fp_df, fp_paired_df, fn_df,
                  threshold_global, missing)

    print("[DONE]")


if __name__ == "__main__":
    main()
