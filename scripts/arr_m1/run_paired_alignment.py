#!/usr/bin/env python3
"""ARR M1 Task B — cross-model sample alignment and paired attribution analysis."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "arr_m1" / "paired"

BABE = {
    "biasdetector": ROOT / "outputs" / "shap_samples.jsonl",
    "daroberta": ROOT / "outputs" / "shap_samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "shap_samples_deberta.jsonl",
}
BASIL = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
    "deberta": ROOT / "outputs" / "basil_shap" / "samples_deberta.jsonl",
}
MANIFEST = ROOT / "outputs" / "basil_shap" / "manifest.csv"


def load_jsonl(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def babe_sid(text: str) -> str:
    return "babe:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def basil_sid(r: dict) -> str:
    return (
        f"basil:{r['triplet_uuid']}|{int(r['outlet_idx'])}|{int(r['sentence_idx'])}"
    )


def pred_type(gold: int, pred: int) -> str:
    if gold == 1 and pred == 1:
        return "TP"
    if gold == 0 and pred == 1:
        return "FP"
    if gold == 0 and pred == 0:
        return "TN"
    return "FN"


def mean_abs_shap(r: dict) -> float:
    wa = r.get("word_attribs") or []
    if not wa:
        return float("nan")
    return sum(abs(x["shap"]) for x in wa) / len(wa)


def top_k_words(r: dict, k: int = 20) -> Set[str]:
    wa = sorted(r.get("word_attribs") or [], key=lambda x: abs(x["shap"]), reverse=True)
    return {w["word"].lower().strip('.,!?;:"()[]{}') for w in wa[:k] if w["word"].strip()}


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return float("nan")
    u = a | b
    return len(a & b) / len(u) if u else float("nan")


def cosine_abs_aligned(ra: dict, rb: dict) -> float:
    """Cosine similarity of |SHAP| on union of normalized word types (0 if missing)."""
    def bag(r):
        b = defaultdict(float)
        for wa in r.get("word_attribs") or []:
            w = wa["word"].lower().strip('.,!?;:"()[]{}')
            if w:
                b[w] += abs(float(wa["shap"]))
        return b

    ba, bb = bag(ra), bag(rb)
    keys = set(ba) | set(bb)
    if not keys:
        return float("nan")
    va = [ba.get(k, 0.0) for k in keys]
    vb = [bb.get(k, 0.0) for k in keys]
    # L1-normalize then cosine (= same as cosine on raw nonneg if we care about pattern)
    sa, sb = sum(va), sum(vb)
    if sa <= 0 or sb <= 0:
        return float("nan")
    va = [x / sa for x in va]
    vb = [x / sb for x in vb]
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(y * y for y in vb))
    return dot / (na * nb) if na and nb else float("nan")


def write_csv(path: Path, rows: List[dict], fields: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def median(xs: List[float]) -> float:
    ys = sorted(x for x in xs if x == x)
    if not ys:
        return float("nan")
    return ys[len(ys) // 2]


def audit_babe() -> Dict[str, Any]:
    caches = {m: load_jsonl(p) for m, p in BABE.items()}
    # index by sid
    by_sid = {m: {} for m in caches}
    id_map_rows = []
    for m, rows in caches.items():
        for i, r in enumerate(rows):
            sid = babe_sid(r["text"])
            by_sid[m][sid] = r
            id_map_rows.append(
                {
                    "corpus": "BABE",
                    "model": m,
                    "canonical_id": sid,
                    "cache_index": i,
                    "gold": r["gold"],
                    "pred": r["pred"],
                    "prob_pos": r["prob_pos"],
                    "pred_type": pred_type(r["gold"], r["pred"]),
                    "n_words": len(r.get("word_attribs") or []),
                    "text_sha16": sid.split(":")[1],
                }
            )

    sets = {m: set(by_sid[m]) for m in by_sid}
    inter_all = sets["biasdetector"] & sets["daroberta"] & sets["deberta"]
    pairs = {
        "bd∩dr": sets["biasdetector"] & sets["daroberta"],
        "bd∩deb": sets["biasdetector"] & sets["deberta"],
        "dr∩deb": sets["daroberta"] & sets["deberta"],
        "all3": inter_all,
    }

    coverage_rows = []
    for m, rows in caches.items():
        coverage_rows.append(
            {
                "corpus": "BABE",
                "set": m,
                "n": len(rows),
                "unique_ids": len(sets[m]),
            }
        )
    for name, s in pairs.items():
        coverage_rows.append({"corpus": "BABE", "set": name, "n": len(s), "unique_ids": len(s)})

    # by pred type for all3 — note: pred types may differ across models for same text
    cell_rows = []
    for cell in ("TP", "FP", "TN", "FN"):
        for m in caches:
            s = {
                sid
                for sid, r in by_sid[m].items()
                if pred_type(r["gold"], r["pred"]) == cell
            }
            cell_rows.append(
                {
                    "corpus": "BABE",
                    "model": m,
                    "pred_type": cell,
                    "n": len(s),
                    "n_in_all3_same_cell": len(
                        {
                            sid
                            for sid in inter_all
                            if all(
                                pred_type(by_sid[mm][sid]["gold"], by_sid[mm][sid]["pred"])
                                == cell
                                for mm in caches
                            )
                        }
                        & s
                        & inter_all
                    ),
                }
            )

    same_cell_all3 = {
        cell: {
            sid
            for sid in inter_all
            if all(
                pred_type(by_sid[m][sid]["gold"], by_sid[m][sid]["pred"]) == cell
                for m in caches
            )
        }
        for cell in ("TP", "FP", "TN", "FN")
    }

    paired_rows = []
    for sid in sorted(inter_all):
        rs = {m: by_sid[m][sid] for m in caches}
        # gold must match
        golds = {rs[m]["gold"] for m in caches}
        assert len(golds) == 1
        row = {
            "canonical_id": sid,
            "gold": rs["biasdetector"]["gold"],
            "text": rs["biasdetector"]["text"][:200],
        }
        for m in caches:
            row[f"pred_{m}"] = rs[m]["pred"]
            row[f"prob_{m}"] = rs[m]["prob_pos"]
            row[f"pred_type_{m}"] = pred_type(rs[m]["gold"], rs[m]["pred"])
            row[f"mean_abs_shap_{m}"] = mean_abs_shap(rs[m])
        # pairwise similarities
        for a, b, key in (
            ("biasdetector", "daroberta", "bd_dr"),
            ("biasdetector", "deberta", "bd_deb"),
            ("daroberta", "deberta", "dr_deb"),
        ):
            row[f"jaccard20_{key}"] = jaccard(top_k_words(rs[a]), top_k_words(rs[b]))
            row[f"cosine_abs_{key}"] = cosine_abs_aligned(rs[a], rs[b])
        paired_rows.append(row)

    # summary stats on paired
    summary = []
    for key in ("bd_dr", "bd_deb", "dr_deb"):
        js = [r[f"jaccard20_{key}"] for r in paired_rows]
        cs = [r[f"cosine_abs_{key}"] for r in paired_rows]
        summary.append(
            {
                "corpus": "BABE",
                "pair": key,
                "n_paired_sentences": len(paired_rows),
                "median_jaccard20": median(js),
                "mean_jaccard20": sum(js) / len(js) if js else float("nan"),
                "median_cosine_abs": median(cs),
                "mean_cosine_abs": sum(cs) / len(cs) if cs else float("nan"),
            }
        )

    # same-cell subsets
    same_cell_summary = []
    for cell, sids in same_cell_all3.items():
        same_cell_summary.append(
            {
                "corpus": "BABE",
                "same_pred_type_all3": cell,
                "n": len(sids),
                "note": "Insufficient for robust 3-model effects if n<30",
            }
        )

    write_csv(OUT / "babe_id_map.csv", id_map_rows)
    write_csv(OUT / "babe_coverage.csv", coverage_rows)
    write_csv(OUT / "babe_cell_counts.csv", cell_rows)
    write_csv(OUT / "babe_paired_all3.csv", paired_rows)
    write_csv(OUT / "babe_paired_similarity_summary.csv", summary)
    write_csv(OUT / "babe_same_cell_all3.csv", same_cell_summary)

    return {
        "n_all3": len(inter_all),
        "same_cell": {k: len(v) for k, v in same_cell_all3.items()},
        "similarity": summary,
    }


def audit_basil() -> Dict[str, Any]:
    caches = {m: load_jsonl(p) for m, p in BASIL.items()}
    by_sid = {m: {} for m in caches}
    id_map_rows = []
    for m, rows in caches.items():
        for i, r in enumerate(rows):
            sid = basil_sid(r)
            by_sid[m][sid] = r
            id_map_rows.append(
                {
                    "corpus": "BASIL",
                    "model": m,
                    "canonical_id": sid,
                    "triplet_uuid": r["triplet_uuid"],
                    "outlet_idx": int(r["outlet_idx"]),
                    "sentence_idx": int(r["sentence_idx"]),
                    "cache_index": i,
                    "gold": r["gold"],
                    "pred": r["pred"],
                    "prob_pos": r["prob_pos"],
                    "pred_type": pred_type(r["gold"], r["pred"]),
                    "has_lex": r.get("has_lex"),
                    "has_inf": r.get("has_inf"),
                }
            )

    sets = {m: set(by_sid[m]) for m in by_sid}
    inter_all = sets["biasdetector"] & sets["daroberta"] & sets["deberta"]
    inter_bd_dr = sets["biasdetector"] & sets["daroberta"]

    coverage = [
        {"corpus": "BASIL", "set": m, "n": len(caches[m]), "unique_ids": len(sets[m])}
        for m in caches
    ]
    coverage += [
        {"corpus": "BASIL", "set": "bd∩dr", "n": len(inter_bd_dr), "unique_ids": len(inter_bd_dr)},
        {"corpus": "BASIL", "set": "all3", "n": len(inter_all), "unique_ids": len(inter_all)},
    ]

    # manifest strata coverage
    strata_rows = []
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8") as f:
            man = list(csv.DictReader(f))
        for row in man:
            sid = f"basil:{row['triplet_uuid']}|{int(row['outlet_idx'])}|{int(row['sentence_idx'])}"
            strata_rows.append(
                {
                    "model": row["model"],
                    "stratum": row["stratum"],
                    "canonical_id": sid,
                    "in_cache": int(sid in by_sid.get(row["model"], {})),
                }
            )
        # aggregate
        from collections import Counter

        agg = Counter((r["model"], r["stratum"]) for r in strata_rows)
        strata_summary = [
            {"model": m, "stratum": s, "n_manifest": n}
            for (m, s), n in sorted(agg.items())
        ]
    else:
        strata_summary = []

    # Paired BD↔DR on intersection (the design of shared FP/FN)
    paired_bd_dr = []
    for sid in sorted(inter_bd_dr):
        ra, rb = by_sid["biasdetector"][sid], by_sid["daroberta"][sid]
        paired_bd_dr.append(
            {
                "canonical_id": sid,
                "gold": ra["gold"],
                "pred_bd": ra["pred"],
                "pred_dr": rb["pred"],
                "prob_bd": ra["prob_pos"],
                "prob_dr": rb["prob_pos"],
                "pred_type_bd": pred_type(ra["gold"], ra["pred"]),
                "pred_type_dr": pred_type(rb["gold"], rb["pred"]),
                "mean_abs_shap_bd": mean_abs_shap(ra),
                "mean_abs_shap_dr": mean_abs_shap(rb),
                "jaccard20": jaccard(top_k_words(ra), top_k_words(rb)),
                "cosine_abs": cosine_abs_aligned(ra, rb),
                "in_all3": int(sid in inter_all),
            }
        )

    # shared FP both pred=1 gold=0
    shared_fp = [
        r
        for r in paired_bd_dr
        if r["gold"] == 0 and r["pred_bd"] == 1 and r["pred_dr"] == 1
    ]
    shared_fn = [
        r
        for r in paired_bd_dr
        if r["gold"] == 1 and r["pred_bd"] == 0 and r["pred_dr"] == 0
    ]

    pair_summary = [
        {
            "corpus": "BASIL",
            "subset": "bd∩dr_all",
            "n": len(paired_bd_dr),
            "median_jaccard20": median([r["jaccard20"] for r in paired_bd_dr]),
            "median_cosine_abs": median([r["cosine_abs"] for r in paired_bd_dr]),
            "median_mean_abs_bd": median([r["mean_abs_shap_bd"] for r in paired_bd_dr]),
            "median_mean_abs_dr": median([r["mean_abs_shap_dr"] for r in paired_bd_dr]),
        },
        {
            "corpus": "BASIL",
            "subset": "shared_FP",
            "n": len(shared_fp),
            "median_jaccard20": median([r["jaccard20"] for r in shared_fp]),
            "median_cosine_abs": median([r["cosine_abs"] for r in shared_fp]),
            "median_mean_abs_bd": median([r["mean_abs_shap_bd"] for r in shared_fp]),
            "median_mean_abs_dr": median([r["mean_abs_shap_dr"] for r in shared_fp]),
        },
        {
            "corpus": "BASIL",
            "subset": "shared_FN",
            "n": len(shared_fn),
            "median_jaccard20": median([r["jaccard20"] for r in shared_fn]),
            "median_cosine_abs": median([r["cosine_abs"] for r in shared_fn]),
            "median_mean_abs_bd": median([r["mean_abs_shap_bd"] for r in shared_fn]),
            "median_mean_abs_dr": median([r["mean_abs_shap_dr"] for r in shared_fn]),
        },
        {
            "corpus": "BASIL",
            "subset": "all3",
            "n": len(inter_all),
            "median_jaccard20": "",
            "median_cosine_abs": "",
            "median_mean_abs_bd": "",
            "median_mean_abs_dr": "",
        },
    ]

    # 3-model paired where available
    paired_all3 = []
    for sid in sorted(inter_all):
        rs = {m: by_sid[m][sid] for m in caches}
        row = {"canonical_id": sid, "gold": rs["biasdetector"]["gold"]}
        for m in caches:
            row[f"pred_{m}"] = rs[m]["pred"]
            row[f"prob_{m}"] = rs[m]["prob_pos"]
            row[f"pred_type_{m}"] = pred_type(rs[m]["gold"], rs[m]["pred"])
            row[f"mean_abs_shap_{m}"] = mean_abs_shap(rs[m])
        for a, b, key in (
            ("biasdetector", "daroberta", "bd_dr"),
            ("biasdetector", "deberta", "bd_deb"),
            ("daroberta", "deberta", "dr_deb"),
        ):
            row[f"jaccard20_{key}"] = jaccard(top_k_words(rs[a]), top_k_words(rs[b]))
            row[f"cosine_abs_{key}"] = cosine_abs_aligned(rs[a], rs[b])
        paired_all3.append(row)

    write_csv(OUT / "basil_id_map.csv", id_map_rows)
    write_csv(OUT / "basil_coverage.csv", coverage)
    write_csv(OUT / "basil_strata_summary.csv", strata_summary)
    write_csv(OUT / "basil_paired_bd_dr.csv", paired_bd_dr)
    write_csv(OUT / "basil_pair_summary.csv", pair_summary)
    write_csv(OUT / "basil_paired_all3.csv", paired_all3)

    protocol = {
        "title": "Shared-sentence SHAP regeneration protocol (NOT EXECUTED)",
        "motivation": (
            f"BABE all3 intersection is small; BASIL all3={len(inter_all)} "
            "because DeBERTa only has magnitude strata."
        ),
        "steps": [
            "1. Build a shared sentence list S from BABE test intersection of "
            "confusion cells of interest (or full test) with seed=7.",
            "2. For BASIL, extend basil_shap_generate.build_manifest to emit "
            "fp_shared / fn_shared for deberta using the same keys as bd/dr.",
            "3. Run basil_shap_generate.py --models deberta on pending keys only "
            "(append-only JSONL; do not overwrite existing).",
            "4. Re-run paired analysis on the expanded intersection.",
            "5. Budget: ~15–20 s/sentence CPU historically; prefer sequential models on 8GB Mac.",
        ],
        "do_not_run_in_m1": True,
    }
    (OUT / "shared_shap_regen_protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )

    return {
        "n_bd_dr": len(inter_bd_dr),
        "n_all3": len(inter_all),
        "n_shared_fp": len(shared_fp),
        "n_shared_fn": len(shared_fn),
        "pair_summary": pair_summary,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    babe = audit_babe()
    basil = audit_basil()
    meta = {"babe": babe, "basil": basil}
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    print("[paired] BABE all3=", babe["n_all3"], "same_cell", babe["same_cell"])
    print(
        "[paired] BASIL bd∩dr=",
        basil["n_bd_dr"],
        "all3=",
        basil["n_all3"],
        "shared_FP=",
        basil["n_shared_fp"],
    )


if __name__ == "__main__":
    main()
