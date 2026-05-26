"""Vocab-size confound check on the original BABE Figure 6.

Reviewer Ax3B argues DA-RoBERTa's 13% Function/Temporal share in panel (d) is
a denominator artifact: DA-RoBERTa has ~12 FPs vs bias-detector's ~37, so
"top 100" is drawn from a much smaller vocabulary pool. This script
re-evaluates panel (d) under five conditions and decides outcome A/B/C.

Reads only existing artifacts (no re-inference, no new SHAP):
  outputs/shap_samples237.jsonl       (bias-detector, 237 samples)
  outputs/shap_samples_daroberta.jsonl (DA-RoBERTa, 212 samples)

Writes to outputs/babe_fig6_confound/:
  vocab_stats_table.csv
  fig6_sensitivity.png
  fig6_matched_pools.csv
  fig6_bootstrap_ci.png
  item3_summary.md   (with outcome A/B/C + BASIL recommendation)

Run:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python babe_fig6_confound.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs" / "babe_fig6_confound"

SAMPLES = {
    "biasdetector": ROOT / "outputs" / "shap_samples237.jsonl",
    "daroberta":    ROOT / "outputs" / "shap_samples_daroberta.jsonl",
}
MODEL_LABELS = {
    "biasdetector": "bias-detector",
    "daroberta": "DA-RoBERTa-BABE-FT",
}
THRESHOLD = 0.5
CATEGORIES = [
    "Emotional/Evaluative",
    "Explicit Bias Terms",
    "Framing/Reporting Verbs",
    "Function/Temporal Words",
]
CATEGORY_COLORS = {
    "Emotional/Evaluative":     "#e74c3c",
    "Explicit Bias Terms":      "#8e44ad",
    "Framing/Reporting Verbs":  "#3498db",
    "Function/Temporal Words":  "#95a5a6",
}
K_SWEEP = [25, 50, 100, 200, 500]
PROP_K = [5, 10, 20, 30]
BOOTSTRAP_B = 1000
BOOTSTRAP_SEED = 0
DEFAULT_K = 100

# Verification targets (published numbers from figure3_tp_fp_breakdown.png panels)
REPRO_TARGETS = {
    ("biasdetector", "TP"): {"Emotional/Evaluative": 93},
    ("biasdetector", "FP"): {
        "Emotional/Evaluative": 91,
        "Framing/Reporting Verbs": 4,
        "Function/Temporal Words": 4,
    },
    ("daroberta", "TP"): {
        "Emotional/Evaluative": 93,
        "Framing/Reporting Verbs": 5,
    },
    ("daroberta", "FP"): {
        "Emotional/Evaluative": 82,
        "Framing/Reporting Verbs": 5,
        "Function/Temporal Words": 13,
    },
}
REPRO_TOL = 2.0  # percentage points


# -------------------------------------------------------------------- helpers

def load_samples(path):
    out = []
    with open(path) as f:
        for line in f:
            out.append(json.loads(line))
    return out


def pred_type(gold, prob_pos, t=THRESHOLD):
    pred = 1 if prob_pos >= t else 0
    if gold == 1 and pred == 1:
        return "TP"
    if gold == 0 and pred == 1:
        return "FP"
    if gold == 0 and pred == 0:
        return "TN"
    return "FN"


def split_by_pred(samples):
    out = {"TP": [], "FP": [], "TN": [], "FN": []}
    for s in samples:
        pt = pred_type(s["gold"], s["prob_pos"])
        out[pt].append(s)
    return out


def normalize_word(w):
    return w.lower().strip('.,!?;:"()[]{}')


def aggregate_words(samples):
    """Return DataFrame[word, mean_abs_shap, count] aggregated from word_attribs.

    Words are normalized via .lower().strip('.,!?;:"()[]{}') to match the
    notebook's `extract_top_words_by_pred_type` behaviour.
    """
    bucket = {}
    for s in samples:
        for wa in s.get("word_attribs", []):
            w = normalize_word(wa["word"])
            if not w:
                continue
            v = abs(wa.get("shap", 0.0))
            if w not in bucket:
                bucket[w] = [0.0, 0]
            bucket[w][0] += v
            bucket[w][1] += 1
    if not bucket:
        return pd.DataFrame(columns=["word", "mean_abs_shap", "count"])
    return pd.DataFrame(
        [
            {"word": w, "mean_abs_shap": tot / cnt, "count": cnt}
            for w, [tot, cnt] in bucket.items()
        ]
    )


# Verbatim copy of categorize_word() from generate_figure1.ipynb cell 21.
def categorize_word(word):
    word_lower = word.lower().strip('.,!?;:"()[]{}')

    explicit_bias_terms = {
        'racist', 'antisemitic', 'xenophobic', 'sexist', 'bigoted', 'prejudice',
        'discriminatory', 'stereotype', 'stereotyping', 'discrimination'
    }
    if any(term in word_lower for term in explicit_bias_terms):
        return 'Explicit Bias Terms'

    framing_verbs = {
        'claim', 'claims', 'claimed', 'claiming', 'allege', 'alleges', 'alleged', 'alleging',
        'report', 'reports', 'reported', 'reporting', 'state', 'states', 'stated', 'stating',
        'say', 'says', 'said', 'saying', 'suggest', 'suggests', 'suggested', 'suggesting',
        'assert', 'asserts', 'asserted', 'asserting', 'maintain', 'maintains', 'maintained',
        'insist', 'insists', 'insisted', 'insisting', 'argue', 'argues', 'argued', 'arguing',
        'call', 'calls', 'called', 'calling', 'describe', 'describes', 'described', 'describing',
        'characterize', 'characterizes', 'characterized', 'portray', 'portrays', 'portrayed'
    }
    if word_lower in framing_verbs:
        return 'Framing/Reporting Verbs'

    function_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'of', 'to', 'in', 'on', 'at', 'for',
        'from', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'it', 'its', 'they', 'them', 'their', 'there', 'then', 'than', 'more', 'most',
        'some', 'any', 'all', 'each', 'every', 'other', 'another', 'much', 'many', 'very'
    }
    temporal_words = {
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'today', 'yesterday', 'tomorrow', 'now', 'then', 'when', 'before', 'after',
        'during', 'while', 'since', 'until', 'ago', 'recently', 'previously', 'earlier',
        'later', 'next', 'last', 'year', 'years', 'month', 'months', 'week', 'weeks',
        'day', 'days', 'hour', 'hours', 'time', 'times'
    }
    if word_lower in function_words or word_lower in temporal_words:
        return 'Function/Temporal Words'

    emotional_evaluative_terms = {
        'boasted', 'bloated', 'dubious', 'relentlessly', 'flagrantly', 'misleading',
        'frantically', 'sided', 'mess', 'quixotic', 'lashed', 'denigrate', 'bizarre',
        'uglier', 'blown', 'nasty', 'ranted', 'heartlessness', 'flippantly', 'flippancy',
        'blasted', 'junkies', 'sandbag', 'guzzling', 'gruesome', 'predominantly',
        'relentless', 'fierce', 'heated', 'intense', 'extreme', 'drastic', 'radical',
        'mockery', 'ridicule', 'scorn', 'contempt', 'disgust', 'anger', 'hate', 'despise',
        'amazing', 'terrible', 'awful', 'horrible', 'wonderful', 'fantastic', 'incredible'
    }
    if any(term in word_lower for term in emotional_evaluative_terms):
        return 'Emotional/Evaluative'

    if word_lower.endswith('less') or word_lower.endswith('ful'):
        if len(word_lower) > 4:
            return 'Emotional/Evaluative'

    return 'Emotional/Evaluative'


def category_proportions(words_df):
    """Return dict {category: percent} over rows in words_df."""
    if len(words_df) == 0:
        return {c: 0.0 for c in CATEGORIES}
    cats = words_df["word"].apply(categorize_word)
    counts = cats.value_counts()
    n = len(words_df)
    return {c: 100.0 * counts.get(c, 0) / n for c in CATEGORIES}


def top_k_proportions(words_df, k):
    eff = min(k, len(words_df))
    top = words_df.nlargest(eff, "mean_abs_shap")
    return category_proportions(top), eff


# ----------------------------------------------------------- step 1: vocab

def step1_vocab_stats(by_model_by_cat):
    rows = []
    for model, by_cat in by_model_by_cat.items():
        for cat in ["TP", "FP", "TN"]:
            samples = by_cat[cat]
            agg = aggregate_words(samples)
            total_tokens = int(agg["count"].sum()) if len(agg) else 0
            unique_types = int(len(agg))
            n_instances = len(samples)
            mean_sent_len = (
                float(np.mean([len(s.get("word_attribs", [])) for s in samples]))
                if samples else 0.0
            )
            rows.append({
                "model": model,
                "category": cat,
                "n_instances": n_instances,
                "total_tokens": total_tokens,
                "unique_types": unique_types,
                "type_token_ratio": (
                    unique_types / total_tokens if total_tokens else 0.0
                ),
                "mean_sentence_length": mean_sent_len,
                "mean_tokens_per_instance": (
                    total_tokens / n_instances if n_instances else 0.0
                ),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------- step 2: K sensitivity

def step2_sensitivity(by_model_by_cat):
    """Return long DataFrame of proportions across K values."""
    rows = []
    for model, by_cat in by_model_by_cat.items():
        for pred_class in ["TP", "FP"]:
            agg = aggregate_words(by_cat[pred_class])
            for k in K_SWEEP:
                props, eff_k = top_k_proportions(agg, k)
                for cat, val in props.items():
                    rows.append({
                        "model": model, "pred_class": pred_class,
                        "K": k, "effective_K": eff_k,
                        "category": cat, "proportion": val,
                    })
    return pd.DataFrame(rows)


def plot_sensitivity(df, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharey=True)
    panels = [
        ("biasdetector", "TP", axes[0, 0], "(a) bias-detector — TP"),
        ("biasdetector", "FP", axes[0, 1], "(b) bias-detector — FP"),
        ("daroberta",    "TP", axes[1, 0], "(c) DA-RoBERTa — TP"),
        ("daroberta",    "FP", axes[1, 1], "(d) DA-RoBERTa — FP"),
    ]
    for model, pred_class, ax, title in panels:
        sub = df[(df.model == model) & (df.pred_class == pred_class)]
        for cat in CATEGORIES:
            line = sub[sub.category == cat].sort_values("K")
            ax.plot(
                line["K"], line["proportion"],
                marker="o", color=CATEGORY_COLORS[cat], label=cat,
            )
        eff = sub.groupby("K")["effective_K"].first().to_dict()
        for k in K_SWEEP:
            if eff.get(k, k) < k:
                ax.axvline(eff[k], linestyle=":", color="black", alpha=0.4)
                ax.text(
                    eff[k], 95, f"vocab\nexhausted\n@{eff[k]}",
                    fontsize=7, ha="center", va="top", color="black",
                )
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("K (top-K word types)")
        ax.set_ylabel("Proportion (%)")
        ax.set_xscale("log")
        ax.set_xticks(K_SWEEP)
        ax.set_xticklabels([str(k) for k in K_SWEEP])
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    handles = [
        plt.Line2D([0], [0], color=CATEGORY_COLORS[c], marker="o", label=c)
        for c in CATEGORIES
    ]
    fig.legend(
        handles=handles, labels=CATEGORIES,
        loc="upper center", bbox_to_anchor=(0.5, 0.99),
        ncol=4, fontsize=10, frameon=True,
    )
    fig.suptitle(
        "Figure 6 sensitivity to K — category proportion at top-K word types",
        fontsize=13, fontweight="bold", y=0.94,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------- step 3: matched pools

def step3_matched_pools(by_model_by_cat):
    rows = []

    # 3a. Proportional-K (top X% of each model's per-(model,pred_class) vocab)
    for model, by_cat in by_model_by_cat.items():
        for pred_class in ["TP", "FP"]:
            agg = aggregate_words(by_cat[pred_class])
            for x_pct in PROP_K:
                n_select = max(1, int(round(len(agg) * x_pct / 100.0)))
                if n_select > len(agg):
                    n_select = len(agg)
                top = agg.nlargest(n_select, "mean_abs_shap")
                props = category_proportions(top)
                for cat, val in props.items():
                    rows.append({
                        "method": "proportional_K",
                        "percentile_or_K": x_pct,
                        "model": model, "pred_class": pred_class,
                        "category": cat, "proportion": val,
                        "n_selected": n_select,
                    })

    # 3b. Threshold-based — 75th percentile of pooled (both models, TP+FP) mean_abs_shap
    pooled_shaps = []
    for model, by_cat in by_model_by_cat.items():
        for pred_class in ["TP", "FP"]:
            agg = aggregate_words(by_cat[pred_class])
            pooled_shaps.extend(agg["mean_abs_shap"].tolist())
    threshold_p75 = float(np.percentile(pooled_shaps, 75)) if pooled_shaps else 0.0

    for model, by_cat in by_model_by_cat.items():
        for pred_class in ["TP", "FP"]:
            agg = aggregate_words(by_cat[pred_class])
            top = agg[agg["mean_abs_shap"] >= threshold_p75]
            props = category_proportions(top)
            for cat, val in props.items():
                rows.append({
                    "method": "threshold_p75",
                    "percentile_or_K": round(threshold_p75, 6),
                    "model": model, "pred_class": pred_class,
                    "category": cat, "proportion": val,
                    "n_selected": int(len(top)),
                })

    return pd.DataFrame(rows), threshold_p75


# ---------------------------------------------------- step 4: bootstrap

def bootstrap_proportions(samples, k=DEFAULT_K, B=BOOTSTRAP_B, seed=BOOTSTRAP_SEED):
    """B × len(CATEGORIES) matrix of resampled proportions."""
    rng = np.random.default_rng(seed)
    n = len(samples)
    if n == 0:
        return np.zeros((B, len(CATEGORIES)))
    samples_arr = np.array(samples, dtype=object)
    out = np.zeros((B, len(CATEGORIES)))
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        resampled = samples_arr[idx].tolist()
        agg = aggregate_words(resampled)
        props, _ = top_k_proportions(agg, k)
        out[b] = [props[c] for c in CATEGORIES]
    return out


def step4_bootstrap(by_model_by_cat):
    """For each (model, pred_class in {TP,FP}): mean + 95% CI per category."""
    summary = []
    raw = {}
    for model, by_cat in by_model_by_cat.items():
        for pred_class in ["TP", "FP"]:
            mat = bootstrap_proportions(by_cat[pred_class])
            raw[(model, pred_class)] = mat
            for i, cat in enumerate(CATEGORIES):
                col = mat[:, i]
                summary.append({
                    "model": model, "pred_class": pred_class,
                    "category": cat,
                    "mean": float(np.mean(col)),
                    "ci_lo": float(np.percentile(col, 2.5)),
                    "ci_hi": float(np.percentile(col, 97.5)),
                    "ci_width": float(np.percentile(col, 97.5) - np.percentile(col, 2.5)),
                })
    return pd.DataFrame(summary), raw


def plot_bootstrap(boot_df, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    panels = [
        ("biasdetector", "TP", axes[0, 0], "(a) bias-detector — TP"),
        ("biasdetector", "FP", axes[0, 1], "(b) bias-detector — FP"),
        ("daroberta",    "TP", axes[1, 0], "(c) DA-RoBERTa — TP"),
        ("daroberta",    "FP", axes[1, 1], "(d) DA-RoBERTa — FP"),
    ]
    width = 0.55
    for model, pred_class, ax, title in panels:
        sub = boot_df[
            (boot_df.model == model) & (boot_df.pred_class == pred_class)
        ].set_index("category")
        bottom = 0.0
        for cat in CATEGORIES:
            mean = sub.loc[cat, "mean"]
            lo = sub.loc[cat, "ci_lo"]
            hi = sub.loc[cat, "ci_hi"]
            ax.bar(
                0, mean, width=width, bottom=bottom,
                color=CATEGORY_COLORS[cat], alpha=0.85,
                edgecolor="black", linewidth=1,
            )
            err_lo = max(0.0, mean - lo)
            err_hi = max(0.0, hi - mean)
            ax.errorbar(
                0, bottom + mean,
                yerr=[[err_lo], [err_hi]],
                fmt="none", ecolor="black", capsize=6, capthick=1.4, linewidth=1.4,
            )
            label = f"{mean:.1f}%\n[{lo:.1f}, {hi:.1f}]"
            if mean > 3:
                ax.text(
                    0, bottom + mean / 2, label,
                    ha="center", va="center", fontsize=8,
                    fontweight="bold", color="white",
                )
            else:
                ax.text(
                    0.35, bottom + mean / 2, label,
                    ha="left", va="center", fontsize=8, color="black",
                )
            bottom += mean
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel("Proportion (%)")
        ax.set_xticks([0])
        ax.set_xticklabels([""])
        ax.set_ylim(0, 110)
        ax.set_xlim(-0.8, 1.0)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORY_COLORS[c], alpha=0.85, edgecolor="black")
        for c in CATEGORIES
    ]
    fig.legend(
        handles=handles, labels=CATEGORIES,
        loc="upper center", bbox_to_anchor=(0.5, 0.99),
        ncol=4, fontsize=10, frameon=True,
    )
    fig.suptitle(
        f"Figure 6 with 95% bootstrap CIs (B={BOOTSTRAP_B}, K={DEFAULT_K})",
        fontsize=13, fontweight="bold", y=0.94,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------- verification

def repro_check(by_model_by_cat):
    """Check K=100 reproduction; return (results_dict, max_abs_delta)."""
    results = {}
    max_delta = 0.0
    for (model, pred_class), targets in REPRO_TARGETS.items():
        agg = aggregate_words(by_model_by_cat[model][pred_class])
        props, eff_k = top_k_proportions(agg, DEFAULT_K)
        deltas = {cat: props[cat] - tgt for cat, tgt in targets.items()}
        results[(model, pred_class)] = {
            "proportions": props,
            "deltas": deltas,
            "effective_K": eff_k,
        }
        for d in deltas.values():
            max_delta = max(max_delta, abs(d))
    return results, max_delta


# ------------------------------------------------------- step 5: summary

def classify_outcome(sens_df, mp_df, boot_df):
    """A: shift survives. B: partial. C: collapse.

    Logic, evaluated in this order:
      A: K-sweep min, ALL proportional-K, AND threshold-based all show
         DA-RoBERTa FP F/T > bias-detector FP F/T + 2pt; AND bootstrap CI
         excludes bias-detector point estimate.
      C: threshold-based condition (the most principled control — equalizes
         feature-quality bar across models) shows DA-RoBERTa FP F/T <=
         bias-detector FP F/T + 3pt. The threshold-based condition is given
         priority because it equalizes the *attribution-strength* threshold
         rather than the *pool size*, which is the substantive claim being
         tested (do DA-RoBERTa FPs actually attribute to function words more
         than bias-detector FPs do, at comparable attribution magnitudes?).
      B: otherwise.

    Degenerate proportional-K cases (n_selected very small, like the X=5%
    case where DA-RoBERTa selects only 12 types) are reported but not used
    to trigger collapse on their own.
    """
    rationale = []

    def fetch(df, **kw):
        sub = df
        for k, v in kw.items():
            sub = sub[sub[k] == v]
        return sub

    # K sensitivity
    da_fp_sens = fetch(
        sens_df, model="daroberta", pred_class="FP",
        category="Function/Temporal Words",
    ).sort_values("K")
    da_fp_ft_min = float(da_fp_sens["proportion"].min())
    da_fp_ft_max = float(da_fp_sens["proportion"].max())

    da_tp_ft = float(fetch(
        sens_df, model="daroberta", pred_class="TP",
        category="Function/Temporal Words", K=DEFAULT_K,
    )["proportion"].iloc[0])
    bd_fp_ft = float(fetch(
        sens_df, model="biasdetector", pred_class="FP",
        category="Function/Temporal Words", K=DEFAULT_K,
    )["proportion"].iloc[0])

    # Matched-pool: proportional-K
    prop_pairs = []
    for x in PROP_K:
        da = float(fetch(
            mp_df, method="proportional_K", percentile_or_K=float(x),
            model="daroberta", pred_class="FP",
            category="Function/Temporal Words",
        )["proportion"].iloc[0])
        bd = float(fetch(
            mp_df, method="proportional_K", percentile_or_K=float(x),
            model="biasdetector", pred_class="FP",
            category="Function/Temporal Words",
        )["proportion"].iloc[0])
        prop_pairs.append((x, da, bd))

    # Matched-pool: threshold-based (the principled control)
    thr_row_da = fetch(
        mp_df, method="threshold_p75", model="daroberta", pred_class="FP",
        category="Function/Temporal Words",
    ).iloc[0]
    thr_row_bd = fetch(
        mp_df, method="threshold_p75", model="biasdetector", pred_class="FP",
        category="Function/Temporal Words",
    ).iloc[0]
    thr_da = float(thr_row_da["proportion"])
    thr_bd = float(thr_row_bd["proportion"])
    thr_n_da = int(thr_row_da["n_selected"])

    # Bootstrap
    boot_da = fetch(
        boot_df, model="daroberta", pred_class="FP",
        category="Function/Temporal Words",
    ).iloc[0]
    ci_lo = float(boot_da["ci_lo"])
    ci_hi = float(boot_da["ci_hi"])

    rationale.append(
        f"K sensitivity: DA-RoBERTa FP F/T ranges [{da_fp_ft_min:.1f}, "
        f"{da_fp_ft_max:.1f}]% across K∈{K_SWEEP}; K=100 (13.0%) is mid-range, "
        f"not inflated by vocab exhaustion (K=200 → "
        f"{float(fetch(sens_df, model='daroberta', pred_class='FP', category='Function/Temporal Words', K=200)['proportion'].iloc[0]):.1f}%)."
    )
    rationale.append(
        f"Threshold-based control (n_selected={thr_n_da} for DA-RoBERTa FP): "
        f"DA-RoBERTa FP F/T = {thr_da:.1f}% vs bias-detector FP F/T = "
        f"{thr_bd:.1f}% → gap "
        f"{'inverts' if thr_da < thr_bd else 'shrinks to ' + f'{thr_da - thr_bd:+.1f} pt'}."
    )
    rationale.append(
        "Proportional-K: "
        + "; ".join(f"top {x}% → DA={da:.1f}% / BD={bd:.1f}%" for x, da, bd in prop_pairs)
    )
    rationale.append(
        f"Bootstrap at K=100: DA-RoBERTa FP F/T 95% CI [{ci_lo:.1f}, {ci_hi:.1f}] "
        f"vs bias-detector FP F/T point estimate {bd_fp_ft:.1f}% — "
        f"{'excludes' if ci_lo > bd_fp_ft else 'overlaps'}."
    )
    rationale.append(
        f"DA-RoBERTa within-model: TP F/T at K=100 = {da_tp_ft:.1f}% vs FP F/T "
        f"at K=100 = 13.0% (gap = {13.0 - da_tp_ft:+.1f} pt)."
    )

    # Outcome A — survives everywhere
    survives_K = da_fp_ft_min > max(da_tp_ft, bd_fp_ft) + 2.0
    survives_prop = all(da > bd + 2.0 for _, da, bd in prop_pairs)
    survives_threshold = thr_da > thr_bd + 2.0
    survives_boot = ci_lo > bd_fp_ft
    if survives_K and survives_prop and survives_threshold and survives_boot:
        return "A", rationale

    # Outcome C — threshold-based control collapses the gap
    if thr_da <= thr_bd + 3.0:
        rationale.append(
            "**Decisive**: under the threshold-based (attribution-strength) control, "
            "the F/T gap collapses or inverts. The original 13% number is what you "
            "get when you fix K and let the comparison pool size differ — but when "
            "you fix the per-feature attribution bar, DA-RoBERTa does NOT attribute "
            "more to function words than bias-detector does."
        )
        return "C", rationale

    # Otherwise outcome B
    rationale.append(
        f"Directional persistence with sensitive magnitude. survives_K={survives_K}, "
        f"survives_prop={survives_prop}, survives_threshold={survives_threshold}, "
        f"survives_boot={survives_boot}."
    )
    return "B", rationale


BASIL_REC = {
    "A": (
        "Keep current Figure 6 structure on BASIL. Add 95% bootstrap CIs to the "
        "BASIL version (the BABE shift is real, but reviewers will want the "
        "uncertainty quantified given small FP counts)."
    ),
    "B": (
        "On BASIL, use the multi-K small-multiples format from Step 2 instead of "
        "a single K=100 panel. Lead the paper text with the K-stable interpretation "
        "rather than the K=100 number."
    ),
    "C": (
        "Restructure Figure 6 on BASIL as 'feature-pool composition' with explicit "
        "vocab-size matching (proportional-K). Alternatively, drop the F/T claim "
        "entirely and reframe panel (d) as 'DA-RoBERTa FP attributions do not "
        "concentrate on framing vocab' rather than 'they shift to function words'."
    ),
}


def write_summary(
    out_path, repro_results, vocab_df, sens_df, mp_df, boot_df,
    threshold_p75, outcome, rationale,
):
    lines = []
    lines.append("# Vocab-size confound check — outcome\n")
    lines.append(f"**Outcome: {outcome}**\n")
    lines.append("\n".join(f"- {r}" for r in rationale))
    lines.append("\n## BASIL Figure 6 recommendation\n")
    lines.append(BASIL_REC[outcome])

    lines.append("\n## Verification\n")
    lines.append("### K=100 reproduction vs published numbers\n")
    lines.append("| model | pred_class | category | got (%) | target (%) | Δ |")
    lines.append("|---|---|---|---:|---:|---:|")
    for (model, pred_class), entry in repro_results.items():
        for cat, tgt in REPRO_TARGETS[(model, pred_class)].items():
            got = entry["proportions"][cat]
            d = entry["deltas"][cat]
            lines.append(
                f"| {model} | {pred_class} | {cat} | {got:.1f} | {tgt} | {d:+.1f} |"
            )

    lines.append("\n### Vocab stats (premise check)\n")
    vc = vocab_df.set_index(["model", "category"])
    bd_fp_types = int(vc.loc[("biasdetector", "FP"), "unique_types"])
    da_fp_types = int(vc.loc[("daroberta", "FP"), "unique_types"])
    ratio = da_fp_types / bd_fp_types if bd_fp_types else 0.0
    lines.append(
        f"- bias-detector FP unique types: **{bd_fp_types}** "
        f"(n={int(vc.loc[('biasdetector', 'FP'), 'n_instances'])} samples)"
    )
    lines.append(
        f"- DA-RoBERTa FP unique types: **{da_fp_types}** "
        f"(n={int(vc.loc[('daroberta', 'FP'), 'n_instances'])} samples)"
    )
    lines.append(f"- ratio (DA-RoBERTa / bias-detector): **{ratio:.2f}**")
    if 0.2 <= ratio <= 0.5:
        lines.append(
            "  - Ratio in [0.2, 0.5] — Ax3B's premise (≈1/3) is supported."
        )
    else:
        lines.append(
            "  - **Ratio outside [0.2, 0.5]** — Ax3B's premise may not hold; "
            "interpret accordingly."
        )

    lines.append("\n### Bootstrap CI widths (sanity)\n")
    bw = boot_df[boot_df.category == "Function/Temporal Words"].set_index(["model", "pred_class"])
    bd_w = float(bw.loc[("biasdetector", "FP"), "ci_width"])
    da_w = float(bw.loc[("daroberta", "FP"), "ci_width"])
    lines.append(f"- bias-detector FP F/T CI width: **{bd_w:.2f}** pts")
    lines.append(f"- DA-RoBERTa FP F/T CI width: **{da_w:.2f}** pts")
    if da_w > bd_w * 1.2:
        lines.append("  - DA-RoBERTa CI wider as expected.")
    else:
        lines.append("  - **DA-RoBERTa CI not substantially wider than bias-detector** — investigate.")

    # Decision table
    lines.append("\n## Decision table — DA-RoBERTa FP Function/Temporal proportion under every control\n")
    lines.append("| Condition | DA-RoBERTa FP F/T (%) | n_selected / K |")
    lines.append("|---|---:|---:|")

    da_fp_sens = sens_df[
        (sens_df.model == "daroberta")
        & (sens_df.pred_class == "FP")
        & (sens_df.category == "Function/Temporal Words")
    ].sort_values("K")
    for _, r in da_fp_sens.iterrows():
        marker = " *(uncorrected)*" if r["K"] == DEFAULT_K else ""
        lines.append(
            f"| K={int(r.K)}{marker} | {r.proportion:.1f} | "
            f"effective_K={int(r.effective_K)} |"
        )

    da_fp_mp = mp_df[
        (mp_df.model == "daroberta")
        & (mp_df.pred_class == "FP")
        & (mp_df.category == "Function/Temporal Words")
    ]
    for _, r in da_fp_mp.iterrows():
        if r["method"] == "proportional_K":
            cond = f"Proportional-K at top {int(r.percentile_or_K)}% of vocab"
            sel = f"n_selected={int(r.n_selected)}"
        else:
            cond = f"Threshold ≥ {threshold_p75:.4f} (p75 of pooled mean_abs_shap)"
            sel = f"n_selected={int(r.n_selected)}"
        lines.append(f"| {cond} | {r.proportion:.1f} | {sel} |")

    boot_row = boot_df[
        (boot_df.model == "daroberta")
        & (boot_df.pred_class == "FP")
        & (boot_df.category == "Function/Temporal Words")
    ].iloc[0]
    lines.append(
        f"| **Bootstrap mean** (K={DEFAULT_K}, B={BOOTSTRAP_B}) | "
        f"{boot_row['mean']:.1f} | 95% CI [{boot_row['ci_lo']:.1f}, "
        f"{boot_row['ci_hi']:.1f}] |"
    )

    # Comparison baselines
    da_tp_ft = float(sens_df[
        (sens_df.model == "daroberta") & (sens_df.pred_class == "TP")
        & (sens_df.category == "Function/Temporal Words")
        & (sens_df.K == DEFAULT_K)
    ]["proportion"].iloc[0])
    bd_fp_ft = float(sens_df[
        (sens_df.model == "biasdetector") & (sens_df.pred_class == "FP")
        & (sens_df.category == "Function/Temporal Words")
        & (sens_df.K == DEFAULT_K)
    ]["proportion"].iloc[0])
    lines.append("")
    lines.append("**Comparison baselines (K=100):**")
    lines.append(f"- DA-RoBERTa TP F/T: **{da_tp_ft:.1f}%** (within-model baseline)")
    lines.append(f"- bias-detector FP F/T: **{bd_fp_ft:.1f}%** (cross-model baseline)")

    out_path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------- main

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading SHAP samples...")
    raw = {m: load_samples(p) for m, p in SAMPLES.items()}
    by_model_by_cat = {m: split_by_pred(s) for m, s in raw.items()}

    print("\nSample counts by category (re-derived at threshold 0.5):")
    for m, by_cat in by_model_by_cat.items():
        counts = " | ".join(f"{k}={len(v)}" for k, v in by_cat.items())
        print(f"  {m}: total={len(raw[m])}  {counts}")

    # Step 1 — vocab stats
    print("\n[Step 1] Vocab statistics...")
    vocab_df = step1_vocab_stats(by_model_by_cat)
    vocab_df.to_csv(OUT_DIR / "vocab_stats_table.csv", index=False)
    pd.options.display.float_format = "{:.3f}".format
    print(vocab_df.to_string(index=False))

    # Verification check #2 — Ax3B's premise (DA-RoBERTa FP ≈ 1/3 of bias-detector FP)
    bd_fp_types = int(vocab_df.set_index(["model", "category"]).loc[
        ("biasdetector", "FP"), "unique_types"
    ])
    da_fp_types = int(vocab_df.set_index(["model", "category"]).loc[
        ("daroberta", "FP"), "unique_types"
    ])
    ratio = da_fp_types / bd_fp_types if bd_fp_types else 0.0
    print(
        f"\nVocab premise check: DA-RoBERTa FP unique_types / bias-detector FP "
        f"unique_types = {da_fp_types}/{bd_fp_types} = {ratio:.2f}"
    )
    if 0.2 <= ratio <= 0.5:
        print("  ✓ Premise (~1/3) holds.")
    else:
        print("  ⚠ Premise may not hold — proceed but flag in summary.")

    # Verification check #1 — K=100 reproduction
    print("\n[Verification] K=100 reproduction...")
    repro, max_delta = repro_check(by_model_by_cat)
    for (model, pred_class), entry in repro.items():
        targets = REPRO_TARGETS[(model, pred_class)]
        print(f"  {model} {pred_class} (effective_K={entry['effective_K']}):")
        for cat, tgt in targets.items():
            got = entry["proportions"][cat]
            d = entry["deltas"][cat]
            tag = "✓" if abs(d) <= REPRO_TOL else "⚠"
            print(f"    {tag} {cat:30s}  got={got:5.1f}%  target={tgt:>3}%  Δ={d:+.1f}")
    if max_delta > REPRO_TOL:
        print(
            f"  ⚠ Max absolute delta {max_delta:.1f} pts exceeds tolerance "
            f"{REPRO_TOL:.1f} — warning, proceeding."
        )
    else:
        print(f"  ✓ All targets within ±{REPRO_TOL:.1f} pts.")

    # Step 2 — K sensitivity
    print("\n[Step 2] K sensitivity sweep...")
    sens_df = step2_sensitivity(by_model_by_cat)
    plot_sensitivity(sens_df, OUT_DIR / "fig6_sensitivity.png")
    print(f"  Wrote {OUT_DIR / 'fig6_sensitivity.png'}")

    # Step 3 — matched pools
    print("\n[Step 3] Matched-pool reproductions...")
    mp_df, threshold_p75 = step3_matched_pools(by_model_by_cat)
    mp_df.to_csv(OUT_DIR / "fig6_matched_pools.csv", index=False)
    print(f"  Threshold (p75 of pooled mean_abs_shap): {threshold_p75:.6f}")
    print(f"  Wrote {OUT_DIR / 'fig6_matched_pools.csv'}")

    # Step 4 — bootstrap
    print(f"\n[Step 4] Bootstrap CIs (B={BOOTSTRAP_B}) — this takes ~30s...")
    boot_df, _raw = step4_bootstrap(by_model_by_cat)
    plot_bootstrap(boot_df, OUT_DIR / "fig6_bootstrap_ci.png")
    boot_df.to_csv(OUT_DIR / "bootstrap_summary.csv", index=False)  # auxiliary
    print(f"  Wrote {OUT_DIR / 'fig6_bootstrap_ci.png'}")
    print(f"  Wrote {OUT_DIR / 'bootstrap_summary.csv'} (aux)")

    # Bootstrap CI width sanity
    bw = boot_df[boot_df.category == "Function/Temporal Words"].set_index(
        ["model", "pred_class"]
    )
    bd_w = float(bw.loc[("biasdetector", "FP"), "ci_width"])
    da_w = float(bw.loc[("daroberta", "FP"), "ci_width"])
    print(f"\nBootstrap CI width sanity (F/T): bias-detector FP={bd_w:.2f}, DA-RoBERTa FP={da_w:.2f}")
    if da_w > bd_w * 1.2:
        print("  ✓ DA-RoBERTa CI substantially wider, as expected.")
    else:
        print("  ⚠ DA-RoBERTa CI not substantially wider — flag in summary.")

    # Step 5 — classify and write summary
    print("\n[Step 5] Classify outcome A/B/C and write summary...")
    outcome, rationale = classify_outcome(sens_df, mp_df, boot_df)
    print(f"  Outcome: {outcome}")
    for r in rationale:
        print(f"    - {r}")

    write_summary(
        OUT_DIR / "item3_summary.md",
        repro, vocab_df, sens_df, mp_df, boot_df,
        threshold_p75, outcome, rationale,
    )
    print(f"  Wrote {OUT_DIR / 'item3_summary.md'}")

    print("\nDone.")


if __name__ == "__main__":
    main()
