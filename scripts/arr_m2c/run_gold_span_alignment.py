#!/usr/bin/env python3
"""ARR M2C — gold-span SHAP plausibility analysis + human annotation prep.

Uses existing SHAP caches and M1 gold_spans.csv. No new SHAP generation.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from offset_alignment import align_record  # noqa: E402
from gold_span_metrics import (  # noqa: E402
    GoldSpan,
    bootstrap_mean_ci,
    char_mask,
    compute_sentence_metrics,
    positional_control_spans,
    random_length_matched_spans,
    random_word_set_metrics,
    word_in_gold,
)

OUT = ROOT / "outputs" / "arr_m2c"
GOLD_SPANS = ROOT / "outputs" / "arr_m1" / "basil_spans" / "gold_spans.csv"
SENT_CSV = ROOT / "basil_sentences.csv"
CACHES = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl",
}
SEED = 7
N_BASELINE_DRAWS = 20
TOP_K = 5
HUMAN_N = 120


def key_tuple(r) -> Tuple:
    return (str(r["triplet_uuid"]), int(r["outlet_idx"]), int(r["sentence_idx"]))


def sid_from_key(k: Tuple) -> str:
    return f"basil:{k[0]}|{k[1]}|{k[2]}"


def load_jsonl_index(path: Path) -> Dict[Tuple, dict]:
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[key_tuple(r)] = r
    return out


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_gold_by_sentence() -> Dict[Tuple, List[GoldSpan]]:
    by = defaultdict(list)
    with GOLD_SPANS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = (row["triplet_uuid"], int(row["outlet_idx"]), int(row["sentence_idx"]))
            by[k].append(
                GoldSpan(
                    start=int(row["start"]),
                    end=int(row["end"]),
                    bias=row["bias"],
                    txt=row["span_txt"],
                )
            )
    return by


def load_sentences() -> Dict[Tuple, dict]:
    out = {}
    with SENT_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[key_tuple(row)] = row
    return out


def verify_span_offsets(text: str, spans: List[GoldSpan]) -> Tuple[bool, List[str]]:
    problems = []
    for sp in spans:
        if not (0 <= sp.start < sp.end <= len(text)):
            problems.append(f"oob {sp.start}:{sp.end}")
            continue
        frag = text[sp.start : sp.end]
        if frag != sp.txt:
            problems.append(f"mismatch want={sp.txt!r} got={frag!r}")
    return len(problems) == 0, problems


def analyze_model(
    model: str,
    cache: Dict[Tuple, dict],
    gold_by: Dict[Tuple, List[GoldSpan]],
    sents: Dict[Tuple, dict],
    exclusions: List[dict],
) -> List[dict]:
    rows = []
    rng_base = random.Random(SEED)

    for k, rec in cache.items():
        text = rec["text"]
        csv_row = sents.get(k)
        if csv_row is None:
            exclusions.append(
                {"model": model, "canonical_id": sid_from_key(k), "reason": "missing_csv_sentence"}
            )
            continue
        if csv_row["text"] != text:
            exclusions.append(
                {
                    "model": model,
                    "canonical_id": sid_from_key(k),
                    "reason": "text_mismatch_cache_vs_csv",
                }
            )
            continue

        spans = gold_by.get(k, [])
        ok, problems = verify_span_offsets(text, spans)
        if spans and not ok:
            exclusions.append(
                {
                    "model": model,
                    "canonical_id": sid_from_key(k),
                    "reason": "span_offset_fail",
                    "detail": ";".join(problems[:3]),
                }
            )
            continue

        al = align_record(text, rec["tokens"], rec["shap_pos"])
        if not al.alignment_ok:
            exclusions.append(
                {
                    "model": model,
                    "canonical_id": sid_from_key(k),
                    "reason": "shap_token_align_fail",
                    "detail": "|".join(al.unaligned_token_strs[:5]),
                }
            )
            continue

        # Gold metrics (empty spans → non_biased / coverage 0)
        m = compute_sentence_metrics(text, al.words, spans, top_k=TOP_K)
        gold_chars = char_mask(len(text), spans)
        labels = [1 if word_in_gold(w, gold_chars) else 0 for w in al.words]

        # Baselines (only meaningful if gold spans exist)
        base_abs = []
        base_pos = []
        base_prec = []
        base_rec = []
        base_ap = []
        pos_ctrl_abs = []
        if spans:
            for d in range(N_BASELINE_DRAWS):
                rng = random.Random(SEED + d * 10007 + hash((model, k)) % 9973)
                rsp = random_length_matched_spans(text, spans, rng)
                rm = compute_sentence_metrics(text, al.words, rsp, top_k=TOP_K)
                base_abs.append(rm["abs_mass_in_gold"])
                base_pos.append(rm["pos_mass_in_gold"])
                base_ap.append(rm["ap_abs"])
                rw = random_word_set_metrics(al.words, labels, TOP_K, rng)
                base_prec.append(rw["precision_at_k"])
                base_rec.append(rw["recall_at_k"])
            # positional control (deterministic)
            psp = positional_control_spans(text, spans)
            pm = compute_sentence_metrics(text, al.words, psp, top_k=TOP_K)
            pos_ctrl_abs.append(pm["abs_mass_in_gold"])

        pred = int(rec["pred"])
        gold = int(rec["gold"])
        if gold == 1 and pred == 1:
            cell = "TP"
        elif gold == 0 and pred == 1:
            cell = "FP"
        elif gold == 0 and pred == 0:
            cell = "TN"
        else:
            cell = "FN"

        row = {
            "canonical_id": sid_from_key(k),
            "triplet_uuid": k[0],
            "outlet_idx": k[1],
            "sentence_idx": k[2],
            "model": model,
            "gold": gold,
            "pred": pred,
            "prob_pos": float(rec["prob_pos"]),
            "pred_type": cell,
            "n_chars": len(text),
            **m,
            "baseline_abs_mass_mean": float(np.mean(base_abs)) if base_abs else float("nan"),
            "baseline_pos_mass_mean": float(np.mean(base_pos)) if base_pos else float("nan"),
            "baseline_precision_at_k_mean": float(np.mean(base_prec)) if base_prec else float("nan"),
            "baseline_recall_at_k_mean": float(np.mean(base_rec)) if base_rec else float("nan"),
            "baseline_ap_abs_mean": (
                float(np.mean([x for x in base_ap if x == x]))
                if any(x == x for x in base_ap)
                else float("nan")
            ),
            "positional_abs_mass": float(pos_ctrl_abs[0]) if pos_ctrl_abs else float("nan"),
            "abs_minus_random_span": (
                m["abs_mass_in_gold"] - float(np.mean(base_abs)) if base_abs else float("nan")
            ),
            "pos_minus_random_span": (
                m["pos_mass_in_gold"] - float(np.mean(base_pos)) if base_pos else float("nan")
            ),
            "prec_minus_random_words": (
                m["precision_at_k"] - float(np.mean(base_prec)) if base_prec else float("nan")
            ),
            "abs_minus_positional": (
                m["abs_mass_in_gold"] - float(pos_ctrl_abs[0]) if pos_ctrl_abs else float("nan")
            ),
            "abs_minus_coverage_baseline": m["abs_mass_in_gold"] - m["gold_char_coverage"],
        }
        rows.append(row)
    return rows


def summarize(rows: List[dict]) -> List[dict]:
    out = []
    models = sorted({r["model"] for r in rows})
    cats = ["ALL_POSITIVE", "lex_only", "inf_only", "both", "non_biased"]
    metrics = [
        ("abs_mass_in_gold", "abs_mass"),
        ("pos_mass_in_gold", "pos_mass"),
        ("precision_at_k", "prec@k"),
        ("recall_at_k", "rec@k"),
        ("ap_abs", "ap_abs"),
        ("abs_minus_random_span", "abs_minus_rand_span"),
        ("pos_minus_random_span", "pos_minus_rand_span"),
        ("prec_minus_random_words", "prec_minus_rand_words"),
        ("abs_minus_coverage_baseline", "abs_minus_coverage"),
        ("abs_minus_positional", "abs_minus_positional"),
        ("baseline_abs_mass_mean", "baseline_abs"),
        ("gold_char_coverage", "span_coverage"),
    ]

    def subset(model, cat):
        s = [r for r in rows if r["model"] == model]
        if cat == "ALL_POSITIVE":
            return [r for r in s if r["ann_category"] != "non_biased"]
        if cat == "non_biased":
            return [r for r in s if r["ann_category"] == "non_biased"]
        return [r for r in s if r["ann_category"] == cat]

    for model in models:
        for cat in cats:
            sub = subset(model, cat)
            if not sub:
                continue
            # coverage row
            out.append(
                {
                    "section": "coverage",
                    "model": model,
                    "ann_category": cat,
                    "n_sentences": len(sub),
                    "metric": "n",
                    "mean": len(sub),
                    "ci95_lo": "",
                    "ci95_hi": "",
                }
            )
            for field, name in metrics:
                if cat == "non_biased" and "minus" in field:
                    continue
                if cat == "non_biased" and field in (
                    "abs_mass_in_gold",
                    "pos_mass_in_gold",
                    "precision_at_k",
                    "recall_at_k",
                    "ap_abs",
                    "baseline_abs_mass_mean",
                    "gold_char_coverage",
                ):
                    # still report coverage-related; mass-in-gold is ~0 by construction
                    pass
                vals = [float(r[field]) for r in sub if r.get(field) == r.get(field)]
                # filter nans
                vals = [v for v in vals if v == v]
                if field == "ap_abs":
                    vals = [
                        float(r["ap_abs"])
                        for r in sub
                        if r.get("ap_eligible") in (1, "1") and r.get("ap_abs") == r.get("ap_abs")
                    ]
                    vals = [v for v in vals if v == v]
                mean, lo, hi = bootstrap_mean_ci(vals)
                out.append(
                    {
                        "section": "metric",
                        "model": model,
                        "ann_category": cat,
                        "n_sentences": len(vals) if field == "ap_abs" else len(sub),
                        "n_eligible": len(vals),
                        "metric": name,
                        "mean": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                    }
                )

    # Paired model comparisons on shared positive keys
    by_model = defaultdict(dict)
    for r in rows:
        if r["ann_category"] == "non_biased":
            continue
        by_model[r["model"]][r["canonical_id"]] = r

    pairs = [
        ("biasdetector", "daroberta"),
        ("biasdetector", "deberta"),
        ("daroberta", "deberta"),
    ]
    for a, b in pairs:
        common = set(by_model[a]) & set(by_model[b])
        if not common:
            continue
        for field, name in (
            ("abs_mass_in_gold", "abs_mass"),
            ("abs_minus_random_span", "abs_minus_rand_span"),
            ("precision_at_k", "prec@k"),
            ("ap_abs", "ap_abs"),
        ):
            diffs = []
            for cid in common:
                va, vb = by_model[a][cid][field], by_model[b][cid][field]
                if va != va or vb != vb:
                    continue
                if field == "ap_abs":
                    if not (
                        by_model[a][cid].get("ap_eligible") in (1, "1")
                        and by_model[b][cid].get("ap_eligible") in (1, "1")
                    ):
                        continue
                diffs.append(float(va) - float(vb))
            mean, lo, hi = bootstrap_mean_ci(diffs)
            out.append(
                {
                    "section": "paired_diff",
                    "model": f"{a}_minus_{b}",
                    "ann_category": "ALL_POSITIVE_SHARED",
                    "n_sentences": len(diffs),
                    "metric": name,
                    "mean": mean,
                    "ci95_lo": lo,
                    "ci95_hi": hi,
                }
            )
        # by ann category for BD-DR
        if (a, b) == ("biasdetector", "daroberta"):
            for cat in ("lex_only", "inf_only", "both"):
                diffs = []
                for cid in common:
                    ra, rb = by_model[a][cid], by_model[b][cid]
                    if ra["ann_category"] != cat:
                        continue
                    va, vb = ra["abs_minus_random_span"], rb["abs_minus_random_span"]
                    if va == va and vb == vb:
                        diffs.append(float(va) - float(vb))
                mean, lo, hi = bootstrap_mean_ci(diffs)
                out.append(
                    {
                        "section": "paired_diff",
                        "model": f"{a}_minus_{b}",
                        "ann_category": cat,
                        "n_sentences": len(diffs),
                        "metric": "abs_minus_rand_span",
                        "mean": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                    }
                )

    # By prediction outcome (TP/FN on gold-positive sentences) where n≥30
    for model in models:
        for outcome in ("TP", "FN"):
            for cat in ("ALL_POSITIVE", "lex_only", "inf_only"):
                if cat == "ALL_POSITIVE":
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] != "non_biased"
                        and r.get("pred_type") == outcome
                    ]
                else:
                    sub = [
                        r
                        for r in rows
                        if r["model"] == model
                        and r["ann_category"] == cat
                        and r.get("pred_type") == outcome
                    ]
                if len(sub) < 30:
                    continue
                for field, name in (
                    ("abs_minus_random_span", "abs_minus_rand_span"),
                    ("abs_mass_in_gold", "abs_mass"),
                ):
                    vals = [float(r[field]) for r in sub if r.get(field) == r.get(field)]
                    vals = [v for v in vals if v == v]
                    mean, lo, hi = bootstrap_mean_ci(vals)
                    out.append(
                        {
                            "section": "by_outcome",
                            "model": model,
                            "ann_category": f"{cat}|{outcome}",
                            "n_sentences": len(vals),
                            "metric": name,
                            "mean": mean,
                            "ci95_lo": lo,
                            "ci95_hi": hi,
                        }
                    )
    return out


def build_human_sample(
    sents: Dict[Tuple, dict],
    gold_by: Dict[Tuple, List[GoldSpan]],
    seed: int = SEED,
    n: int = HUMAN_N,
) -> List[dict]:
    """Blind annotation sample — text only, no SHAP/model labels in annotator columns."""
    rng = random.Random(seed)
    # Categorize all CSV sentences
    buckets = {"lex_only": [], "inf_only": [], "both": [], "non_biased": []}
    for k, row in sents.items():
        spans = gold_by.get(k, [])
        types = {sp.bias for sp in spans}
        if not spans:
            buckets["non_biased"].append(k)
        elif types == {"lex"}:
            buckets["lex_only"].append(k)
        elif types == {"inf"}:
            buckets["inf_only"].append(k)
        else:
            buckets["both"].append(k)

    # Target balance: ~30 each; both only has 44 total
    target = {"lex_only": 30, "inf_only": 30, "both": 30, "non_biased": 30}
    chosen = []
    notes = {}
    for cat, want in target.items():
        pool = list(buckets[cat])
        rng.shuffle(pool)
        take = min(want, len(pool))
        notes[cat] = {"available": len(pool), "taken": take}
        for i, k in enumerate(pool[:take]):
            chosen.append((cat, i, k))
    # fill to n from largest remaining if short
    while len(chosen) < n:
        # add more inf_only / non_biased
        for cat in ("inf_only", "non_biased", "lex_only", "both"):
            if len(chosen) >= n:
                break
            have = {k for _, _, k in chosen}
            rem = [k for k in buckets[cat] if k not in have]
            rng.shuffle(rem)
            if rem:
                chosen.append((cat, len(chosen), rem[0]))
        else:
            break

    rng.shuffle(chosen)
    rows = []
    for ann_idx, (cat, _, k) in enumerate(chosen[:n]):
        row = sents[k]
        spans = gold_by.get(k, [])
        # gold fields for analysts only — separate columns prefixed gold_
        rows.append(
            {
                "item_id": f"H{ann_idx:03d}",
                "canonical_id": sid_from_key(k),
                "triplet_uuid": k[0],
                "outlet_idx": k[1],
                "sentence_idx": k[2],
                "year": row.get("year", ""),
                "source": row.get("source", ""),
                "sentence_text": row["text"],
                # annotator fields (blank)
                "ann_bias_present": "",  # yes/no
                "ann_bias_type": "",  # lexical / informational / both / none
                "ann_span1_start": "",
                "ann_span1_end": "",
                "ann_span1_text": "",
                "ann_span2_start": "",
                "ann_span2_end": "",
                "ann_span2_text": "",
                "ann_needs_article_context": "",  # yes/no/unsure
                "ann_uncertainty": "",  # low/med/high
                "ann_comments": "",
                # hidden gold for later scoring (analysts; strip before sending if needed)
                "GOLD_category": cat,
                "GOLD_n_spans": len(spans),
                "GOLD_spans_json": json.dumps(
                    [{"start": s.start, "end": s.end, "bias": s.bias, "txt": s.txt} for s in spans],
                    ensure_ascii=False,
                ),
            }
        )
    (OUT / "human_sample_notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
    return rows


def write_annotator_html(sample: List[dict], path: Path) -> None:
    """Simple HTML form preserving character offsets via JS selection."""
    items = []
    for r in sample:
        # strip GOLD from display payload
        items.append(
            {
                "item_id": r["item_id"],
                "text": r["sentence_text"],
                "canonical_id": r["canonical_id"],
            }
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>BASIL Bias Evidence Annotation (Blind)</title>
<style>
 body {{ font-family: Georgia, serif; max-width: 820px; margin: 1.5rem auto; line-height: 1.45; color: #222; }}
 .item {{ border-top: 1px solid #ccc; padding: 1rem 0 1.25rem; }}
 .meta {{ color: #666; font-size: 0.9rem; }}
 .sent {{ background: #f7f7f5; padding: 0.85rem 1rem; border-radius: 4px; white-space: pre-wrap; }}
 label {{ display: inline-block; margin-right: 0.75rem; }}
 textarea, input[type=text] {{ width: 100%; box-sizing: border-box; }}
 button {{ margin: 0.25rem 0.25rem 0.25rem 0; }}
 .hint {{ font-size: 0.85rem; color: #555; }}
</style>
</head>
<body>
<h1>Bias evidence annotation (blind)</h1>
<p class="hint">Select text in the sentence to capture exact character offsets. Do not use external model highlights.
See the annotation guide for definitions. Export JSON when finished.</p>
<div id="app"></div>
<p><button id="export">Export annotations JSON</button></p>
<script>
const ITEMS = {json.dumps(items, ensure_ascii=False)};
const root = document.getElementById('app');
const state = {{}};
ITEMS.forEach((it, idx) => {{
  state[it.item_id] = {{
    item_id: it.item_id,
    canonical_id: it.canonical_id,
    bias_present: '',
    bias_type: '',
    spans: [],
    needs_context: '',
    uncertainty: '',
    comments: ''
  }};
  const div = document.createElement('div');
  div.className = 'item';
  div.innerHTML = `
    <div class="meta">${{it.item_id}} · ${{it.canonical_id}}</div>
    <div class="sent" id="sent-${{it.item_id}}">${{it.text.replace(/</g,'&lt;')}}</div>
    <p class="hint">Drag to select evidence, then click “Add span”.</p>
    <button type="button" data-add="${{it.item_id}}">Add span from selection</button>
    <button type="button" data-clear="${{it.item_id}}">Clear spans</button>
    <div id="spans-${{it.item_id}}" class="hint"></div>
    <p>
      <label>Bias present?
        <select data-field="bias_present" data-id="${{it.item_id}}">
          <option value="">—</option><option>yes</option><option>no</option>
        </select>
      </label>
      <label>Type
        <select data-field="bias_type" data-id="${{it.item_id}}">
          <option value="">—</option>
          <option>lexical</option><option>informational</option><option>both</option><option>none</option>
        </select>
      </label>
      <label>Needs article context?
        <select data-field="needs_context" data-id="${{it.item_id}}">
          <option value="">—</option><option>yes</option><option>no</option><option>unsure</option>
        </select>
      </label>
      <label>Uncertainty
        <select data-field="uncertainty" data-id="${{it.item_id}}">
          <option value="">—</option><option>low</option><option>med</option><option>high</option>
        </select>
      </label>
    </p>
    <label>Comments<textarea data-field="comments" data-id="${{it.item_id}}" rows="2"></textarea></label>
  `;
  root.appendChild(div);
}});
function renderSpans(id) {{
  const el = document.getElementById('spans-'+id);
  el.textContent = state[id].spans.map(s => `[${{s.start}},${{s.end}}) “${{s.text}}”`).join(' | ') || '(no spans)';
}}
root.addEventListener('click', (e) => {{
  const add = e.target.getAttribute('data-add');
  const clr = e.target.getAttribute('data-clear');
  if (add) {{
    const sent = document.getElementById('sent-'+add);
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || !sent.contains(sel.anchorNode)) return;
    const range = sel.getRangeAt(0);
    const pre = document.createRange();
    pre.selectNodeContents(sent);
    pre.setEnd(range.startContainer, range.startOffset);
    const start = pre.toString().length;
    const text = range.toString();
    const end = start + text.length;
    if (text.length === 0) return;
    state[add].spans.push({{start, end, text}});
    renderSpans(add);
  }}
  if (clr) {{ state[clr].spans = []; renderSpans(clr); }}
}});
root.addEventListener('change', (e) => {{
  const id = e.target.getAttribute('data-id');
  const field = e.target.getAttribute('data-field');
  if (id && field) state[id][field] = e.target.value;
}});
document.getElementById('export').onclick = () => {{
  const blob = new Blob([JSON.stringify(Object.values(state), null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'basil_blind_annotations.json';
  a.click();
}};
</script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def make_figures(rows: List[dict], summary: List[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = OUT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Abs mass vs random baseline by model × ann category
    cats = ["lex_only", "inf_only", "both"]
    models = ["biasdetector", "daroberta", "deberta"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, model in zip(axes, models):
        # gather means from summary
        shap_m, rand_m, labels = [], [], []
        for cat in cats:
            hs = [
                s
                for s in summary
                if s["section"] == "metric"
                and s["model"] == model
                and s["ann_category"] == cat
                and s["metric"] == "abs_mass"
            ]
            hr = [
                s
                for s in summary
                if s["section"] == "metric"
                and s["model"] == model
                and s["ann_category"] == cat
                and s["metric"] == "baseline_abs"
            ]
            if hs and hr and hs[0]["mean"] == hs[0]["mean"]:
                labels.append(cat)
                shap_m.append(float(hs[0]["mean"]))
                rand_m.append(float(hr[0]["mean"]))
        x = np.arange(len(labels))
        w = 0.35
        if len(labels):
            ax.bar(x - w / 2, shap_m, w, label="SHAP mass in gold", color="#2c3e50")
            ax.bar(x + w / 2, rand_m, w, label="Length-matched random", color="#bdc3c7")
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.set_title(model)
        ax.set_ylabel("Mean |SHAP| mass in spans")
        ax.set_ylim(0, 1)
    axes[0].legend(fontsize=8)
    fig.suptitle("Gold-span attribution mass vs length-matched random baseline")
    fig.tight_layout()
    fig.savefig(fig_dir / "abs_mass_vs_random.png", dpi=160, bbox_inches="tight")
    fig.savefig(fig_dir / "abs_mass_vs_random.pdf", bbox_inches="tight")
    plt.close(fig)

    # Excess over random (abs_minus_rand) lex vs inf
    fig, ax = plt.subplots(figsize=(7.5, 4))
    xpos = 0
    ticks, ticklabels = [], []
    colors = {"biasdetector": "#c0392b", "daroberta": "#2980b9", "deberta": "#27ae60"}
    for cat in ("lex_only", "inf_only"):
        for model in models:
            hits = [
                s
                for s in summary
                if s["section"] == "metric"
                and s["model"] == model
                and s["ann_category"] == cat
                and s["metric"] == "abs_minus_rand_span"
            ]
            if not hits:
                continue
            m, lo, hi = float(hits[0]["mean"]), float(hits[0]["ci95_lo"]), float(hits[0]["ci95_hi"])
            ax.bar(xpos, m, color=colors[model], yerr=[[m - lo], [hi - m]], capsize=3, width=0.8)
            ticks.append(xpos)
            ticklabels.append(f"{cat}\n{model[:2]}")
            xpos += 1
        xpos += 0.6
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels, fontsize=8)
    ax.set_ylabel("Mean excess |SHAP| mass over random spans")
    ax.set_title("SHAP−random gold-span mass (95% CI)")
    fig.tight_layout()
    fig.savefig(fig_dir / "excess_mass_lex_vs_inf.png", dpi=160, bbox_inches="tight")
    fig.savefig(fig_dir / "excess_mass_lex_vs_inf.pdf", bbox_inches="tight")
    plt.close(fig)


def flag_contextual_examples(rows: List[dict], sents: Dict, gold_by: Dict) -> List[dict]:
    """Heuristic flags for informational spans that may need article context.

    We cannot recover full article context necessity from spans alone; flag
    short informational spans and 'both' sentences for qualitative review.
    """
    out = []
    # pick BD rows with inf
    for r in rows:
        if r["model"] != "biasdetector":
            continue
        if r["ann_category"] not in ("inf_only", "both"):
            continue
        k = (r["triplet_uuid"], int(r["outlet_idx"]), int(r["sentence_idx"]))
        spans = gold_by.get(k, [])
        inf_spans = [sp for sp in spans if sp.bias == "inf"]
        if not inf_spans:
            continue
        mean_len = float(np.mean([sp.end - sp.start for sp in inf_spans]))
        # flag: weak excess over random OR very short/long relative cues
        weak = r.get("abs_minus_random_span") == r.get("abs_minus_random_span") and float(
            r["abs_minus_random_span"]
        ) < 0.05
        out.append(
            {
                "canonical_id": r["canonical_id"],
                "ann_category": r["ann_category"],
                "abs_mass_in_gold": r["abs_mass_in_gold"],
                "abs_minus_random_span": r["abs_minus_random_span"],
                "mean_inf_span_len": mean_len,
                "flag_weak_vs_random": int(weak),
                "sentence_preview": sents[k]["text"][:180],
                "inf_span_preview": " || ".join(sp.txt[:80] for sp in inf_spans[:2]),
            }
        )
    out.sort(key=lambda x: (float(x["abs_minus_random_span"]) if x["abs_minus_random_span"] == x["abs_minus_random_span"] else 99))
    return out[:80]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)

    gold_by = load_gold_by_sentence()
    sents = load_sentences()
    exclusions: List[dict] = []

    all_rows: List[dict] = []
    coverage = {}
    for model, path in CACHES.items():
        cache = load_jsonl_index(path)
        rows = analyze_model(model, cache, gold_by, sents, exclusions)
        all_rows.extend(rows)
        pos = [r for r in rows if r["ann_category"] != "non_biased"]
        coverage[model] = {
            "n_cache": len(cache),
            "n_analyzed": len(rows),
            "n_positive_aligned": len(pos),
            "n_lex_only": sum(1 for r in pos if r["ann_category"] == "lex_only"),
            "n_inf_only": sum(1 for r in pos if r["ann_category"] == "inf_only"),
            "n_both": sum(1 for r in pos if r["ann_category"] == "both"),
            "n_non_biased": sum(1 for r in rows if r["ann_category"] == "non_biased"),
        }
        print(f"[{model}] analyzed={len(rows)} positive={len(pos)} {coverage[model]}")

    # Shared coverage
    by_m = defaultdict(set)
    for r in all_rows:
        if r["ann_category"] != "non_biased":
            by_m[r["model"]].add(r["canonical_id"])
    coverage["paired_positive"] = {
        "bd∩dr": len(by_m["biasdetector"] & by_m["daroberta"]),
        "bd∩deb": len(by_m["biasdetector"] & by_m["deberta"]),
        "dr∩deb": len(by_m["daroberta"] & by_m["deberta"]),
        "all3": len(by_m["biasdetector"] & by_m["daroberta"] & by_m["deberta"]),
    }

    write_csv(OUT / "gold_span_alignment.csv", all_rows)
    summary = summarize(all_rows)
    write_csv(OUT / "gold_span_summary.csv", summary)
    write_csv(OUT / "exclusion_log.csv", exclusions)
    (OUT / "coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")

    ctx = flag_contextual_examples(all_rows, sents, gold_by)
    write_csv(OUT / "informational_context_flags.csv", ctx)

    make_figures(all_rows, summary)

    # Human annotation prep
    sample = build_human_sample(sents, gold_by, SEED, HUMAN_N)
    write_csv(OUT / "human_annotation_sample.csv", sample)
    # Annotator-facing CSV without GOLD columns
    blind = []
    for r in sample:
        blind.append({k: v for k, v in r.items() if not k.startswith("GOLD_")})
    write_csv(OUT / "human_annotation_sample_BLIND.csv", blind)
    write_annotator_html(sample, OUT / "human_annotation_interface.html")

    # Key console stats
    print("\n=== KEY: abs_minus_rand_span ===")
    for s in summary:
        if s["section"] == "metric" and s["metric"] == "abs_minus_rand_span":
            print(
                f"{s['model']:12} {s['ann_category']:10} n={s['n_sentences']:3} "
                f"mean={float(s['mean']):+.3f} CI=[{float(s['ci95_lo']):+.3f},{float(s['ci95_hi']):+.3f}]"
            )
    print("exclusions", len(exclusions), "human sample", len(sample))
    print("paired", coverage["paired_positive"])


if __name__ == "__main__":
    main()
