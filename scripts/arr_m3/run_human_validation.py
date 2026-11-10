#!/usr/bin/env python3
"""ARR M3 Phase 1 — analyze real annA/annB exports (do not modify source JSON)."""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2c"))
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2d"))

from offset_alignment import align_record  # noqa: E402
from gold_span_metrics import (  # noqa: E402
    GoldSpan,
    average_precision,
    bootstrap_mean_ci,
    char_mask,
    compute_sentence_metrics,
    random_length_matched_spans,
    word_in_gold,
)
from human_agreement import cohen_kappa, span_soft_f1  # noqa: E402

OUT = ROOT / "outputs" / "arr_m3"
RAW_A = ROOT / "outputs" / "arr_m2d" / "human_raw" / "basil_blind_annotations_annA.json"
RAW_B = ROOT / "outputs" / "arr_m2d" / "human_raw" / "basil_blind_annotations_annB.json"
SAMPLE = ROOT / "outputs" / "arr_m2c" / "human_annotation_sample.csv"
CACHES = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl",
}
SEED = 7
N_BASELINE = 20
TOP_K = 5


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
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


def load_json_list(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "annotations" in data:
        data = data["annotations"]
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}")
    return data


def load_sample() -> Dict[str, dict]:
    out = {}
    with SAMPLE.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["item_id"]] = row
    return out


def norm_present(v) -> str:
    v = ("" if v is None else str(v)).strip().lower()
    if v in ("yes", "y", "true", "1"):
        return "yes"
    if v in ("no", "n", "false", "0"):
        return "no"
    return ""


def norm_type(v) -> str:
    v = ("" if v is None else str(v)).strip().lower()
    return {
        "lexical": "lexical",
        "lex": "lexical",
        "informational": "informational",
        "inf": "informational",
        "both": "both",
        "none": "none",
        "no": "none",
    }.get(v, "" if not v else v)


def norm_context(v) -> str:
    v = ("" if v is None else str(v)).strip().lower()
    return v if v in ("yes", "no", "unsure") else ""


def validate_spans(text: str, spans: Sequence[dict]) -> Tuple[List[dict], List[dict]]:
    """Return (valid_spans, errors). Offsets treated as Python/Unicode code-point indices.

    Sample has 0 non-BMP characters, so JS UTF-16 code-unit offsets coincide with
    Python string indices for this study.
    """
    valid, errors = [], []
    for sp in spans or []:
        try:
            s, e = int(sp["start"]), int(sp["end"])
        except (KeyError, TypeError, ValueError) as ex:
            errors.append({"error": "bad_offsets", "span": sp, "detail": str(ex)})
            continue
        claimed = sp.get("text", "")
        if s < 0 or e < s or e > len(text):
            errors.append({"error": "oob", "start": s, "end": e, "claimed": claimed})
            continue
        got = text[s:e]
        if got != claimed:
            errors.append(
                {
                    "error": "text_mismatch",
                    "start": s,
                    "end": e,
                    "claimed": claimed,
                    "got": got,
                }
            )
            continue
        valid.append({"start": s, "end": e, "text": claimed})
    return valid, errors


def index_annotator(raw: List[dict], sample: Dict[str, dict], who: str) -> Tuple[Dict[str, dict], dict]:
    by_id = {}
    issues = []
    for row in raw:
        iid = row.get("item_id")
        if not iid:
            issues.append({"who": who, "issue": "missing_item_id", "row": row})
            continue
        if iid in by_id:
            issues.append({"who": who, "issue": "duplicate_item_id", "item_id": iid})
            continue
        if iid not in sample:
            issues.append({"who": who, "issue": "unknown_item_id", "item_id": iid})
            continue
        text = sample[iid]["sentence_text"]
        if row.get("canonical_id") != sample[iid]["canonical_id"]:
            issues.append(
                {
                    "who": who,
                    "issue": "canonical_mismatch",
                    "item_id": iid,
                    "ann": row.get("canonical_id"),
                    "sample": sample[iid]["canonical_id"],
                }
            )
        present = norm_present(row.get("bias_present"))
        btype = norm_type(row.get("bias_type"))
        ctx = norm_context(row.get("needs_context"))
        spans_raw = row.get("spans") or []
        spans, span_errs = validate_spans(text, spans_raw)
        for e in span_errs:
            issues.append({"who": who, "item_id": iid, "issue": "span_error", **e})

        if present == "yes" and len(spans) == 0:
            issues.append({"who": who, "item_id": iid, "issue": "yes_without_spans"})
        if present == "no" and len(spans) > 0:
            issues.append({"who": who, "item_id": iid, "issue": "no_with_spans"})
        if present == "yes" and btype == "none":
            issues.append({"who": who, "item_id": iid, "issue": "yes_type_none"})
        if present == "no" and btype not in ("", "none"):
            issues.append({"who": who, "item_id": iid, "issue": "no_type_nonzero", "type": btype})
        if present == "" and btype:
            issues.append({"who": who, "item_id": iid, "issue": "type_without_present", "type": btype})

        by_id[iid] = {
            "item_id": iid,
            "canonical_id": sample[iid]["canonical_id"],
            "annotator_id": row.get("annotator_id") or who,
            "bias_present": present,
            "bias_type": btype,
            "needs_context": ctx,
            "uncertainty": (row.get("uncertainty") or "").strip().lower(),
            "comments": row.get("comments") or "",
            "spans": spans,
            "n_spans": len(spans),
            "span_coverage": (
                float(char_mask(len(text), [GoldSpan(s["start"], s["end"], "h", s["text"]) for s in spans]).mean())
                if text and spans
                else 0.0
            ),
            "sentence_text": text,
            "GOLD_category": sample[iid]["GOLD_category"],
            "GOLD_spans": json.loads(sample[iid]["GOLD_spans_json"]),
        }
    report = {
        "who": who,
        "n_raw": len(raw),
        "n_indexed": len(by_id),
        "n_issues": len(issues),
        "issue_counts": dict(Counter(i["issue"] for i in issues)),
        "present_counts": dict(Counter(r["bias_present"] for r in by_id.values())),
        "type_counts": dict(Counter(r["bias_type"] for r in by_id.values())),
        "context_counts": dict(Counter(r["needs_context"] for r in by_id.values())),
        "issues": issues,
    }
    return by_id, report


def confusion(y1: Sequence[str], y2: Sequence[str], labels: Sequence[str]) -> List[dict]:
    mat = Counter((a, b) for a, b in zip(y1, y2))
    rows = []
    for a in labels:
        for b in labels:
            rows.append({"row": a, "col": b, "count": mat[(a, b)]})
    return rows


def agreement_block(ann_a, ann_b, field: str, labels: Sequence[str], both_required=True) -> dict:
    pairs = []
    for iid in sorted(set(ann_a) & set(ann_b)):
        va, vb = ann_a[iid][field], ann_b[iid][field]
        if both_required and (not va or not vb):
            continue
        if not both_required and (not va and not vb):
            continue
        if not va or not vb:
            continue
        pairs.append((va, vb))
    y1 = [p[0] for p in pairs]
    y2 = [p[1] for p in pairs]
    n = len(pairs)
    raw = float(np.mean([a == b for a, b in pairs])) if n else float("nan")
    # bootstrap raw agreement CI
    if n:
        rng = np.random.default_rng(SEED)
        boots = []
        arr = np.array([1.0 if a == b else 0.0 for a, b in pairs])
        for _ in range(2000):
            boots.append(float(rng.choice(arr, size=n, replace=True).mean()))
        boots.sort()
        lo, hi = boots[int(0.025 * 2000)], boots[int(0.975 * 2000)]
    else:
        lo = hi = float("nan")
    return {
        "field": field,
        "n_paired_complete": n,
        "raw_agreement": raw,
        "raw_ci95_lo": lo,
        "raw_ci95_hi": hi,
        "cohen_kappa": cohen_kappa(y1, y2) if n else float("nan"),
        "labels": list(labels),
        "confusion": confusion(y1, y2, labels),
        "missing_handling": "exclude pairs where either annotator has empty label",
    }


def span_agreement_rows(ann_a, ann_b) -> Tuple[List[dict], dict]:
    rows = []
    f1s, ious, tok_f1s = [], [], []
    for iid in sorted(set(ann_a) & set(ann_b)):
        text = ann_a[iid]["sentence_text"]
        ma = char_mask(len(text), [GoldSpan(s["start"], s["end"], "h", s["text"]) for s in ann_a[iid]["spans"]])
        mb = char_mask(len(text), [GoldSpan(s["start"], s["end"], "h", s["text"]) for s in ann_b[iid]["spans"]])
        soft = span_soft_f1(ma, mb)
        soft2 = span_soft_f1(mb, ma)
        f1 = 0.5 * (soft["f1"] + soft2["f1"])
        # token-level F1 via whitespace words
        words = text.split()
        # map words to char spans approximately
        # use simple regex-free whitespace split with positions
        import re

        wspans = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
        lab_a = [1 if ma[s:e].any() else 0 for s, e in wspans]
        lab_b = [1 if mb[s:e].any() else 0 for s, e in wspans]
        if not wspans:
            tok_f1 = float("nan")
        else:
            tp = sum(1 for x, y in zip(lab_a, lab_b) if x and y)
            pa = sum(lab_a)
            pb = sum(lab_b)
            if pa == 0 and pb == 0:
                tok_f1 = 1.0
            else:
                prec = tp / pb if pb else 0.0
                rec = tp / pa if pa else 0.0
                tok_f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        rows.append(
            {
                "item_id": iid,
                "GOLD_category": ann_a[iid]["GOLD_category"],
                "type_a": ann_a[iid]["bias_type"],
                "type_b": ann_b[iid]["bias_type"],
                "present_a": ann_a[iid]["bias_present"],
                "present_b": ann_b[iid]["bias_present"],
                "char_soft_f1": f1,
                "char_iou": soft["iou"],
                "token_f1": tok_f1,
                "both_empty_spans": int(len(ann_a[iid]["spans"]) == 0 and len(ann_b[iid]["spans"]) == 0),
                "either_empty_spans": int(len(ann_a[iid]["spans"]) == 0 or len(ann_b[iid]["spans"]) == 0),
            }
        )
        f1s.append(f1)
        ious.append(soft["iou"])
        if tok_f1 == tok_f1:
            tok_f1s.append(tok_f1)
    summary = {
        "n": len(rows),
        "char_soft_f1_mean": bootstrap_mean_ci(f1s),
        "char_iou_mean": bootstrap_mean_ci(ious),
        "token_f1_mean": bootstrap_mean_ci(tok_f1s),
        "empty_span_policy": (
            "Both empty ⇒ F1/IoU=1.0 (agree on no evidence). "
            "One empty vs non-empty ⇒ F1/IoU=0. Included in means."
        ),
    }
    return rows, summary


def human_vs_basil(ann: Dict[str, dict], who: str) -> Tuple[List[dict], dict]:
    gold_map = {
        "lex_only": "lexical",
        "inf_only": "informational",
        "both": "both",
        "non_biased": "none",
    }
    rows = []
    type_hits, bin_hits, f1s = [], [], []
    for iid, r in ann.items():
        gold_type = gold_map[r["GOLD_category"]]
        gold_bin = "no" if r["GOLD_category"] == "non_biased" else "yes"
        ht = r["bias_type"]
        hp = r["bias_present"]
        text = r["sentence_text"]
        mg = char_mask(
            len(text),
            [GoldSpan(s["start"], s["end"], s.get("bias", "g"), s.get("txt", s.get("text", ""))) for s in r["GOLD_spans"]],
        )
        mh = char_mask(len(text), [GoldSpan(s["start"], s["end"], "h", s["text"]) for s in r["spans"]])
        soft = span_soft_f1(mg, mh)
        row = {
            "annotator": who,
            "item_id": iid,
            "GOLD_category": r["GOLD_category"],
            "gold_type": gold_type,
            "gold_bin": gold_bin,
            "human_present": hp,
            "human_type": ht,
            "bin_agree": int(hp == gold_bin) if hp else "",
            "type_agree": int(ht == gold_type) if ht else "",
            "span_f1": soft["f1"],
            "span_iou": soft["iou"],
            "complete_present": int(bool(hp)),
            "complete_type": int(bool(ht)),
        }
        rows.append(row)
        if hp:
            bin_hits.append(float(hp == gold_bin))
        if ht:
            type_hits.append(float(ht == gold_type))
        f1s.append(soft["f1"])
    # kappa vs basil on complete pairs
    y_h_bin = [r["human_present"] for r in rows if r["human_present"]]
    y_g_bin = [r["gold_bin"] for r in rows if r["human_present"]]
    y_h_ty = [r["human_type"] for r in rows if r["human_type"]]
    y_g_ty = [r["gold_type"] for r in rows if r["human_type"]]
    summary = {
        "annotator": who,
        "n": len(rows),
        "n_complete_present": len(bin_hits),
        "n_complete_type": len(type_hits),
        "bin_agree_rate": float(np.mean(bin_hits)) if bin_hits else float("nan"),
        "bin_agree_ci": bootstrap_mean_ci(bin_hits),
        "type_agree_rate": float(np.mean(type_hits)) if type_hits else float("nan"),
        "type_agree_ci": bootstrap_mean_ci(type_hits),
        "kappa_bin": cohen_kappa(y_h_bin, y_g_bin) if y_h_bin else float("nan"),
        "kappa_type": cohen_kappa(y_h_ty, y_g_ty) if y_h_ty else float("nan"),
        "span_f1_mean": bootstrap_mean_ci(f1s),
    }
    return rows, summary


def both_disagree_basil(ann_a, ann_b) -> List[dict]:
    gold_map = {
        "lex_only": "lexical",
        "inf_only": "informational",
        "both": "both",
        "non_biased": "none",
    }
    out = []
    for iid in sorted(set(ann_a) & set(ann_b)):
        ga = gold_map[ann_a[iid]["GOLD_category"]]
        gb = "no" if ann_a[iid]["GOLD_category"] == "non_biased" else "yes"
        ha, hb = ann_a[iid]["bias_present"], ann_b[iid]["bias_present"]
        ta, tb = ann_a[iid]["bias_type"], ann_b[iid]["bias_type"]
        if not ha or not hb:
            continue
        if ha != gb and hb != gb:
            out.append(
                {
                    "item_id": iid,
                    "kind": "both_disagree_binary",
                    "GOLD": ann_a[iid]["GOLD_category"],
                    "gold_bin": gb,
                    "a": ha,
                    "b": hb,
                    "type_a": ta,
                    "type_b": tb,
                    "text": ann_a[iid]["sentence_text"][:160],
                }
            )
        if ta and tb and ta != ga and tb != ga:
            out.append(
                {
                    "item_id": iid,
                    "kind": "both_disagree_type",
                    "GOLD": ann_a[iid]["GOLD_category"],
                    "gold_type": ga,
                    "type_a": ta,
                    "type_b": tb,
                    "text": ann_a[iid]["sentence_text"][:160],
                }
            )
    return out


def load_cache_index(path: Path) -> Dict[str, dict]:
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid = f"basil:{r['triplet_uuid']}|{r['outlet_idx']}|{r['sentence_idx']}"
            out[cid] = r
    return out


def shap_vs_human(
    ann: Dict[str, dict],
    who: str,
    caches: Dict[str, Dict[str, dict]],
    agree_ids: Optional[set] = None,
    tag: str = "all",
) -> Tuple[List[dict], List[dict]]:
    rows = []
    for model, cache in caches.items():
        for iid, r in ann.items():
            if agree_ids is not None and iid not in agree_ids:
                continue
            if not r["bias_present"] or r["bias_present"] != "yes":
                continue
            if not r["spans"]:
                continue
            cid = r["canonical_id"]
            if cid not in cache:
                continue
            rec = cache[cid]
            text = r["sentence_text"]
            if rec.get("text") and rec["text"] != text:
                # skip text mismatch
                continue
            al = align_record(text, rec["tokens"], rec["shap_pos"])
            human_spans = [GoldSpan(s["start"], s["end"], "h", s["text"]) for s in r["spans"]]
            m = compute_sentence_metrics(text, al.words, human_spans, top_k=TOP_K)
            # baselines
            rng = random.Random(SEED + hash((iid, model, who)) % 10_000)
            base_abs, base_pos = [], []
            for _ in range(N_BASELINE):
                rsp = random_length_matched_spans(text, human_spans, rng)
                bm = compute_sentence_metrics(text, al.words, rsp, top_k=TOP_K)
                base_abs.append(bm["abs_mass_in_gold"])
                base_pos.append(bm["pos_mass_in_gold"])
            base_abs_m = float(np.mean(base_abs))
            base_pos_m = float(np.mean(base_pos))
            rows.append(
                {
                    "subset": tag,
                    "annotator": who,
                    "item_id": iid,
                    "model": model,
                    "canonical_id": cid,
                    "human_type": r["bias_type"],
                    "GOLD_category": r["GOLD_category"],
                    "span_coverage": r["span_coverage"],
                    "n_chars": len(text),
                    "abs_mass": m["abs_mass_in_gold"],
                    "pos_mass": m["pos_mass_in_gold"],
                    "prec_at_k": m["precision_at_k"],
                    "ap_abs": m["ap_abs"] if m["ap_eligible"] else float("nan"),
                    "ap_eligible": m["ap_eligible"],
                    "baseline_abs": base_abs_m,
                    "baseline_pos": base_pos_m,
                    "abs_minus_rand": m["abs_mass_in_gold"] - base_abs_m,
                    "pos_minus_rand": m["pos_mass_in_gold"] - base_pos_m,
                    "abs_minus_coverage": m["abs_mass_in_gold"] - r["span_coverage"],
                    "pred": rec.get("pred"),
                    "prob_pos": rec.get("prob_pos") or rec.get("prob"),
                }
            )
    # summarize
    summary = []
    by = defaultdict(list)
    for r in rows:
        by[(r["subset"], r["annotator"], r["model"], r["human_type"] or "UNK")].append(r)
        by[(r["subset"], r["annotator"], r["model"], "ALL_POSITIVE")].append(r)
    for key, sub in by.items():
        subset, who_k, model, htype = key
        for field, name in (
            ("abs_mass", "abs_mass"),
            ("pos_mass", "pos_mass"),
            ("abs_minus_rand", "abs_minus_rand"),
            ("pos_minus_rand", "pos_minus_rand"),
            ("abs_minus_coverage", "abs_minus_coverage"),
            ("ap_abs", "ap_abs"),
            ("span_coverage", "span_coverage"),
        ):
            vals = [float(r[field]) for r in sub if r.get(field) == r.get(field)]
            if field == "ap_abs":
                vals = [float(r["ap_abs"]) for r in sub if r.get("ap_eligible") and r.get("ap_abs") == r.get("ap_abs")]
            if len(vals) < 5:
                continue
            mean, lo, hi = bootstrap_mean_ci(vals)
            summary.append(
                {
                    "subset": subset,
                    "annotator": who_k,
                    "model": model,
                    "human_type": htype,
                    "metric": name,
                    "n": len(vals),
                    "mean": mean,
                    "ci95_lo": lo,
                    "ci95_hi": hi,
                }
            )
    # paired BD-DR on shared ids within this annotator+subset
    for subset in {r["subset"] for r in rows}:
        for who_k in {r["annotator"] for r in rows}:
            by_m = defaultdict(dict)
            for r in rows:
                if r["subset"] != subset or r["annotator"] != who_k:
                    continue
                by_m[r["model"]][r["item_id"]] = r
            common = set(by_m.get("biasdetector", {})) & set(by_m.get("daroberta", {}))
            if len(common) >= 5:
                diffs = [
                    float(by_m["biasdetector"][i]["abs_minus_rand"])
                    - float(by_m["daroberta"][i]["abs_minus_rand"])
                    for i in common
                    if by_m["biasdetector"][i]["abs_minus_rand"] == by_m["biasdetector"][i]["abs_minus_rand"]
                    and by_m["daroberta"][i]["abs_minus_rand"] == by_m["daroberta"][i]["abs_minus_rand"]
                ]
                mean, lo, hi = bootstrap_mean_ci(diffs)
                summary.append(
                    {
                        "subset": subset,
                        "annotator": who_k,
                        "model": "biasdetector_minus_daroberta",
                        "human_type": "ALL_POSITIVE",
                        "metric": "abs_minus_rand",
                        "n": len(diffs),
                        "mean": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                    }
                )
    return rows, summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sample = load_sample()
    raw_a = load_json_list(RAW_A)
    raw_b = load_json_list(RAW_B)
    ann_a, rep_a = index_annotator(raw_a, sample, "annA")
    ann_b, rep_b = index_annotator(raw_b, sample, "annB")

    integrity = {
        "offset_convention": (
            "Python/Unicode code-point indices. Study texts contain 0 non-BMP characters, "
            "so JS UTF-16 code-unit offsets from the annotation UI are identical."
        ),
        "n_sample": len(sample),
        "annA": {k: v for k, v in rep_a.items() if k != "issues"},
        "annB": {k: v for k, v in rep_b.items() if k != "issues"},
        "shared_ids": len(set(ann_a) & set(ann_b)),
        "source_files_unmodified": True,
    }
    (OUT / "annotation_integrity.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")
    write_csv(OUT / "annotation_integrity_issues.csv", rep_a["issues"] + rep_b["issues"])

    # Human-human
    present = agreement_block(ann_a, ann_b, "bias_present", ["yes", "no"])
    btype = agreement_block(ann_a, ann_b, "bias_type", ["lexical", "informational", "both", "none"])
    ctx = agreement_block(ann_a, ann_b, "needs_context", ["yes", "no", "unsure"])
    span_rows, span_sum = span_agreement_rows(ann_a, ann_b)
    # span agreement on both-complete type subsets
    span_lex = [r["char_soft_f1"] for r in span_rows if r["type_a"] == "lexical" and r["type_b"] == "lexical"]
    span_inf = [
        r["char_soft_f1"] for r in span_rows if r["type_a"] == "informational" and r["type_b"] == "informational"
    ]
    hh = {
        "bias_present": present,
        "bias_type": btype,
        "needs_context": ctx,
        "spans": {
            "policy": span_sum["empty_span_policy"],
            "char_soft_f1": {
                "mean": span_sum["char_soft_f1_mean"][0],
                "ci95_lo": span_sum["char_soft_f1_mean"][1],
                "ci95_hi": span_sum["char_soft_f1_mean"][2],
                "n": span_sum["n"],
            },
            "char_iou": {
                "mean": span_sum["char_iou_mean"][0],
                "ci95_lo": span_sum["char_iou_mean"][1],
                "ci95_hi": span_sum["char_iou_mean"][2],
            },
            "token_f1": {
                "mean": span_sum["token_f1_mean"][0],
                "ci95_lo": span_sum["token_f1_mean"][1],
                "ci95_hi": span_sum["token_f1_mean"][2],
            },
            "both_agree_lexical_span_f1": {
                "n": len(span_lex),
                "mean_ci": bootstrap_mean_ci(span_lex) if span_lex else (float("nan"),) * 3,
            },
            "both_agree_informational_span_f1": {
                "n": len(span_inf),
                "mean_ci": bootstrap_mean_ci(span_inf) if span_inf else (float("nan"),) * 3,
            },
        },
    }
    # serialize confusion separately
    conf_rows = []
    for block_name, block in (("bias_present", present), ("bias_type", btype), ("needs_context", ctx)):
        for c in block["confusion"]:
            conf_rows.append({"field": block_name, **c})
    write_csv(OUT / "hh_confusion.csv", conf_rows)
    write_csv(OUT / "hh_span_by_item.csv", span_rows)
    (OUT / "hh_agreement_summary.json").write_text(
        json.dumps(hh, indent=2, default=float), encoding="utf-8"
    )

    # Human vs BASIL
    hb_rows_a, hb_sum_a = human_vs_basil(ann_a, "annA")
    hb_rows_b, hb_sum_b = human_vs_basil(ann_b, "annB")
    write_csv(OUT / "human_vs_basil_by_item.csv", hb_rows_a + hb_rows_b)
    both_dis = both_disagree_basil(ann_a, ann_b)
    write_csv(OUT / "both_humans_disagree_basil.csv", both_dis)
    (OUT / "human_vs_basil_summary.json").write_text(
        json.dumps({"annA": hb_sum_a, "annB": hb_sum_b, "n_both_disagree_rows": len(both_dis)}, indent=2, default=float),
        encoding="utf-8",
    )

    # Agreement set: both complete present+type and equal
    agree_ids = set()
    for iid in set(ann_a) & set(ann_b):
        if (
            ann_a[iid]["bias_present"]
            and ann_b[iid]["bias_present"]
            and ann_a[iid]["bias_present"] == ann_b[iid]["bias_present"]
            and ann_a[iid]["bias_type"]
            and ann_b[iid]["bias_type"]
            and ann_a[iid]["bias_type"] == ann_b[iid]["bias_type"]
            and ann_a[iid]["bias_present"] == "yes"
        ):
            agree_ids.add(iid)

    caches = {m: load_cache_index(p) for m, p in CACHES.items()}
    # coverage of sample in caches
    sample_cids = {sample[i]["canonical_id"] for i in sample}
    cache_cov = {m: len(set(c) & sample_cids) for m, c in caches.items()}
    (OUT / "shap_sample_coverage.json").write_text(json.dumps(cache_cov, indent=2), encoding="utf-8")

    shap_rows, shap_sum = [], []
    for who, ann in (("annA", ann_a), ("annB", ann_b)):
        r1, s1 = shap_vs_human(ann, who, caches, agree_ids=None, tag="annotator_all")
        r2, s2 = shap_vs_human(ann, who, caches, agree_ids=agree_ids, tag="both_humans_agree")
        shap_rows.extend(r1)
        shap_rows.extend(r2)
        shap_sum.extend(s1)
        shap_sum.extend(s2)
    write_csv(OUT / "shap_vs_human_by_item.csv", shap_rows)
    write_csv(OUT / "shap_vs_human_summary.csv", shap_sum)

    # Console key numbers
    print("=== INTEGRITY ===")
    print("A issues", rep_a["issue_counts"])
    print("B issues", rep_b["issue_counts"])
    print("=== HH ===")
    print(
        f"present n={present['n_paired_complete']} raw={present['raw_agreement']:.3f} "
        f"κ={present['cohen_kappa']:.3f}"
    )
    print(
        f"type n={btype['n_paired_complete']} raw={btype['raw_agreement']:.3f} κ={btype['cohen_kappa']:.3f}"
    )
    print(
        f"context n={ctx['n_paired_complete']} raw={ctx['raw_agreement']:.3f} κ={ctx['cohen_kappa']:.3f}"
    )
    print(
        f"span F1 mean={span_sum['char_soft_f1_mean'][0]:.3f} "
        f"CI=[{span_sum['char_soft_f1_mean'][1]:.3f},{span_sum['char_soft_f1_mean'][2]:.3f}]"
    )
    print("=== HUMAN-BASIL ===")
    for s in (hb_sum_a, hb_sum_b):
        print(
            s["annotator"],
            f"bin={s['bin_agree_rate']:.3f} κ={s['kappa_bin']:.3f} "
            f"type={s['type_agree_rate']:.3f} κ={s['kappa_type']:.3f} "
            f"spanF1={s['span_f1_mean'][0]:.3f}"
        )
    print("both_disagree rows", len(both_dis), "agree_ids", len(agree_ids))
    print("=== SHAP coverage on sample ===", cache_cov)
    print("shap rows", len(shap_rows))
    for s in shap_sum:
        if s["metric"] == "abs_minus_rand" and s["human_type"] == "ALL_POSITIVE":
            print(
                f"{s['subset']} {s['annotator']} {s['model']}: n={s['n']} "
                f"excess={float(s['mean']):+.3f} [{float(s['ci95_lo']):+.3f},{float(s['ci95_hi']):+.3f}]"
            )


if __name__ == "__main__":
    main()
