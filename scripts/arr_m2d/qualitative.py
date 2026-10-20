"""Task B — reproducible qualitative error analysis + SHAP/gold visualizations."""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2c"))

from offset_alignment import align_record  # noqa: E402
from gold_span_metrics import GoldSpan, char_mask  # noqa: E402

from robustness import load_alignment, load_faithfulness_apos  # noqa: E402

OUT = ROOT / "outputs" / "arr_m2d"
GOLD_SPANS = ROOT / "outputs" / "arr_m1" / "basil_spans" / "gold_spans.csv"
SENT_CSV = ROOT / "basil_sentences.csv"
CACHES = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
}
SEED = 7


def load_gold_by_id() -> Dict[str, List[GoldSpan]]:
    by: Dict[str, List[GoldSpan]] = defaultdict(list)
    with GOLD_SPANS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = f"basil:{row['triplet_uuid']}|{row['outlet_idx']}|{row['sentence_idx']}"
            by[cid].append(
                GoldSpan(int(row["start"]), int(row["end"]), row["bias"], row["span_txt"])
            )
    return by


def load_sentences() -> Dict[str, str]:
    out = {}
    with SENT_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = f"basil:{row['triplet_uuid']}|{row['outlet_idx']}|{row['sentence_idx']}"
            out[cid] = row["text"]
    return out


def load_cache(model: str) -> Dict[str, dict]:
    path = CACHES[model]
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid = f"basil:{r['triplet_uuid']}|{r['outlet_idx']}|{r['sentence_idx']}"
            out[cid] = r
    return out


def pick_examples(align: List[dict], faith: Dict[Tuple[str, str], float]) -> List[dict]:
    """Select a fixed, seeded set of illustrative examples (not a sample for inference)."""
    rng = np.random.default_rng(SEED)
    by_id_model = {(r["canonical_id"], r["model"]): r for r in align}

    # Join BD+DR on shared positives with faithfulness
    shared = []
    for (cid, model), r in by_id_model.items():
        if model != "biasdetector":
            continue
        if r["ann_category"] == "non_biased":
            continue
        if (cid, "daroberta") not in by_id_model:
            continue
        dr = by_id_model[(cid, "daroberta")]
        fb = faith.get((cid, "biasdetector"))
        fd = faith.get((cid, "daroberta"))
        shared.append(
            {
                "cid": cid,
                "bd": r,
                "dr": dr,
                "faith_bd": fb,
                "faith_dr": fd,
                "align_bd": float(r["abs_minus_random_span"])
                if r["abs_minus_random_span"] == r["abs_minus_random_span"]
                else float("nan"),
                "align_dr": float(dr["abs_minus_random_span"])
                if dr["abs_minus_random_span"] == dr["abs_minus_random_span"]
                else float("nan"),
                "cov": float(r["gold_char_coverage"]),
                "cat": r["ann_category"],
            }
        )

    picks: List[dict] = []

    def add(role: str, item: dict, model: str = "biasdetector") -> None:
        r = item["bd"] if model == "biasdetector" else item["dr"]
        picks.append(
            {
                "role": role,
                "canonical_id": item["cid"],
                "model": model,
                "ann_category": item["cat"],
                "pred_type": r["pred_type"],
                "prob_pos": r["prob_pos"],
                "gold_char_coverage": item["cov"],
                "abs_minus_rand": float(r["abs_minus_random_span"])
                if r["abs_minus_random_span"] == r["abs_minus_random_span"]
                else None,
                "abs_mass": float(r["abs_mass_in_gold"]),
                "faith_a_pos_delta": item["faith_bd"] if model == "biasdetector" else item["faith_dr"],
                "paired_align_bd": item["align_bd"],
                "paired_align_dr": item["align_dr"],
            }
        )

    # High faith + high align (need M2B overlap)
    with_faith = [s for s in shared if s["faith_bd"] is not None and s["faith_dr"] is not None]
    hi_faith_hi_align = sorted(
        [s for s in with_faith if s["align_bd"] == s["align_bd"]],
        key=lambda s: (-abs(s["faith_bd"] or 0), -s["align_bd"]),
    )
    for s in hi_faith_hi_align:
        if s["align_bd"] >= 0.15 and abs(s["faith_bd"]) >= 0.25 and s["cat"] == "lex_only":
            add("high_faith_high_align", s)
            break

    # High faith + poor align
    for s in sorted(with_faith, key=lambda s: (-abs(s["faith_bd"] or 0), s["align_bd"] or 99)):
        if s["faith_bd"] is not None and abs(s["faith_bd"]) >= 0.25 and (s["align_bd"] or 0) < 0.02:
            if s["cat"] in ("lex_only", "inf_only"):
                add("high_faith_poor_align", s)
                break

    # Good lexical alignment (DR preferred)
    lex = [s for s in shared if s["cat"] == "lex_only" and s["align_dr"] == s["align_dr"]]
    lex_sorted = sorted(lex, key=lambda s: -s["align_dr"])
    if lex_sorted:
        add("good_lexical_align", lex_sorted[0], model="daroberta")

    # Poor informational alignment with high coverage
    inf = [
        s
        for s in shared
        if s["cat"] == "inf_only" and s["cov"] >= 0.6 and s["align_bd"] == s["align_bd"]
    ]
    inf_sorted = sorted(inf, key=lambda s: s["align_bd"])
    if inf_sorted:
        add("poor_informational_align", inf_sorted[0])

    # BD vs DR disagreement on alignment (largest |Δ|)
    disagree = sorted(
        [s for s in shared if s["align_bd"] == s["align_bd"] and s["align_dr"] == s["align_dr"]],
        key=lambda s: -abs(s["align_dr"] - s["align_bd"]),
    )
    if disagree:
        s = disagree[0]
        add("model_disagreement_bd", s, model="biasdetector")
        add("model_disagreement_dr", s, model="daroberta")

    # Near-full sentence coverage annotations
    high_cov = sorted(
        [s for s in shared if s["cov"] >= 0.85],
        key=lambda s: -s["cov"],
    )
    if high_cov:
        add("near_full_span_coverage", high_cov[0])

    # Ensure uniqueness of roles; fill gaps with deterministic fallbacks
    roles_have = {p["role"] for p in picks}
    needed = [
        "high_faith_high_align",
        "high_faith_poor_align",
        "good_lexical_align",
        "poor_informational_align",
        "near_full_span_coverage",
    ]
    for role in needed:
        if role in roles_have:
            continue
        # fallback: any shared with matching category heuristics
        pool = shared
        if "lexical" in role:
            pool = [s for s in shared if s["cat"] == "lex_only"] or shared
        if "informational" in role or "full_span" in role:
            pool = [s for s in shared if s["cat"] == "inf_only"] or shared
        if not pool:
            continue
        idx = int(rng.integers(0, len(pool)))
        add(role, pool[idx], model="daroberta" if "lexical" in role else "biasdetector")

    return picks


def build_example_records(picks: List[dict]) -> List[dict]:
    gold_by = load_gold_by_id()
    sents = load_sentences()
    caches = {m: load_cache(m) for m in CACHES}
    records = []
    for p in picks:
        cid = p["canonical_id"]
        model = p["model"]
        text = sents[cid]
        spans = gold_by.get(cid, [])
        cache = caches[model][cid]
        al = align_record(text, cache["tokens"], cache["shap_pos"])
        words = [
            {
                "token": w.surface,
                "start": w.start,
                "end": w.end,
                "shap": w.shap,
            }
            for w in al.words
        ]
        records.append(
            {
                **p,
                "sentence_text": text,
                "gold_spans": [
                    {"start": s.start, "end": s.end, "bias": s.bias, "txt": s.txt} for s in spans
                ],
                "words": words,
                "gold_label": int(cache.get("gold", cache.get("label", 1))),
                "pred": int(cache.get("pred", round(float(p["prob_pos"])))),
            }
        )
    return records


def render_example_figure(rec: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    text = rec["sentence_text"]
    words = rec["words"]
    spans = rec["gold_spans"]
    n = len(text)
    gold = np.zeros(n, dtype=bool)
    for sp in spans:
        gold[sp["start"] : sp["end"]] = True

    # char-level shap via words
    shap_c = np.zeros(n, dtype=float)
    for w in words:
        if w["end"] > w["start"]:
            shap_c[w["start"] : w["end"]] = w["shap"]

    fig, ax = plt.subplots(figsize=(11, 2.8))
    ax.set_xlim(0, max(n, 1))
    ax.set_ylim(0, 3)
    ax.axis("off")
    title = (
        f"{rec['role']} · {rec['model']} · {rec['ann_category']} · "
        f"{rec['pred_type']} · P={float(rec['prob_pos']):.2f} · "
        f"excess={rec['abs_minus_rand']}"
    )
    ax.set_title(title, fontsize=9, loc="left")

    # Gold band
    ax.text(0, 2.6, "BASIL gold", fontsize=8, color="#333")
    y_g = 2.2
    for i in range(n):
        if gold[i]:
            ax.add_patch(
                FancyBboxPatch(
                    (i, y_g),
                    1,
                    0.35,
                    boxstyle="square,pad=0",
                    linewidth=0,
                    facecolor="#f1c40f",
                    alpha=0.85,
                )
            )
    # SHAP heat
    ax.text(0, 1.5, "SHAP (signed)", fontsize=8, color="#333")
    vmax = max(abs(float(w["shap"])) for w in words) or 1.0
    y_s = 1.1
    for w in words:
        s = float(w["shap"])
        if s >= 0:
            color = (0.8, 0.1, 0.1, min(0.95, 0.15 + 0.85 * s / vmax))
        else:
            color = (0.1, 0.3, 0.8, min(0.95, 0.15 + 0.85 * (-s) / vmax))
        ax.add_patch(
            FancyBboxPatch(
                (w["start"], y_s),
                max(w["end"] - w["start"], 1),
                0.35,
                boxstyle="square,pad=0",
                linewidth=0,
                facecolor=color,
            )
        )

    # Wrapped text preview
    preview = text if len(text) <= 140 else text[:137] + "..."
    ax.text(0, 0.35, preview, fontsize=8, family="monospace", wrap=True)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def write_examples_html(records: List[dict], path: Path) -> None:
    blocks = []
    for rec in records:
        spans_html = ", ".join(
            f"[{s['bias']}] “{s['txt'][:60]}” [{s['start']}:{s['end']}]" for s in rec["gold_spans"]
        )
        # top words by |shap|
        top = sorted(rec["words"], key=lambda w: abs(w["shap"]), reverse=True)[:8]
        top_s = ", ".join(f"{w['token']}({w['shap']:+.3f})" for w in top)
        blocks.append(
            f"""
<section>
<h2>{rec['role']}</h2>
<p><b>id</b> {rec['canonical_id']} · <b>model</b> {rec['model']} ·
<b>cat</b> {rec['ann_category']} · <b>pred</b> {rec['pred_type']} ·
<b>P</b> {float(rec['prob_pos']):.3f} · <b>coverage</b> {float(rec['gold_char_coverage']):.2f} ·
<b>excess</b> {rec['abs_minus_rand']} · <b>A_pos ΔP</b> {rec['faith_a_pos_delta']}</p>
<pre style="white-space:pre-wrap;background:#f7f7f5;padding:0.75rem;">{rec['sentence_text']}</pre>
<p><b>Gold spans:</b> {spans_html or '(none)'}</p>
<p><b>Top |SHAP| words:</b> {top_s}</p>
<p><img src="figures/examples/{rec['role']}_{rec['model']}.png" alt="{rec['role']}" style="max-width:100%"/></p>
</section>
"""
        )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>M2D Qualitative Examples</title>
<style>body{{font-family:Georgia,serif;max-width:900px;margin:1.5rem auto;line-height:1.4}}
section{{border-top:1px solid #ccc;padding:1rem 0}}</style></head>
<body>
<h1>M2D qualitative examples</h1>
<p>Illustrative only — not a representative quantitative sample. Seed={SEED}.</p>
{''.join(blocks)}
</body></html>"""
    path.write_text(html, encoding="utf-8")


def run_qualitative() -> List[dict]:
    align = load_alignment()
    faith = load_faithfulness_apos()
    picks = pick_examples(align, faith)
    records = build_example_records(picks)
    fig_dir = OUT / "figures" / "examples"
    fig_dir.mkdir(parents=True, exist_ok=True)
    for rec in records:
        render_example_figure(rec, fig_dir / f"{rec['role']}_{rec['model']}.png")
    # JSON dump (full detail)
    serializable = []
    for rec in records:
        serializable.append(
            {
                k: v
                for k, v in rec.items()
                if k != "words" or True  # keep words
            }
        )
    (OUT / "qualitative_examples.json").write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # flat CSV without full word list
    flat = []
    for rec in records:
        flat.append(
            {
                "role": rec["role"],
                "canonical_id": rec["canonical_id"],
                "model": rec["model"],
                "ann_category": rec["ann_category"],
                "pred_type": rec["pred_type"],
                "prob_pos": rec["prob_pos"],
                "gold_char_coverage": rec["gold_char_coverage"],
                "abs_minus_rand": rec["abs_minus_rand"],
                "abs_mass": rec["abs_mass"],
                "faith_a_pos_delta": rec["faith_a_pos_delta"],
                "paired_align_bd": rec.get("paired_align_bd"),
                "paired_align_dr": rec.get("paired_align_dr"),
                "sentence_text": rec["sentence_text"],
                "gold_spans_json": json.dumps(rec["gold_spans"], ensure_ascii=False),
                "top_shap_json": json.dumps(
                    sorted(rec["words"], key=lambda w: abs(w["shap"]), reverse=True)[:10],
                    ensure_ascii=False,
                ),
            }
        )
    from robustness import write_csv

    write_csv(OUT / "qualitative_examples.csv", flat)
    write_examples_html(records, OUT / "qualitative_examples.html")
    return flat
