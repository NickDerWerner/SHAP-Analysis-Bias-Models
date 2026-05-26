"""Extract FP-paragraph numbers for bias-detector and DA-RoBERTa SHAP analyses.

Produces:
- Top words by mean |SHAP| over FPs (with sign direction)
- Mean confidence on FPs
- Mean |SHAP| per instance on FPs
- TP vs FP comparison for the headline word ("illegal" for bd, "claims" stem for dr)
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

MODELS = [
    ("bias-detector (current 337)", OUTPUTS / "shap_samples.jsonl", "illegal"),
    ("bias-detector (legacy 237)", OUTPUTS / "shap_samples237.jsonl", "illegal"),
    ("DA-RoBERTa-BABE-FT", OUTPUTS / "shap_samples_daroberta.jsonl", "claims"),
]


def normalize(w: str) -> str:
    # strip surrounding punctuation/whitespace, lowercase
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def filter_subset(rows, gold, pred):
    return [r for r in rows if r.get("gold") == gold and r.get("pred") == pred]


def aggregate_word_stats(rows, top_n=8):
    """For each word (normalized), accumulate (|shap|, signed shap) across rows.

    Returns list sorted by mean |SHAP| desc, with: (word, n_occurrences, mean_abs_shap, mean_signed_shap, direction)
    """
    bag = defaultdict(list)  # word -> list of signed shap values
    for r in rows:
        for wa in r.get("word_attribs", []):
            w = normalize(wa["word"])
            if not w:
                continue
            bag[w].append(wa["shap"])
    results = []
    for w, vals in bag.items():
        n = len(vals)
        mean_abs = mean(abs(v) for v in vals)
        mean_signed = mean(vals)
        direction = "+ (toward biased)" if mean_signed > 0 else "- (toward non-biased)"
        results.append((w, n, mean_abs, mean_signed, direction))
    # rank by mean |SHAP|, tiebreak on count
    results.sort(key=lambda t: (t[2], t[1]), reverse=True)
    return results[:top_n]


def per_instance_mean_abs_shap(rows):
    """Mean over instances of (mean |SHAP| across that instance's words)."""
    vals = []
    for r in rows:
        ws = [abs(wa["shap"]) for wa in r.get("word_attribs", [])]
        if ws:
            vals.append(mean(ws))
    return mean(vals) if vals else float("nan")


def pooled_mean_abs_shap(rows):
    """Mean |SHAP| across ALL word-attribs pooled (no per-instance averaging)."""
    vals = []
    for r in rows:
        for wa in r.get("word_attribs", []):
            vals.append(abs(wa["shap"]))
    return mean(vals) if vals else float("nan")


def mean_confidence(rows):
    """For pred=1 rows, prob_pos IS the confidence."""
    confs = [r["prob_pos"] for r in rows if "prob_pos" in r]
    return mean(confs) if confs else float("nan")


def word_in_tps_vs_fps(rows_tp, rows_fp, target_stem):
    """Mean |SHAP| of any word whose normalized form starts with target_stem, in TPs vs FPs."""
    def gather(rows):
        vals = []
        per_instance_present = 0
        for r in rows:
            instance_vals = []
            for wa in r.get("word_attribs", []):
                w = normalize(wa["word"])
                if w.startswith(target_stem):
                    instance_vals.append(abs(wa["shap"]))
            if instance_vals:
                per_instance_present += 1
                vals.extend(instance_vals)
        return vals, per_instance_present

    tp_vals, tp_n = gather(rows_tp)
    fp_vals, fp_n = gather(rows_fp)
    return {
        "tp_mean_abs": mean(tp_vals) if tp_vals else float("nan"),
        "tp_occurrences": len(tp_vals),
        "tp_instances_with_word": tp_n,
        "fp_mean_abs": mean(fp_vals) if fp_vals else float("nan"),
        "fp_occurrences": len(fp_vals),
        "fp_instances_with_word": fp_n,
    }


def main():
    out_lines = []
    for name, path, stem in MODELS:
        rows = load(path)
        fps = filter_subset(rows, gold=0, pred=1)
        tps = filter_subset(rows, gold=1, pred=1)
        out_lines.append(f"\n=== {name} ({path.name}) ===")
        out_lines.append(f"  Total rows: {len(rows)}")
        out_lines.append(f"  FPs (gold=0, pred=1): {len(fps)}")
        out_lines.append(f"  TPs (gold=1, pred=1): {len(tps)}")

        out_lines.append(f"\n  Mean confidence on FPs: {mean_confidence(fps):.4f}")
        out_lines.append(f"  Mean confidence on TPs: {mean_confidence(tps):.4f}")

        out_lines.append(f"\n  Mean |SHAP| per FP instance (instance-avg): {per_instance_mean_abs_shap(fps):.4f}")
        out_lines.append(f"  Mean |SHAP| per TP instance (instance-avg): {per_instance_mean_abs_shap(tps):.4f}")
        out_lines.append(f"  Mean |SHAP| pooled across FP word-attribs:  {pooled_mean_abs_shap(fps):.4f}")
        out_lines.append(f"  Mean |SHAP| pooled across TP word-attribs:  {pooled_mean_abs_shap(tps):.4f}")

        out_lines.append(f"\n  Top words by mean |SHAP| across FPs (any frequency):")
        out_lines.append(f"    {'word':<20} {'n':>5} {'mean|SHAP|':>12} {'mean signed':>13}  direction")
        for w, n, ma, ms, d in aggregate_word_stats(fps, top_n=8):
            out_lines.append(f"    {w:<20} {n:>5} {ma:>12.4f} {ms:>13.4f}  {d}")

        out_lines.append(f"\n  Top RECURRING words across FPs (count ≥ 2):")
        out_lines.append(f"    {'word':<20} {'n':>5} {'mean|SHAP|':>12} {'mean signed':>13}  direction")
        recurring = [t for t in aggregate_word_stats(fps, top_n=10_000) if t[1] >= 2][:8]
        if recurring:
            for w, n, ma, ms, d in recurring:
                out_lines.append(f"    {w:<20} {n:>5} {ma:>12.4f} {ms:>13.4f}  {d}")
        else:
            out_lines.append("    (none — every top word appears only once in the FP set)")

        out_lines.append(f"\n  '{stem}*' comparison TP vs FP:")
        cmp = word_in_tps_vs_fps(tps, fps, stem)
        out_lines.append(
            f"    TP: mean|SHAP|={cmp['tp_mean_abs']:.4f}  "
            f"occurrences={cmp['tp_occurrences']}  "
            f"instances_with_word={cmp['tp_instances_with_word']}/{len(tps)}"
        )
        out_lines.append(
            f"    FP: mean|SHAP|={cmp['fp_mean_abs']:.4f}  "
            f"occurrences={cmp['fp_occurrences']}  "
            f"instances_with_word={cmp['fp_instances_with_word']}/{len(fps)}"
        )

    print("\n".join(out_lines))


if __name__ == "__main__":
    main()
