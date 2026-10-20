#!/usr/bin/env python3
"""ARR M1 Task C — DeBERTa attribution integrity (read-only on original caches)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from word_aggregation import (  # noqa: E402
    SPECIAL,
    alignment_ok,
    mass_diagnostics,
    reaggregate_additive,
    reaggregate_charspan,
)

OUT = ROOT / "outputs" / "arr_m1" / "deberta_integrity"

TARGETS = [
    ("babe_deberta", ROOT / "outputs" / "shap_samples_deberta.jsonl"),
    ("babe_deberta_bak", ROOT / "outputs" / "shap_samples_deberta.jsonl.bak"),
    ("basil_deberta", ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl"),
    ("babe_bd", ROOT / "outputs" / "shap_samples.jsonl"),
    ("babe_dr", ROOT / "outputs" / "shap_samples_daroberta.jsonl"),
]


def load_jsonl(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def analyze(name: str, path: Path) -> Dict:
    if not path.exists():
        return {"name": name, "missing": True}
    rows = load_jsonl(path)
    drop_fracs = []
    additive_resids = []
    align_char = 0
    align_add = 0
    match_stored_char = 0
    n = 0
    per_row = []

    for i, r in enumerate(rows):
        tokens = r["tokens"]
        shap = r["shap_pos"]
        stored = r.get("word_attribs") or []
        diag = mass_diagnostics(tokens, shap)
        drop_fracs.append(diag["charspan_drop_frac"])
        additive_resids.append(abs(diag["additive_residual"]))

        cs = reaggregate_charspan(tokens, shap)
        ad, meta = reaggregate_additive(tokens, shap)
        if alignment_ok(r["text"], cs):
            align_char += 1
        if alignment_ok(r["text"], ad):
            align_add += 1

        # Does stored match charspan (post-fix DeBERTa) or something else?
        if len(cs) == len(stored) and all(
            abs(a["shap"] - b["shap"]) < 1e-9 and a["word"] == b["word"]
            for a, b in zip(cs, stored)
        ):
            match_stored_char += 1

        n += 1
        if i < 5 or diag["charspan_drop_frac"] > 0.4:
            per_row.append(
                {
                    "name": name,
                    "index": i,
                    "n_tokens": len(tokens),
                    "n_words_stored": len(stored),
                    "n_words_charspan": int(diag["n_words_charspan"]),
                    "n_words_additive": int(diag["n_words_additive"]),
                    "token_sum": diag["token_sum"],
                    "charspan_word_sum": diag["charspan_word_sum"],
                    "charspan_space_mass": diag["charspan_space_mass"],
                    "charspan_drop_frac": diag["charspan_drop_frac"],
                    "additive_word_sum": diag["additive_word_sum"],
                    "additive_whitespace_shap": diag["additive_whitespace_shap"],
                    "additive_residual": diag["additive_residual"],
                    "text_preview": r["text"][:120],
                }
            )

    drop_fracs.sort()
    def pct(xs, p):
        if not xs:
            return float("nan")
        return xs[min(len(xs) - 1, int(p * (len(xs) - 1)))]

    summary = {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "n_records": n,
        "mean_charspan_drop_frac": sum(drop_fracs) / n if n else float("nan"),
        "median_charspan_drop_frac": pct(drop_fracs, 0.5),
        "p90_charspan_drop_frac": pct(drop_fracs, 0.9),
        "max_additive_residual": max(additive_resids) if additive_resids else float("nan"),
        "align_ok_charspan": align_char,
        "align_ok_additive": align_add,
        "stored_matches_charspan": match_stored_char,
        "interpretation": (
            "Whitespace mass under charspan is attribution assigned to space "
            "characters when token SHAP is spread across the token string; "
            "it is not deletion of non-space token content. Additive method "
            "keeps full token SHAP on word surfaces."
        ),
    }

    # Write derived additive word_attribs for deberta only (new file, no overwrite)
    if name in ("babe_deberta", "basil_deberta"):
        out_path = OUT / f"{name}_word_attribs_additive.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                ad, meta = reaggregate_additive(r["tokens"], r["shap_pos"])
                rec = {
                    "text": r["text"],
                    "gold": r["gold"],
                    "pred": r["pred"],
                    "prob_pos": r["prob_pos"],
                    "word_attribs_charspan_equiv": r.get("word_attribs"),
                    "word_attribs_additive": ad,
                    "mass_meta": meta,
                }
                if "triplet_uuid" in r:
                    rec["triplet_uuid"] = r["triplet_uuid"]
                    rec["outlet_idx"] = r["outlet_idx"]
                    rec["sentence_idx"] = r["sentence_idx"]
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        summary["derived_additive_path"] = str(out_path.relative_to(ROOT))

    return summary, per_row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    details = []
    for name, path in TARGETS:
        result = analyze(name, path)
        if isinstance(result, dict) and result.get("missing"):
            summaries.append(result)
            continue
        summary, per_row = result
        summaries.append(summary)
        details.extend(per_row)

    fields = list(summaries[0].keys()) if summaries else []
    with (OUT / "integrity_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(summaries)

    if details:
        with (OUT / "integrity_examples.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(details[0].keys()))
            w.writeheader()
            w.writerows(details)

    (OUT / "run_meta.json").write_text(
        json.dumps({"summaries": summaries}, indent=2, default=str), encoding="utf-8"
    )
    print("[deberta_integrity] wrote", OUT)
    for s in summaries:
        if s.get("missing"):
            print("  MISSING", s["name"])
        else:
            print(
                f"  {s['name']}: drop_median={s['median_charspan_drop_frac']:.3f} "
                f"stored≡charspan={s['stored_matches_charspan']}/{s['n_records']} "
                f"align_char={s['align_ok_charspan']}"
            )


if __name__ == "__main__":
    main()
