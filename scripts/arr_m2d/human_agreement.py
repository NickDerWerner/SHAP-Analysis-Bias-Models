"""Task D — human annotation analysis pipeline (runs only when real files are supplied).

Metrics (and why):
- Binary bias presence: Cohen's κ — chance-corrected agreement for binary labels.
- Bias type (4-way): Cohen's κ on {none, lexical, informational, both}.
- Needs-context: Cohen's κ on {yes, no, unsure} (3-way).
- Span agreement: character-level soft F1 / IoU on union masks — handles variable-length
  multi-span annotations without requiring exact boundary identity.
- Human↔BASIL: same span soft-F1 + type agreement vs gold category.
- SHAP↔human: reuse M2C-style abs mass in human spans vs length-matched random baselines,
  stratified by human lexical vs informational (when type is available).

This module NEVER invents annotations. If files are missing, it exits with a clear message.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2d"))
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2c"))
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))

from stats_utils import bootstrap_mean_ci  # noqa: E402

OUT = ROOT / "outputs" / "arr_m2d"
SAMPLE = ROOT / "outputs" / "arr_m2c" / "human_annotation_sample.csv"


def _norm_present(v: str) -> str:
    v = (v or "").strip().lower()
    if v in ("yes", "y", "true", "1"):
        return "yes"
    if v in ("no", "n", "false", "0"):
        return "no"
    return ""


def _norm_type(v: str) -> str:
    v = (v or "").strip().lower()
    mapping = {
        "lexical": "lexical",
        "lex": "lexical",
        "informational": "informational",
        "inf": "informational",
        "both": "both",
        "none": "none",
        "no": "none",
        "": "",
    }
    return mapping.get(v, v)


def _norm_context(v: str) -> str:
    v = (v or "").strip().lower()
    if v in ("yes", "no", "unsure"):
        return v
    return ""


def cohen_kappa(y1: Sequence[str], y2: Sequence[str]) -> float:
    """Cohen's κ for categorical labels (same length, paired)."""
    assert len(y1) == len(y2)
    n = len(y1)
    if n == 0:
        return float("nan")
    labels = sorted(set(y1) | set(y2))
    idx = {lab: i for i, lab in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=float)
    for a, b in zip(y1, y2):
        mat[idx[a], idx[b]] += 1
    mat /= n
    po = float(np.trace(mat))
    pe = float(mat.sum(0) @ mat.sum(1))
    if abs(1 - pe) < 1e-12:
        return float("nan")
    return (po - pe) / (1 - pe)


def char_mask_from_spans(text_len: int, spans: Sequence[dict]) -> np.ndarray:
    m = np.zeros(text_len, dtype=bool)
    for sp in spans:
        a, b = int(sp["start"]), int(sp["end"])
        a = max(0, min(a, text_len))
        b = max(0, min(b, text_len))
        if a < b:
            m[a:b] = True
    return m


def span_soft_f1(mask_a: np.ndarray, mask_b: np.ndarray) -> Dict[str, float]:
    """Character soft precision/recall/F1 and IoU between two boolean masks."""
    inter = float(np.logical_and(mask_a, mask_b).sum())
    a = float(mask_a.sum())
    b = float(mask_b.sum())
    union = float(np.logical_or(mask_a, mask_b).sum())
    if a == 0 and b == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "iou": 1.0}
    prec = inter / b if b else 0.0  # treating b as prediction
    rec = inter / a if a else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    iou = inter / union if union else 1.0
    return {"precision": prec, "recall": rec, "f1": f1, "iou": iou}


def load_annotator_json(path: Path) -> Dict[str, dict]:
    """Load HTML-export JSON: list of {item_id, bias_present, bias_type, spans, ...}."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "annotations" in data:
        data = data["annotations"]
    out = {}
    for row in data:
        iid = row.get("item_id") or row.get("id")
        if not iid:
            continue
        out[iid] = {
            "item_id": iid,
            "annotator_id": row.get("annotator_id", ""),
            "bias_present": _norm_present(row.get("bias_present") or row.get("ann_bias_present", "")),
            "bias_type": _norm_type(row.get("bias_type") or row.get("ann_bias_type", "")),
            "needs_context": _norm_context(
                row.get("needs_context") or row.get("ann_needs_article_context", "")
            ),
            "uncertainty": (row.get("uncertainty") or row.get("ann_uncertainty") or "").strip().lower(),
            "comments": row.get("comments") or row.get("ann_comments") or "",
            "spans": row.get("spans")
            or _spans_from_flat(row),
        }
    return out


def _spans_from_flat(row: dict) -> List[dict]:
    spans = []
    for i in (1, 2, 3, 4):
        s, e, t = row.get(f"ann_span{i}_start"), row.get(f"ann_span{i}_end"), row.get(f"ann_span{i}_text")
        if s in (None, "") or e in (None, ""):
            continue
        spans.append({"start": int(s), "end": int(e), "text": t or ""})
    return spans


def load_annotator_csv(path: Path) -> Dict[str, dict]:
    out = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iid = row["item_id"]
            out[iid] = {
                "item_id": iid,
                "annotator_id": row.get("annotator_id", ""),
                "bias_present": _norm_present(row.get("ann_bias_present", "")),
                "bias_type": _norm_type(row.get("ann_bias_type", "")),
                "needs_context": _norm_context(row.get("ann_needs_article_context", "")),
                "uncertainty": (row.get("ann_uncertainty") or "").strip().lower(),
                "comments": row.get("ann_comments") or "",
                "spans": _spans_from_flat(row),
            }
    return out


def load_annotations(path: Path) -> Dict[str, dict]:
    if path.suffix.lower() == ".json":
        return load_annotator_json(path)
    return load_annotator_csv(path)


def load_sample() -> Dict[str, dict]:
    out = {}
    with SAMPLE.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["item_id"]] = row
    return out


def analyze_pair(
    ann_a: Dict[str, dict],
    ann_b: Dict[str, dict],
    sample: Dict[str, dict],
    id_a: str,
    id_b: str,
) -> Dict:
    common = sorted(set(ann_a) & set(ann_b) & set(sample))
    if not common:
        raise SystemExit("No overlapping item_ids between annotators and sample.")

    present_a = [ann_a[i]["bias_present"] for i in common]
    present_b = [ann_b[i]["bias_present"] for i in common]
    # drop incomplete
    pairs_p = [(x, y) for x, y in zip(present_a, present_b) if x and y]
    kappa_present = cohen_kappa([x for x, _ in pairs_p], [y for _, y in pairs_p]) if pairs_p else float("nan")

    type_a = [ann_a[i]["bias_type"] for i in common]
    type_b = [ann_b[i]["bias_type"] for i in common]
    pairs_t = [(x, y) for x, y in zip(type_a, type_b) if x and y]
    kappa_type = cohen_kappa([x for x, _ in pairs_t], [y for _, y in pairs_t]) if pairs_t else float("nan")

    ctx_a = [ann_a[i]["needs_context"] for i in common]
    ctx_b = [ann_b[i]["needs_context"] for i in common]
    pairs_c = [(x, y) for x, y in zip(ctx_a, ctx_b) if x and y]
    kappa_ctx = cohen_kappa([x for x, _ in pairs_c], [y for _, y in pairs_c]) if pairs_c else float("nan")

    f1s, ious = [], []
    for iid in common:
        text = sample[iid]["sentence_text"]
        ma = char_mask_from_spans(len(text), ann_a[iid]["spans"])
        mb = char_mask_from_spans(len(text), ann_b[iid]["spans"])
        m = span_soft_f1(ma, mb)
        # symmetric F1: average of (a as ref) and (b as ref)
        m2 = span_soft_f1(mb, ma)
        f1s.append(0.5 * (m["f1"] + m2["f1"]))
        ious.append(m["iou"])
    f1_mean, f1_lo, f1_hi = bootstrap_mean_ci(f1s)
    iou_mean, iou_lo, iou_hi = bootstrap_mean_ci(ious)

    # Human vs BASIL gold
    gold_type_map = {
        "lex_only": "lexical",
        "inf_only": "informational",
        "both": "both",
        "non_biased": "none",
    }
    human_basil_type_hit = []
    human_basil_f1 = []
    for iid in common:
        gold_cat = sample[iid]["GOLD_category"]
        gold_type = gold_type_map[gold_cat]
        # use annotator A as primary for human-basil (also report B)
        for ann, tag in ((ann_a, id_a), (ann_b, id_b)):
            ht = ann[iid]["bias_type"]
            if not ht:
                continue
            human_basil_type_hit.append(
                {"item_id": iid, "annotator": tag, "agree": int(ht == gold_type), "human": ht, "gold": gold_type}
            )
            text = sample[iid]["sentence_text"]
            gold_spans = json.loads(sample[iid]["GOLD_spans_json"])
            mg = char_mask_from_spans(len(text), gold_spans)
            mh = char_mask_from_spans(len(text), ann[iid]["spans"])
            human_basil_f1.append(span_soft_f1(mg, mh)["f1"])

    hb_f1_mean, hb_lo, hb_hi = bootstrap_mean_ci(human_basil_f1)
    type_agree_rate = (
        float(np.mean([r["agree"] for r in human_basil_type_hit])) if human_basil_type_hit else float("nan")
    )

    return {
        "n_items": len(common),
        "kappa_bias_present": kappa_present,
        "kappa_bias_type": kappa_type,
        "kappa_needs_context": kappa_ctx,
        "span_soft_f1_mean": f1_mean,
        "span_soft_f1_ci95_lo": f1_lo,
        "span_soft_f1_ci95_hi": f1_hi,
        "span_iou_mean": iou_mean,
        "span_iou_ci95_lo": iou_lo,
        "span_iou_ci95_hi": iou_hi,
        "human_basil_type_agree_rate": type_agree_rate,
        "human_basil_span_f1_mean": hb_f1_mean,
        "human_basil_span_f1_ci95_lo": hb_lo,
        "human_basil_span_f1_ci95_hi": hb_hi,
        "n_present_pairs": len(pairs_p),
        "n_type_pairs": len(pairs_t),
        "n_context_pairs": len(pairs_c),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Analyze real human annotations (M2D).")
    p.add_argument("--annotator-a", type=Path, required=True, help="JSON or CSV from annotator A")
    p.add_argument("--annotator-b", type=Path, required=True, help="JSON or CSV from annotator B")
    p.add_argument("--id-a", default="A", help="Annotator A id label")
    p.add_argument("--id-b", default="B", help="Annotator B id label")
    p.add_argument("--out-dir", type=Path, default=OUT / "human_analysis")
    args = p.parse_args(argv)

    if not args.annotator_a.exists() or not args.annotator_b.exists():
        print(
            "ERROR: Annotation files not found. Do not simulate labels. "
            "Provide real exports from two annotators.",
            file=sys.stderr,
        )
        return 2

    sample = load_sample()
    ann_a = load_annotations(args.annotator_a)
    ann_b = load_annotations(args.annotator_b)
    # stamp ids if missing
    for row in ann_a.values():
        row["annotator_id"] = row.get("annotator_id") or args.id_a
    for row in ann_b.values():
        row["annotator_id"] = row.get("annotator_id") or args.id_b

    summary = analyze_pair(ann_a, ann_b, sample, args.id_a, args.id_b)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "agreement_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    # per-item table
    common = sorted(set(ann_a) & set(ann_b) & set(sample))
    rows = []
    for iid in common:
        text = sample[iid]["sentence_text"]
        ma = char_mask_from_spans(len(text), ann_a[iid]["spans"])
        mb = char_mask_from_spans(len(text), ann_b[iid]["spans"])
        soft = span_soft_f1(ma, mb)
        rows.append(
            {
                "item_id": iid,
                "GOLD_category": sample[iid]["GOLD_category"],
                "present_a": ann_a[iid]["bias_present"],
                "present_b": ann_b[iid]["bias_present"],
                "type_a": ann_a[iid]["bias_type"],
                "type_b": ann_b[iid]["bias_type"],
                "context_a": ann_a[iid]["needs_context"],
                "context_b": ann_b[iid]["needs_context"],
                "span_f1": soft["f1"],
                "span_iou": soft["iou"],
            }
        )
    fields = list(rows[0].keys()) if rows else []
    with (args.out_dir / "agreement_by_item.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
