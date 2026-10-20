#!/usr/bin/env python3
"""ARR M1 Task A — taxonomy audit with Other/Unassigned (read-only on originals)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from taxonomy import (  # noqa: E402
    CATEGORIES_LEGACY,
    CATEGORIES_V2,
    categorize_word_legacy,
    categorize_word_v2,
    categorize_with_rule,
    normalize_word,
)

OUT = ROOT / "outputs" / "arr_m1" / "taxonomy"
SEED = 7

BABE_CACHES = {
    "biasdetector": ROOT / "outputs" / "shap_samples.jsonl",
    "daroberta": ROOT / "outputs" / "shap_samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "shap_samples_deberta.jsonl",
}
BASIL_CACHES = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl",
}


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def bootstrap_ci(values: List[float], n_boot: int = 1000, seed: int = SEED) -> Tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    return sum(values) / n, lo, hi


def aggregate_word_types(records: List[dict]) -> Dict[str, Dict[str, float]]:
    """word -> {sum_abs, count}"""
    bag: Dict[str, List[float]] = defaultdict(list)
    for r in records:
        for wa in r.get("word_attribs", []):
            w = normalize_word(wa["word"])
            if not w:
                continue
            bag[w].append(abs(float(wa["shap"])))
    return {
        w: {"mean_abs_shap": sum(v) / len(v), "count": float(len(v)), "sum_abs": sum(v)}
        for w, v in bag.items()
    }


def p75_threshold(type_stats: Dict[str, Dict[str, float]]) -> float:
    vals = [d["mean_abs_shap"] for d in type_stats.values()]
    if not vals:
        return 0.0
    vals_sorted = sorted(vals)
    idx = int(math.ceil(0.75 * len(vals_sorted))) - 1
    idx = max(0, min(idx, len(vals_sorted) - 1))
    return vals_sorted[idx]


def dist_from_tokens(
    tokens: List[Tuple[str, float]], scheme: str
) -> Dict[str, Any]:
    """tokens: list of (word, abs_shap_weight_for_attribution)."""
    cats = CATEGORIES_V2 if scheme == "v2" else CATEGORIES_LEGACY
    fn = categorize_word_v2 if scheme == "v2" else categorize_word_legacy
    counts = {c: 0 for c in cats}
    weights = {c: 0.0 for c in cats}
    for w, abs_s in tokens:
        c = fn(w)
        counts[c] += 1
        weights[c] += abs_s
    n = len(tokens)
    tw = sum(weights.values()) or 1.0
    return {
        "n_tokens": n,
        "count": counts,
        "count_pct": {c: (100.0 * counts[c] / n if n else 0.0) for c in cats},
        "weight": weights,
        "weight_pct": {c: (100.0 * weights[c] / tw if tw else 0.0) for c in cats},
    }


def instance_level_other_frac(records: List[dict]) -> List[float]:
    """Per-instance fraction of word_attribs labeled Other under v2 (count)."""
    out = []
    for r in records:
        was = r.get("word_attribs", [])
        if not was:
            continue
        n_other = sum(
            1 for wa in was if categorize_word_v2(wa["word"]) == "Other/Unassigned"
        )
        out.append(n_other / len(was))
    return out


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def audit_corpus(name: str, caches: Dict[str, Path]) -> List[dict]:
    summary_rows = []
    detail_token_rows = []

    for model, path in caches.items():
        records = load_jsonl(path)
        # --- all attributed word occurrences ---
        occ: List[Tuple[str, float]] = []
        for r in records:
            for wa in r.get("word_attribs", []):
                w = normalize_word(wa["word"])
                if w:
                    occ.append((w, abs(float(wa["shap"]))))

        type_stats = aggregate_word_types(records)
        thr = p75_threshold(type_stats)
        selected = [
            (w, d["mean_abs_shap"])
            for w, d in type_stats.items()
            if d["mean_abs_shap"] >= thr
        ]
        # weight selected types by mean_abs (type-level) for attribution-weighted
        selected_occ_weight = [(w, mean) for w, mean in selected]

        for scheme in ("legacy", "v2"):
            for pool_name, pool in (
                ("all_occurrences", occ),
                ("p75_word_types", selected_occ_weight),
            ):
                d = dist_from_tokens(pool, scheme)
                cats = CATEGORIES_V2 if scheme == "v2" else CATEGORIES_LEGACY
                row = {
                    "corpus": name,
                    "model": model,
                    "scheme": scheme,
                    "pool": pool_name,
                    "n_records": len(records),
                    "n_units": d["n_tokens"],
                    "p75_threshold": thr if pool_name.startswith("p75") else "",
                }
                for c in cats:
                    row[f"count_pct__{c}"] = round(d["count_pct"][c], 4)
                    row[f"weight_pct__{c}"] = round(d["weight_pct"][c], 4)
                    row[f"count__{c}"] = d["count"][c]
                summary_rows.append(row)

        # instance-level Other CI
        other_fracs = instance_level_other_frac(records)
        mean, lo, hi = bootstrap_ci(other_fracs)
        summary_rows.append(
            {
                "corpus": name,
                "model": model,
                "scheme": "v2",
                "pool": "instance_other_frac_mean",
                "n_records": len(records),
                "n_units": len(other_fracs),
                "p75_threshold": "",
                "count_pct__Other/Unassigned": round(100.0 * mean, 4),
                "weight_pct__Other/Unassigned": "",
                "ci95_lo": round(100.0 * lo, 4),
                "ci95_hi": round(100.0 * hi, 4),
            }
        )

        # per-type detail for p75 under v2
        for w, mean_abs in sorted(selected, key=lambda x: -x[1]):
            cat, rule = categorize_with_rule(w)
            legacy = categorize_word_legacy(w)
            detail_token_rows.append(
                {
                    "corpus": name,
                    "model": model,
                    "word": w,
                    "mean_abs_shap": mean_abs,
                    "count": type_stats[w]["count"],
                    "category_v2": cat,
                    "rule": rule,
                    "category_legacy": legacy,
                    "selected_p75": 1,
                }
            )

    return summary_rows, detail_token_rows


def build_validation_sample(
    caches: Dict[str, Path], n_per_bucket: int = 20
) -> List[dict]:
    """Stratified sample of word types for manual review."""
    rng = random.Random(SEED)
    # pool from BABE biasdetector + daroberta top types
    type_bag: Dict[str, Dict[str, Any]] = {}
    for model, path in caches.items():
        stats = aggregate_word_types(load_jsonl(path))
        for w, d in stats.items():
            if w not in type_bag or d["mean_abs_shap"] > type_bag[w]["mean_abs_shap"]:
                type_bag[w] = {
                    "word": w,
                    "mean_abs_shap": d["mean_abs_shap"],
                    "count": d["count"],
                    "example_model": model,
                }

    by_cat: Dict[str, List[dict]] = defaultdict(list)
    for w, meta in type_bag.items():
        cat, rule = categorize_with_rule(w)
        by_cat[cat].append({**meta, "category_v2": cat, "rule": rule,
                            "category_legacy": categorize_word_legacy(w)})

    sample = []
    for cat in CATEGORIES_V2:
        pool = by_cat.get(cat, [])
        pool.sort(key=lambda x: -x["mean_abs_shap"])
        # take top half + random from rest for diversity
        top = pool[: max(n_per_bucket // 2, 1)]
        rest = pool[len(top) :]
        rng.shuffle(rest)
        chosen = top + rest[: max(0, n_per_bucket - len(top))]
        for i, row in enumerate(chosen):
            sample.append(
                {
                    "sample_id": f"{cat[:3]}_{i:03d}",
                    "word": row["word"],
                    "category_v2": row["category_v2"],
                    "rule": row["rule"],
                    "category_legacy": row["category_legacy"],
                    "mean_abs_shap": round(row["mean_abs_shap"], 6),
                    "count": int(row["count"]),
                    "example_model": row["example_model"],
                    "manual_category": "",  # blank for annotator
                    "notes": "",
                }
            )
    return sample


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_summary = []
    all_detail = []

    for corpus, caches in (("BABE", BABE_CACHES), ("BASIL", BASIL_CACHES)):
        summary, detail = audit_corpus(corpus, caches)
        all_summary.extend(summary)
        all_detail.extend(detail)

    # unify fieldnames
    keys = []
    seen = set()
    for r in all_summary:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    write_csv(OUT / "category_distributions.csv", all_summary, keys)
    write_csv(
        OUT / "p75_word_type_assignments.csv",
        all_detail,
        [
            "corpus",
            "model",
            "word",
            "mean_abs_shap",
            "count",
            "category_v2",
            "rule",
            "category_legacy",
            "selected_p75",
        ],
    )

    sample = build_validation_sample(BABE_CACHES, n_per_bucket=20)
    write_csv(
        OUT / "manual_validation_sample.csv",
        sample,
        [
            "sample_id",
            "word",
            "category_v2",
            "rule",
            "category_legacy",
            "mean_abs_shap",
            "count",
            "example_model",
            "manual_category",
            "notes",
        ],
    )

    # Compact headline table: p75 v2 vs legacy Em/Eval and Other
    headline = []
    for r in all_summary:
        if r.get("pool") != "p75_word_types":
            continue
        headline.append(
            {
                "corpus": r["corpus"],
                "model": r["model"],
                "scheme": r["scheme"],
                "n_selected_types": r["n_units"],
                "pct_Emotional_count": r.get("count_pct__Emotional/Evaluative", ""),
                "pct_Other_count": r.get("count_pct__Other/Unassigned", ""),
                "pct_Emotional_weight": r.get("weight_pct__Emotional/Evaluative", ""),
                "pct_Other_weight": r.get("weight_pct__Other/Unassigned", ""),
                "pct_Explicit_count": r.get("count_pct__Explicit Bias Terms", ""),
                "pct_Framing_count": r.get("count_pct__Framing/Reporting Verbs", ""),
                "pct_Function_count": r.get("count_pct__Function/Temporal Words", ""),
            }
        )
    write_csv(
        OUT / "headline_p75_comparison.csv",
        headline,
        list(headline[0].keys()) if headline else [],
    )

    # fingerprint
    payload = json.dumps(
        {"seed": SEED, "babe": {k: str(v) for k, v in BABE_CACHES.items()}},
        sort_keys=True,
    )
    (OUT / "run_meta.json").write_text(
        json.dumps(
            {
                "seed": SEED,
                "fingerprint": hashlib.sha256(payload.encode()).hexdigest()[:16],
                "n_summary_rows": len(all_summary),
                "n_validation_sample": len(sample),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[taxonomy] wrote {OUT}")
    print(f"  summary rows={len(all_summary)} validation_sample={len(sample)}")


if __name__ == "__main__":
    main()
