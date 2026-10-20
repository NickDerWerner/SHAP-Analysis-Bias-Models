#!/usr/bin/env python3
"""ARR M2B — offset-aware faithfulness (18-sentence regression + ~200-scale).

Preserves M1/M2A/original caches. Writes only under outputs/arr_m2b/.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))

from offset_alignment import (  # noqa: E402
    AlignmentResult,
    align_record,
    apply_mask_offsets,
    select_source_words,
)

OUT = ROOT / "outputs" / "arr_m2b"
M2A_MANIFEST = ROOT / "outputs" / "arr_m2" / "sampling_manifest.csv"
SEED = 7
BUDGETS = (1, 2, 3)
CONDITIONS = ("A_pos", "B_neg", "C_abs", "D_random", "E_lowabs")
N_RANDOM_REPEATS = 3  # variability for random control
ALIGN_GATE = 0.99  # required successful complete-budget rate on eligible rows
PROB_REPRO_TOL = 1e-3
MAX_LENGTH = 256
MEDIUM_TARGET = 200

MODELS = {
    "biasdetector": "himel7/bias-detector",
    "daroberta": "mediabiasgroup/DA-RoBERTa-BABE-FT",
}
CACHE = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
}


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def pick_device(name: str) -> torch.device:
    if name == "cpu":
        return torch.device("cpu")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def sid(r: dict) -> str:
    return f"basil:{r['triplet_uuid']}|{int(r['outlet_idx'])}|{int(r['sentence_idx'])}"


def pred_type(gold: int, pred: int) -> str:
    if gold == 1 and pred == 1:
        return "TP"
    if gold == 0 and pred == 1:
        return "FP"
    if gold == 0 and pred == 0:
        return "TN"
    return "FN"


def load_jsonl(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f]


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


def infer_positive_index(id2label) -> int:
    id2label = {int(k): v for k, v in id2label.items()}
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "bias" in s and not any(x in s for x in ["no", "non", "unbias", "neutral"]):
            return int(i)
    return 1


def softmax_np(logits: np.ndarray) -> np.ndarray:
    x = logits - np.max(logits, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=-1, keepdims=True)


@torch.no_grad()
def predict_one(model, tokenizer, text, device, positive_index):
    enc = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=MAX_LENGTH, padding=False
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    logits = model(**enc).logits[0].detach().float().cpu().numpy()
    probs = softmax_np(logits)
    if logits.shape[-1] == 2:
        margin = float(logits[positive_index] - logits[1 - positive_index])
    else:
        others = [logits[i] for i in range(len(logits)) if i != positive_index]
        margin = float(logits[positive_index] - max(others))
    return {
        "prob_pos": float(probs[positive_index]),
        "logit_margin": margin,
        "pred": int(probs[positive_index] >= 0.5),
    }


def bootstrap_mean_ci(values: List[float], n_boot: int = 2000, seed: int = SEED):
    if not values:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = sorted(float(rng.choice(arr, size=len(arr), replace=True).mean()) for _ in range(n_boot))
    return float(arr.mean()), means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def load_caches():
    return {m: {sid(r): r for r in load_jsonl(p)} for m, p in CACHE.items()}


def build_paired_pools(caches):
    common = set(caches["biasdetector"]) & set(caches["daroberta"])
    pools = defaultdict(list)
    for k in common:
        a, b = caches["biasdetector"][k], caches["daroberta"][k]
        if a["text"] != b["text"] or a["gold"] != b["gold"]:
            continue
        ca = pred_type(int(a["gold"]), int(a["pred"]))
        cb = pred_type(int(b["gold"]), int(b["pred"]))
        if ca != cb:
            continue
        pools[ca].append(k)
    return pools


def audit_alignment(caches, sentence_ids: List[str], models: Sequence[str]) -> List[dict]:
    rows = []
    for cid in sentence_ids:
        for m in models:
            rec = caches[m][cid]
            al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
            rows.append(
                {
                    "canonical_id": cid,
                    "model": m,
                    "n_source_words": len(al.words),
                    "n_shap_tokens_content": al.n_shap_tokens_content,
                    "n_shap_tokens_aligned": al.n_shap_tokens_aligned,
                    "token_align_rate": al.token_align_rate,
                    "alignment_ok": int(al.alignment_ok),
                    "n_unaligned": len(al.unaligned_token_indices),
                    "unaligned_preview": "|".join(al.unaligned_token_strs[:8]),
                }
            )
    return rows


def sample_medium(pools, seed=SEED, target=MEDIUM_TARGET) -> Tuple[List[dict], dict]:
    """~200 paired sentences, stratified; document shortfalls."""
    rng = random.Random(seed)
    # Allocate proportionally but cap by availability; aim balanced
    strata = ["TP", "FP", "TN", "FN"]
    avail = {s: list(pools.get(s, [])) for s in strata}
    for s in strata:
        rng.shuffle(avail[s])

    # Ideal equal split 50 each; TN scarce
    ideal = {s: target // 4 for s in strata}
    take = {s: min(ideal[s], len(avail[s])) for s in strata}
    remaining = target - sum(take.values())
    # Fill remainder from largest remaining pools (usually TP/FN/FP)
    while remaining > 0:
        candidates = [s for s in strata if len(avail[s]) > take[s]]
        if not candidates:
            break
        # prefer non-TN first for balance documentation
        candidates.sort(key=lambda s: (0 if s != "TN" else 1, -(len(avail[s]) - take[s])))
        s = candidates[0]
        take[s] += 1
        remaining -= 1

    rows = []
    for s in strata:
        for rank, k in enumerate(avail[s][: take[s]]):
            rows.append({"canonical_id": k, "stratum": s, "sample_rank": rank, "pair_scope": "paired"})
    notes = {
        "seed": seed,
        "target": target,
        "available": {s: len(avail[s]) for s in strata},
        "taken": take,
        "n": len(rows),
        "tn_note": (
            f"Only {len(avail['TN'])} shared TN in SHAP intersection; taken {take['TN']}."
        ),
    }
    return rows, notes


def load_m2a_manifest() -> List[dict]:
    with M2A_MANIFEST.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_phase(
    name: str,
    sentence_rows: List[dict],
    caches: dict,
    device: torch.device,
    models: Sequence[str],
    random_repeats: int,
    out_prefix: str,
) -> Dict[str, Any]:
    """Run faithfulness for a sentence list; return bench + gate stats."""
    ids = [r["canonical_id"] for r in sentence_rows]
    stratum_of = {r["canonical_id"]: r["stratum"] for r in sentence_rows}

    align_rows = audit_alignment(caches, ids, models)
    write_csv(OUT / f"{out_prefix}_alignment_audit.csv", align_rows)

    # Eligible: alignment_ok for the model being evaluated
    ok_ids = {
        m: {r["canonical_id"] for r in align_rows if r["model"] == m and r["alignment_ok"] == 1}
        for m in models
    }

    result_rows: List[dict] = []
    repro_rows: List[dict] = []
    fail_rows: List[dict] = []
    bench = {
        "phase": name,
        "device": str(device),
        "n_sentences_requested": len(ids),
        "model_setup_s": {},
        "inference_s": 0.0,
        "n_forwards": 0,
        "peak_rss_mb": peak_rss_mb(),
        "wall_s0": time.time(),
    }

    n_attempted = 0
    n_complete = 0
    n_excluded_incomplete = 0
    n_excluded_bad_align = 0

    for model_key in models:
        print(f"[{name}] load {model_key} on {device}")
        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(MODELS[model_key], use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(MODELS[model_key])
        model.eval().to(device)
        pos = infer_positive_index(getattr(model.config, "id2label", {0: "NEG", 1: "POS"}))
        mask_token = tok.mask_token or "[MASK]"
        bench["model_setup_s"][model_key] = time.time() - t0

        for cid in ids:
            rec = caches[model_key][cid]
            text = rec["text"]
            gold = int(rec["gold"])
            stratum = stratum_of[cid]

            if cid not in ok_ids[model_key]:
                n_excluded_bad_align += 1
                fail_rows.append(
                    {
                        "phase": name,
                        "canonical_id": cid,
                        "model": model_key,
                        "reason": "alignment_ok=false",
                        "stratum": stratum,
                    }
                )
                continue

            al = align_record(text, rec["tokens"], rec["shap_pos"])
            assert al.alignment_ok

            t1 = time.time()
            base = predict_one(model, tok, text, device, pos)
            bench["inference_s"] += time.time() - t1
            bench["n_forwards"] += 1

            repro_rows.append(
                {
                    "phase": name,
                    "canonical_id": cid,
                    "model": model_key,
                    "cache_prob": float(rec["prob_pos"]),
                    "live_prob": base["prob_pos"],
                    "abs_delta": abs(base["prob_pos"] - float(rec["prob_pos"])),
                    "within_tol": int(abs(base["prob_pos"] - float(rec["prob_pos"])) <= PROB_REPRO_TOL),
                }
            )

            for cond in CONDITIONS:
                repeats = N_RANDOM_REPEATS if cond == "D_random" else 1
                # cap repeats for regression speed optionally via arg
                repeats = min(repeats, random_repeats) if cond == "D_random" else 1
                for rep in range(repeats):
                    rng = random.Random(SEED + hash((cid, model_key, cond, rep)) % 10_000_000)
                    for budget in BUDGETS:
                        if budget > len(al.words):
                            continue
                        n_attempted += 1
                        chosen = select_source_words(al.words, cond, budget, rng)
                        pert, meta = apply_mask_offsets(text, chosen, mask_token)
                        if not meta["complete_budget"]:
                            n_excluded_incomplete += 1
                            fail_rows.append(
                                {
                                    "phase": name,
                                    "canonical_id": cid,
                                    "model": model_key,
                                    "reason": "incomplete_budget",
                                    "condition": cond,
                                    "budget": budget,
                                    "n_applied": meta["n_applied"],
                                    "failed_words": "|".join(meta["failed_words"]),
                                }
                            )
                            # predefined rule: exclude — do not keep underfilled row as success
                            continue
                        n_complete += 1
                        t1 = time.time()
                        out = predict_one(model, tok, pert, device, pos)
                        bench["inference_s"] += time.time() - t1
                        bench["n_forwards"] += 1

                        d_prob = out["prob_pos"] - base["prob_pos"]
                        d_margin = out["logit_margin"] - base["logit_margin"]
                        result_rows.append(
                            {
                                "phase": name,
                                "canonical_id": cid,
                                "model": model_key,
                                "stratum": stratum,
                                "pair_scope": "paired",
                                "gold": gold,
                                "condition": cond,
                                "random_rep": rep,
                                "budget": budget,
                                "n_source_words": len(al.words),
                                "selected_words": "|".join(w.surface for w in chosen),
                                "selected_shap": "|".join(f"{w.shap:.6f}" for w in chosen),
                                "n_applied": meta["n_applied"],
                                "complete_budget": 1,
                                "mask_token": mask_token,
                                "orig_prob": base["prob_pos"],
                                "pert_prob": out["prob_pos"],
                                "delta_prob": d_prob,
                                "abs_delta_prob": abs(d_prob),
                                "orig_logit_margin": base["logit_margin"],
                                "pert_logit_margin": out["logit_margin"],
                                "delta_logit_margin": d_margin,
                                "abs_delta_logit_margin": abs(d_margin),
                                "orig_pred": base["pred"],
                                "pert_pred": out["pred"],
                                "flipped": int(out["pred"] != base["pred"]),
                                "direction_ok": (
                                    int(d_prob < 0)
                                    if cond == "A_pos"
                                    else int(d_prob > 0)
                                    if cond == "B_neg"
                                    else ""
                                ),
                            }
                        )

        del model
        if device.type == "mps":
            torch.mps.empty_cache()
        bench["peak_rss_mb"] = max(bench["peak_rss_mb"], peak_rss_mb())

    bench["wall_s"] = time.time() - bench.pop("wall_s0")
    bench["n_attempted_perturbations"] = n_attempted
    bench["n_complete_perturbations"] = n_complete
    bench["n_excluded_incomplete"] = n_excluded_incomplete
    bench["n_excluded_bad_align"] = n_excluded_bad_align
    bench["complete_rate"] = (n_complete / n_attempted) if n_attempted else float("nan")
    bench["sentence_align_ok_rate"] = {
        m: (len(ok_ids[m]) / len(ids) if ids else float("nan")) for m in models
    }

    write_csv(OUT / f"{out_prefix}_results.csv", result_rows)
    write_csv(OUT / f"{out_prefix}_repro.csv", repro_rows)
    write_csv(OUT / f"{out_prefix}_exclusions.csv", fail_rows)

    summary = summarize(result_rows, name)
    write_csv(OUT / f"{out_prefix}_summary.csv", summary)

    return {
        "bench": bench,
        "results": result_rows,
        "summary": summary,
        "align_rows": align_rows,
        "gate_pass": bool(bench["complete_rate"] >= ALIGN_GATE),
    }


def summarize(result_rows: List[dict], phase: str) -> List[dict]:
    """Sentence-level aggregation: for random, mean over reps first."""
    # Aggregate random reps → one value per (model,cid,condition,budget)
    grouped = defaultdict(list)
    for r in result_rows:
        key = (r["model"], r["canonical_id"], r["condition"], int(r["budget"]), r["stratum"])
        grouped[key].append(r)

    collapsed = []
    for key, rs in grouped.items():
        model, cid, cond, budget, stratum = key
        collapsed.append(
            {
                "model": model,
                "canonical_id": cid,
                "condition": cond,
                "budget": budget,
                "stratum": stratum,
                "delta_prob": float(np.mean([x["delta_prob"] for x in rs])),
                "abs_delta_prob": float(np.mean([x["abs_delta_prob"] for x in rs])),
                "delta_logit_margin": float(np.mean([x["delta_logit_margin"] for x in rs])),
                "direction_ok": (
                    int(np.mean([x["delta_prob"] for x in rs]) < 0)
                    if cond == "A_pos"
                    else int(np.mean([x["delta_prob"] for x in rs]) > 0)
                    if cond == "B_neg"
                    else ""
                ),
                "flipped": int(np.mean([x["flipped"] for x in rs]) >= 0.5),
            }
        )

    out = []
    models = sorted({c["model"] for c in collapsed})
    for model in models:
        for stratum in ["ALL", "TP", "FP", "TN", "FN"]:
            for cond in CONDITIONS:
                for budget in BUDGETS:
                    sub = [
                        c
                        for c in collapsed
                        if c["model"] == model
                        and c["condition"] == cond
                        and c["budget"] == budget
                        and (stratum == "ALL" or c["stratum"] == stratum)
                    ]
                    if not sub:
                        continue
                    # sentence-level bootstrap
                    vals = [c["delta_prob"] for c in sub]
                    mean, lo, hi = bootstrap_mean_ci(vals)
                    abs_vals = [c["abs_delta_prob"] for c in sub]
                    am, alo, ahi = bootstrap_mean_ci(abs_vals)
                    lm = [c["delta_logit_margin"] for c in sub]
                    lmean, llo, lhi = bootstrap_mean_ci(lm)
                    out.append(
                        {
                            "phase": phase,
                            "section": "delta_prob",
                            "model": model,
                            "stratum": stratum,
                            "condition": cond,
                            "budget": budget,
                            "n_sentences": len(sub),
                            "mean": mean,
                            "ci95_lo": lo,
                            "ci95_hi": hi,
                            "mean_abs": am,
                            "abs_ci95_lo": alo,
                            "abs_ci95_hi": ahi,
                            "mean_delta_logit": lmean,
                            "logit_ci95_lo": llo,
                            "logit_ci95_hi": lhi,
                            "frac_direction_ok": (
                                sum(1 for c in sub if c["direction_ok"] == 1) / len(sub)
                                if cond in ("A_pos", "B_neg")
                                else ""
                            ),
                            "frac_flip": sum(c["flipped"] for c in sub) / len(sub),
                        }
                    )

        # paired contrasts at sentence level
        for budget in BUDGETS:
            for ca, cb, name in (
                ("A_pos", "D_random", "A_minus_random"),
                ("B_neg", "D_random", "B_minus_random"),
                ("C_abs", "D_random", "C_minus_random_abs"),
                ("C_abs", "E_lowabs", "C_minus_lowabs_abs"),
            ):
                diffs = []
                by_cid = defaultdict(dict)
                for c in collapsed:
                    if c["model"] == model and c["budget"] == budget:
                        by_cid[c["canonical_id"]][c["condition"]] = c
                for cid, d in by_cid.items():
                    if ca in d and cb in d:
                        if "abs" in name:
                            diffs.append(d[ca]["abs_delta_prob"] - d[cb]["abs_delta_prob"])
                        else:
                            diffs.append(d[ca]["delta_prob"] - d[cb]["delta_prob"])
                if not diffs:
                    continue
                mean, lo, hi = bootstrap_mean_ci(diffs)
                out.append(
                    {
                        "phase": phase,
                        "section": "paired_contrast",
                        "model": model,
                        "stratum": "ALL",
                        "condition": name,
                        "budget": budget,
                        "n_sentences": len(diffs),
                        "mean": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                    }
                )
    return out


def compare_m2a(new_summary: List[dict], old_summary_path: Path) -> List[dict]:
    if not old_summary_path.exists():
        return []
    old = list(csv.DictReader(old_summary_path.open()))
    rows = []
    for ns in new_summary:
        if ns.get("section") != "delta_prob" or ns.get("stratum") != "ALL":
            continue
        hits = [
            o
            for o in old
            if o.get("section") == "delta_prob"
            and o.get("stratum") == "ALL"
            and o.get("model") == ns["model"]
            and o.get("condition") == ns["condition"]
            and str(o.get("budget")) == str(ns["budget"])
        ]
        if not hits:
            continue
        o = hits[0]
        old_v = float(o["value"])
        new_v = float(ns["mean"])
        rows.append(
            {
                "model": ns["model"],
                "condition": ns["condition"],
                "budget": ns["budget"],
                "m2a_mean_delta_prob": old_v,
                "m2b_mean_delta_prob": new_v,
                "delta_change": new_v - old_v,
                "m2a_ci_lo": o.get("ci95_lo"),
                "m2a_ci_hi": o.get("ci95_hi"),
                "m2b_ci_lo": ns["ci95_lo"],
                "m2b_ci_hi": ns["ci95_hi"],
                "sign_same": int((old_v < 0 and new_v < 0) or (old_v > 0 and new_v > 0) or (old_v == 0 and new_v == 0)),
            }
        )
    return rows


def make_figures(summary: List[dict], tag: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = OUT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for budget in BUDGETS:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
        for ax, model in zip(axes, MODELS):
            labels, means, los, his = [], [], [], []
            for cond in CONDITIONS:
                hits = [
                    r
                    for r in summary
                    if r.get("section") == "delta_prob"
                    and r.get("stratum") == "ALL"
                    and r.get("model") == model
                    and r.get("condition") == cond
                    and int(r.get("budget")) == budget
                ]
                if not hits:
                    continue
                labels.append(cond)
                means.append(float(hits[0]["mean"]))
                los.append(float(hits[0]["ci95_lo"]))
                his.append(float(hits[0]["ci95_hi"]))
            if not labels:
                continue
            x = np.arange(len(labels))
            yerr = np.vstack([np.array(means) - np.array(los), np.array(his) - np.array(means)])
            colors = ["#c0392b", "#2980b9", "#8e44ad", "#95a5a6", "#27ae60"]
            ax.bar(x, means, yerr=yerr, color=colors[: len(labels)], capsize=3, width=0.75)
            ax.axhline(0, color="black", lw=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=25, ha="right")
            ax.set_title(model)
            ax.set_ylabel("Mean Δ P(biased)")
        fig.suptitle(
            f"M2B faithfulness ({tag}, budget={budget}): SHAP targets vs controls\n"
            "Sentence-level means; 95% bootstrap CIs"
        )
        fig.tight_layout()
        fig.savefig(fig_dir / f"faithfulness_{tag}_budget{budget}.png", dpi=160, bbox_inches="tight")
        fig.savefig(fig_dir / f"faithfulness_{tag}_budget{budget}.pdf", bbox_inches="tight")
        plt.close(fig)

    # Absolute-effect panel budget=2
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, model in zip(axes, MODELS):
        labs, vals, elo, ehi = [], [], [], []
        for cond in ("C_abs", "D_random", "E_lowabs"):
            hits = [
                r
                for r in summary
                if r.get("section") == "delta_prob"
                and r.get("stratum") == "ALL"
                and r.get("model") == model
                and r.get("condition") == cond
                and int(r.get("budget")) == 2
            ]
            if not hits:
                continue
            labs.append(cond)
            vals.append(float(hits[0]["mean_abs"]))
            elo.append(float(hits[0]["abs_ci95_lo"]))
            ehi.append(float(hits[0]["abs_ci95_hi"]))
        x = np.arange(len(labs))
        yerr = np.vstack([np.array(vals) - np.array(elo), np.array(ehi) - np.array(vals)])
        ax.bar(x, vals, yerr=yerr, color=["#8e44ad", "#95a5a6", "#27ae60"], capsize=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labs)
        ax.set_title(model)
        ax.set_ylabel("Mean |Δ P(biased)|")
    fig.suptitle(f"M2B absolute sensitivity ({tag}, budget=2)")
    fig.tight_layout()
    fig.savefig(fig_dir / f"abs_sensitivity_{tag}_budget2.png", dpi=160, bbox_inches="tight")
    fig.savefig(fig_dir / f"abs_sensitivity_{tag}_budget2.pdf", bbox_inches="tight")
    plt.close(fig)


def optional_sufficiency(
    caches, sentence_rows, device, models, n_max: int = 40
) -> Optional[List[dict]]:
    """Complementary: keep top-|SHAP| words, mask the rest; compare to random keep.

    Documented as OOD-heavy; limited subsample.
    """
    rng = random.Random(SEED)
    ids = [r["canonical_id"] for r in sentence_rows]
    rng.shuffle(ids)
    ids = ids[:n_max]
    rows = []
    for model_key in models:
        tok = AutoTokenizer.from_pretrained(MODELS[model_key], use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(MODELS[model_key])
        model.eval().to(device)
        pos = infer_positive_index(getattr(model.config, "id2label", {0: "NEG", 1: "POS"}))
        mask_token = tok.mask_token or "[MASK]"
        for cid in ids:
            rec = caches[model_key][cid]
            al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
            if not al.alignment_ok or len(al.words) < 4:
                continue
            base = predict_one(model, tok, rec["text"], device, pos)
            k = max(1, len(al.words) // 5)  # keep ~20%
            keep_shap = select_source_words(al.words, "C_abs", k, rng)
            keep_rand = select_source_words(al.words, "D_random", k, rng)
            for label, keep in (("keep_high_abs", keep_shap), ("keep_random", keep_rand)):
                keep_idx = {w.index for w in keep}
                drop = [w for w in al.words if w.index not in keep_idx]
                pert, meta = apply_mask_offsets(rec["text"], drop, mask_token)
                if not meta["complete_budget"]:
                    continue
                out = predict_one(model, tok, pert, device, pos)
                rows.append(
                    {
                        "canonical_id": cid,
                        "model": model_key,
                        "condition": label,
                        "n_keep": k,
                        "n_masked": len(drop),
                        "orig_prob": base["prob_pos"],
                        "pert_prob": out["prob_pos"],
                        "abs_delta_prob": abs(out["prob_pos"] - base["prob_pos"]),
                        "same_pred": int(out["pred"] == base["pred"]),
                    }
                )
        del model
        if device.type == "mps":
            torch.mps.empty_cache()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="auto", choices=["auto", "mps", "cpu"])
    ap.add_argument("--skip-medium", action="store_true")
    ap.add_argument("--random-repeats", type=int, default=N_RANDOM_REPEATS)
    ap.add_argument("--medium-n", type=int, default=MEDIUM_TARGET)
    ap.add_argument("--sufficiency", action="store_true", help="Run optional keep-top sufficiency subsample")
    args = ap.parse_args()
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)

    device = pick_device("cpu" if args.device == "cpu" else "auto")
    caches = load_caches()
    pools = build_paired_pools(caches)

    # --- Phase 1: M2A regression ---
    m2a = load_m2a_manifest()
    write_csv(
        OUT / "regression_manifest.csv",
        [{"canonical_id": r["canonical_id"], "stratum": r["stratum"]} for r in m2a],
    )
    reg = run_phase(
        "regression_m2a18",
        [{"canonical_id": r["canonical_id"], "stratum": r["stratum"]} for r in m2a],
        caches,
        device,
        list(MODELS),
        random_repeats=1,  # match M2A single random for comparability
        out_prefix="regression",
    )
    # Also copy primary names required by user for final medium; regression kept separate
    cmp = compare_m2a(reg["summary"], ROOT / "outputs" / "arr_m2" / "faithfulness_pilot_summary.csv")
    write_csv(OUT / "m2a_vs_m2b_regression_compare.csv", cmp)
    make_figures(reg["summary"], "regression")

    print(
        f"[gate] complete_rate={reg['bench']['complete_rate']:.4f} "
        f"align_ok={reg['bench']['sentence_align_ok_rate']} pass={reg['gate_pass']}"
    )

    meta = {"regression": reg["bench"], "gate_pass": reg["gate_pass"], "compare_n": len(cmp)}
    if not reg["gate_pass"]:
        (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print("[STOP] Alignment gate failed; not running medium-scale.")
        return

    if args.skip_medium:
        (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return

    # --- Phase 2: medium scale ---
    med_rows, med_notes = sample_medium(pools, SEED, args.medium_n)
    write_csv(OUT / "medium_sampling_manifest.csv", med_rows)
    (OUT / "medium_sampling_notes.json").write_text(json.dumps(med_notes, indent=2), encoding="utf-8")

    med = run_phase(
        "medium",
        med_rows,
        caches,
        device,
        list(MODELS),
        random_repeats=args.random_repeats,
        out_prefix="medium",
    )
    # User-requested canonical filenames (medium is the main experiment)
    write_csv(OUT / "faithfulness_results.csv", med["results"])
    write_csv(OUT / "faithfulness_summary.csv", med["summary"])
    write_csv(OUT / "alignment_audit.csv", med["align_rows"])
    make_figures(med["summary"], "medium")

    if args.sufficiency:
        suf = optional_sufficiency(caches, med_rows, device, list(MODELS))
        if suf:
            write_csv(OUT / "sufficiency_subsample.csv", suf)

    meta["medium"] = med["bench"]
    meta["medium_notes"] = med_notes
    meta["medium_gate_pass"] = med["gate_pass"]
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    print("[done] medium n=", med_notes["n"], "complete_rate=", med["bench"]["complete_rate"])


if __name__ == "__main__":
    main()
