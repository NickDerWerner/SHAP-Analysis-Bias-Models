#!/usr/bin/env python3
"""ARR M2A — SHAP faithfulness pilot (20 BASIL sentences, BD + DA-RoBERTa).

Does not regenerate SHAP, retrain, or modify existing caches.
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
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from perturbations import (  # noqa: E402
    apply_mask,
    count_changed_whitespace_tokens,
    select_words,
)

OUT = ROOT / "outputs" / "arr_m2"
SEED = 7
BUDGETS = (1, 2, 3)
CONDITIONS = ("A_pos", "B_neg", "C_abs", "D_random", "E_lowabs")
STRATA_TARGET = {"TP": 5, "FP": 5, "TN": 5, "FN": 5}

MODELS = {
    "biasdetector": "himel7/bias-detector",
    "daroberta": "mediabiasgroup/DA-RoBERTa-BABE-FT",
}
CACHE = {
    "biasdetector": ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl",
    "daroberta": ROOT / "outputs" / "basil_shap" / "samples_daroberta.jsonl",
}

PROB_REPRO_TOL = 1e-3  # absolute |Δp| tolerance for unperturbed repro
MAX_LENGTH = 256


def peak_rss_mb() -> float:
    # macOS ru_maxrss is bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def pick_device(prefer_mps: bool = True) -> torch.device:
    if prefer_mps and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_jsonl(path: Path) -> List[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


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


def infer_positive_index(id2label) -> int:
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "bias" in s and not any(x in s for x in ["no", "non", "unbias", "neutral"]):
            return int(i)
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "biased" in s and not any(x in s for x in ["not", "no", "non"]):
            return int(i)
    return 1


def softmax_np(logits: np.ndarray) -> np.ndarray:
    x = logits - np.max(logits, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=-1, keepdims=True)


@torch.no_grad()
def predict_one(
    model, tokenizer, text: str, device: torch.device, positive_index: int
) -> Dict[str, float]:
    enc = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
        padding=False,
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    logits = model(**enc).logits[0].detach().float().cpu().numpy()
    probs = softmax_np(logits)
    # biased-class logit margin: logit_pos - logit_neg (binary)
    if logits.shape[-1] == 2:
        margin = float(logits[positive_index] - logits[1 - positive_index])
    else:
        # multiclass fallback: pos vs max other
        others = [logits[i] for i in range(len(logits)) if i != positive_index]
        margin = float(logits[positive_index] - max(others))
    return {
        "prob_pos": float(probs[positive_index]),
        "logit_margin": margin,
        "pred": int(probs[positive_index] >= 0.5),
        "logits": logits.tolist(),
    }


def build_intersection_pools() -> Dict[str, List[Tuple[str, dict, dict]]]:
    bd = {sid(r): r for r in load_jsonl(CACHE["biasdetector"])}
    dr = {sid(r): r for r in load_jsonl(CACHE["daroberta"])}
    common = set(bd) & set(dr)
    pools: Dict[str, List[Tuple[str, dict, dict]]] = defaultdict(list)
    for k in common:
        a, b = bd[k], dr[k]
        # require identical text
        if a["text"] != b["text"]:
            continue
        if a["gold"] != b["gold"]:
            continue
        ca = pred_type(int(a["gold"]), int(a["pred"]))
        cb = pred_type(int(b["gold"]), int(b["pred"]))
        if ca != cb:
            continue
        pools[ca].append((k, a, b))
    return pools


def sample_manifest(pools: Dict[str, List], seed: int = SEED) -> Tuple[List[dict], dict]:
    rng = random.Random(seed)
    rows = []
    notes = {
        "seed": seed,
        "targets": STRATA_TARGET,
        "available": {s: len(pools.get(s, [])) for s in STRATA_TARGET},
        "shortfalls": {},
        "tn_limitation": None,
        "design": (
            "Shared prediction cell for both models on identical BASIL text "
            "with cached SHAP in both JSONL files."
        ),
    }
    for stratum, n_want in STRATA_TARGET.items():
        pool = list(pools.get(stratum, []))
        rng.shuffle(pool)
        n_take = min(n_want, len(pool))
        if n_take < n_want:
            notes["shortfalls"][stratum] = {
                "requested": n_want,
                "available": len(pool),
                "taken": n_take,
            }
        if stratum == "TN" and len(pool) < n_want:
            notes["tn_limitation"] = (
                f"Only {len(pool)} shared TN sentences exist in the BD∩DR SHAP "
                f"cache intersection (requested {n_want}). Alternative not executed: "
                "regenerate SHAP for additional shared-TN keys from full BASIL "
                "predictions (both models pred=0, gold=0). Pilot uses all available "
                f"shared TNs (n={n_take}) without substituting unpaired or "
                "single-model sentences."
            )
        for rank, (k, a, b) in enumerate(pool[:n_take]):
            rows.append(
                {
                    "canonical_id": k,
                    "stratum": stratum,
                    "sample_rank": rank,
                    "triplet_uuid": a["triplet_uuid"],
                    "outlet_idx": int(a["outlet_idx"]),
                    "sentence_idx": int(a["sentence_idx"]),
                    "gold": int(a["gold"]),
                    "text": a["text"],
                    "prob_bd_cache": float(a["prob_pos"]),
                    "prob_dr_cache": float(b["prob_pos"]),
                    "pred_bd": int(a["pred"]),
                    "pred_dr": int(b["pred"]),
                    "n_words_bd": len(a.get("word_attribs") or []),
                    "n_words_dr": len(b.get("word_attribs") or []),
                }
            )
    notes["n_pilot_sentences"] = len(rows)
    return rows, notes


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # stable field order: union preserving first-seen
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


def bootstrap_mean_ci(values: List[float], n_boot: int = 2000, seed: int = SEED):
    if not values:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=float)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(float(sample.mean()))
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[int(0.975 * n_boot)]
    return float(arr.mean()), lo, hi


def load_model_pair(model_key: str, device: torch.device):
    hf_id = MODELS[model_key]
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(hf_id)
    model.eval()
    model.to(device)
    id2label = getattr(model.config, "id2label", {0: "NEG", 1: "POS"})
    # ensure int keys
    id2label = {int(k): v for k, v in id2label.items()}
    pos = infer_positive_index(id2label)
    mask_token = tokenizer.mask_token or "[MASK]"
    setup_s = time.time() - t0
    return {
        "key": model_key,
        "hf_id": hf_id,
        "tokenizer": tokenizer,
        "model": model,
        "positive_index": pos,
        "mask_token": mask_token,
        "id2label": id2label,
        "setup_s": setup_s,
    }


def run_pilot(device_name: str = "auto") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t_wall0 = time.time()
    rss0 = peak_rss_mb()

    if device_name == "auto":
        device = pick_device(True)
    elif device_name == "mps":
        device = pick_device(True)
    else:
        device = torch.device("cpu")

    pools = build_intersection_pools()
    manifest, notes = sample_manifest(pools, SEED)
    write_csv(OUT / "sampling_manifest.csv", manifest)
    (OUT / "sampling_notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")

    # Index caches for word_attribs
    caches = {
        "biasdetector": {sid(r): r for r in load_jsonl(CACHE["biasdetector"])},
        "daroberta": {sid(r): r for r in load_jsonl(CACHE["daroberta"])},
    }

    result_rows: List[dict] = []
    repro_rows: List[dict] = []
    unexpected: List[dict] = []
    bench = {
        "device": str(device),
        "rss_start_mb": rss0,
        "model_setup_s": {},
        "inference_s_total": 0.0,
        "n_forwards": 0,
        "peak_rss_mb": rss0,
    }

    # Process one model at a time to limit RAM
    for model_key in ("biasdetector", "daroberta"):
        print(f"[load] {model_key} on {device} ...")
        bundle = load_model_pair(model_key, device)
        bench["model_setup_s"][model_key] = bundle["setup_s"]
        rng = random.Random(SEED + (0 if model_key == "biasdetector" else 1))

        for mrow in manifest:
            cid = mrow["canonical_id"]
            rec = caches[model_key][cid]
            text = rec["text"]
            gold = int(rec["gold"])
            cache_p = float(rec["prob_pos"])
            was = rec.get("word_attribs") or []
            n_words = len(was)
            sent_len_ws = len(text.split())

            t1 = time.time()
            base = predict_one(
                bundle["model"], bundle["tokenizer"], text, device, bundle["positive_index"]
            )
            bench["inference_s_total"] += time.time() - t1
            bench["n_forwards"] += 1

            dp = abs(base["prob_pos"] - cache_p)
            repro_rows.append(
                {
                    "canonical_id": cid,
                    "model": model_key,
                    "stratum": mrow["stratum"],
                    "cache_prob_pos": cache_p,
                    "live_prob_pos": base["prob_pos"],
                    "abs_delta": dp,
                    "within_tol": int(dp <= PROB_REPRO_TOL),
                    "tol": PROB_REPRO_TOL,
                    "live_logit_margin": base["logit_margin"],
                    "live_pred": base["pred"],
                    "cache_pred": int(rec["pred"]),
                }
            )

            for cond in CONDITIONS:
                for budget in BUDGETS:
                    if budget > n_words:
                        continue
                    chosen = select_words(was, cond, budget, rng)
                    pert_text, meta = apply_mask(text, chosen, bundle["mask_token"])
                    n_changed = count_changed_whitespace_tokens(
                        text, pert_text, bundle["mask_token"]
                    )
                    # Control: applied count should equal budget if alignments succeed
                    over_changed = int(meta["n_applied"] > budget)

                    t1 = time.time()
                    out = predict_one(
                        bundle["model"],
                        bundle["tokenizer"],
                        pert_text,
                        device,
                        bundle["positive_index"],
                    )
                    bench["inference_s_total"] += time.time() - t1
                    bench["n_forwards"] += 1

                    d_prob = out["prob_pos"] - base["prob_pos"]
                    d_margin = out["logit_margin"] - base["logit_margin"]
                    flipped = int(out["pred"] != base["pred"])

                    # Directional expectation flags (not assumed to hold)
                    expect_dir = ""
                    if cond == "A_pos":
                        expect_dir = "d_prob<0"
                    elif cond == "B_neg":
                        expect_dir = "d_prob>0"

                    row = {
                        "canonical_id": cid,
                        "model": model_key,
                        "stratum": mrow["stratum"],
                        "gold": gold,
                        "condition": cond,
                        "budget": budget,
                        "n_word_attribs": n_words,
                        "sentence_n_ws_tokens": sent_len_ws,
                        "selected_words": "|".join(w["word"] for w in chosen),
                        "selected_shap": "|".join(f"{float(w['shap']):.6f}" for w in chosen),
                        "n_requested": meta["n_requested"],
                        "n_applied": meta["n_applied"],
                        "n_failed_align": meta["n_failed"],
                        "failed_words": "|".join(meta["failed_words"]),
                        "n_changed_ws_tokens": n_changed,
                        "over_budget_flag": over_changed,
                        "mask_token": bundle["mask_token"],
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
                        "flipped": flipped,
                        "expect_direction": expect_dir,
                        "direction_ok": (
                            int(d_prob < 0)
                            if cond == "A_pos"
                            else int(d_prob > 0)
                            if cond == "B_neg"
                            else ""
                        ),
                        "perturbed_text": pert_text,
                        "original_text": text,
                    }
                    result_rows.append(row)

                    # Flag unexpected directional failures for A/B
                    if cond == "A_pos" and d_prob > 0.02:
                        unexpected.append({**row, "why": "A_pos increased p_biased"})
                    if cond == "B_neg" and d_prob < -0.02:
                        unexpected.append({**row, "why": "B_neg decreased p_biased"})

        # free model before next
        del bundle["model"]
        if device.type == "mps":
            torch.mps.empty_cache()
        bench["peak_rss_mb"] = max(bench["peak_rss_mb"], peak_rss_mb())

    write_csv(OUT / "faithfulness_pilot_results.csv", result_rows)
    write_csv(OUT / "repro_check.csv", repro_rows)
    write_csv(OUT / "unexpected_cases.csv", unexpected)

    # --- summaries ---
    summary_rows = []
    # Repro summary
    for model_key in MODELS:
        sub = [r for r in repro_rows if r["model"] == model_key]
        summary_rows.append(
            {
                "section": "repro",
                "model": model_key,
                "stratum": "ALL",
                "condition": "unperturbed",
                "budget": "",
                "n": len(sub),
                "metric": "frac_within_tol",
                "value": sum(r["within_tol"] for r in sub) / len(sub) if sub else float("nan"),
                "ci95_lo": "",
                "ci95_hi": "",
                "mean_abs_delta_prob": (
                    sum(r["abs_delta"] for r in sub) / len(sub) if sub else float("nan")
                ),
            }
        )

    # Per model × condition × budget: mean delta_prob and paired vs random/low
    by_key = defaultdict(list)
    for r in result_rows:
        by_key[(r["model"], r["canonical_id"], r["budget"])].append(r)

    for model_key in MODELS:
        for stratum in list(STRATA_TARGET) + ["ALL"]:
            for cond in CONDITIONS:
                for budget in BUDGETS:
                    sub = [
                        r
                        for r in result_rows
                        if r["model"] == model_key
                        and r["condition"] == cond
                        and r["budget"] == budget
                        and (stratum == "ALL" or r["stratum"] == stratum)
                    ]
                    if not sub:
                        continue
                    vals = [r["delta_prob"] for r in sub]
                    mean, lo, hi = bootstrap_mean_ci(vals)
                    summary_rows.append(
                        {
                            "section": "delta_prob",
                            "model": model_key,
                            "stratum": stratum,
                            "condition": cond,
                            "budget": budget,
                            "n": len(sub),
                            "metric": "mean_delta_prob",
                            "value": mean,
                            "ci95_lo": lo,
                            "ci95_hi": hi,
                            "mean_abs_delta_prob": sum(r["abs_delta_prob"] for r in sub)
                            / len(sub),
                            "frac_direction_ok": (
                                sum(1 for r in sub if r["direction_ok"] == 1) / len(sub)
                                if cond in ("A_pos", "B_neg")
                                else ""
                            ),
                            "frac_flip": sum(r["flipped"] for r in sub) / len(sub),
                        }
                    )
                    # logit space separate
                    vals_l = [r["delta_logit_margin"] for r in sub]
                    mean_l, lo_l, hi_l = bootstrap_mean_ci(vals_l)
                    summary_rows.append(
                        {
                            "section": "delta_logit_margin",
                            "model": model_key,
                            "stratum": stratum,
                            "condition": cond,
                            "budget": budget,
                            "n": len(sub),
                            "metric": "mean_delta_logit_margin",
                            "value": mean_l,
                            "ci95_lo": lo_l,
                            "ci95_hi": hi_l,
                            "mean_abs_delta_prob": "",
                            "frac_direction_ok": "",
                            "frac_flip": "",
                        }
                    )

    # Paired contrasts: A_pos - D_random, C_abs - E_lowabs, C_abs - D_random
    contrasts = [
        ("A_pos", "D_random", "A_minus_random"),
        ("C_abs", "D_random", "C_minus_random"),
        ("C_abs", "E_lowabs", "C_minus_lowabs"),
        ("B_neg", "D_random", "B_minus_random"),
    ]
    for model_key in MODELS:
        for budget in BUDGETS:
            for c_a, c_b, name in contrasts:
                diffs = []
                for cid in {r["canonical_id"] for r in result_rows if r["model"] == model_key}:
                    ra = [
                        r
                        for r in result_rows
                        if r["model"] == model_key
                        and r["canonical_id"] == cid
                        and r["condition"] == c_a
                        and r["budget"] == budget
                    ]
                    rb = [
                        r
                        for r in result_rows
                        if r["model"] == model_key
                        and r["canonical_id"] == cid
                        and r["condition"] == c_b
                        and r["budget"] == budget
                    ]
                    if ra and rb:
                        # use abs delta for C contrasts; signed for A/B
                        if name.startswith("A_") or name.startswith("B_"):
                            # A should be more negative than random → diff = dA - dR (expect <0 for A)
                            diffs.append(ra[0]["delta_prob"] - rb[0]["delta_prob"])
                        else:
                            diffs.append(ra[0]["abs_delta_prob"] - rb[0]["abs_delta_prob"])
                if not diffs:
                    continue
                mean, lo, hi = bootstrap_mean_ci(diffs)
                summary_rows.append(
                    {
                        "section": "paired_contrast",
                        "model": model_key,
                        "stratum": "ALL",
                        "condition": name,
                        "budget": budget,
                        "n": len(diffs),
                        "metric": "mean_paired_diff",
                        "value": mean,
                        "ci95_lo": lo,
                        "ci95_hi": hi,
                    }
                )

    write_csv(OUT / "faithfulness_pilot_summary.csv", summary_rows)

    # Figure: mean delta_prob by condition for budget=2 (clearest mid budget)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
        for ax, model_key in zip(axes, MODELS):
            means = []
            los = []
            his = []
            labels = []
            for cond in CONDITIONS:
                hit = [
                    r
                    for r in summary_rows
                    if r["section"] == "delta_prob"
                    and r["model"] == model_key
                    and r["stratum"] == "ALL"
                    and r["condition"] == cond
                    and r["budget"] == 2
                ]
                if not hit:
                    continue
                labels.append(cond)
                means.append(float(hit[0]["value"]))
                los.append(float(hit[0]["ci95_lo"]))
                his.append(float(hit[0]["ci95_hi"]))
            x = np.arange(len(labels))
            yerr = np.vstack(
                [np.array(means) - np.array(los), np.array(his) - np.array(means)]
            )
            colors = ["#c0392b", "#2980b9", "#8e44ad", "#7f8c8d", "#27ae60"]
            ax.bar(x, means, yerr=yerr, color=colors[: len(labels)], capsize=3)
            ax.axhline(0, color="black", lw=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=30, ha="right")
            ax.set_title(model_key)
            ax.set_ylabel("Mean Δ P(biased)")
        fig.suptitle(
            "Faithfulness pilot (budget=2): SHAP-selected vs controls\n"
            f"n={notes['n_pilot_sentences']} shared BASIL sentences; 95% bootstrap CIs"
        )
        fig.tight_layout()
        fig.savefig(OUT / "faithfulness_pilot_figure.png", dpi=150, bbox_inches="tight")
        fig.savefig(OUT / "faithfulness_pilot_figure.pdf", bbox_inches="tight")
        plt.close(fig)
    except Exception as e:
        (OUT / "figure_error.txt").write_text(str(e), encoding="utf-8")

    bench["wall_s"] = time.time() - t_wall0
    bench["peak_rss_mb"] = max(bench["peak_rss_mb"], peak_rss_mb())
    bench["n_pilot_sentences"] = notes["n_pilot_sentences"]
    bench["n_result_rows"] = len(result_rows)
    # Scaling extrapolations (linear in forwards; uncertain)
    fwd_per_sent = bench["n_forwards"] / max(notes["n_pilot_sentences"], 1)
    s_per_fwd = bench["inference_s_total"] / max(bench["n_forwards"], 1)
    for n in (200, 1000):
        bench[f"est_wall_s_{n}"] = (
            sum(bench["model_setup_s"].values())
            + n * fwd_per_sent * s_per_fwd
        )
        bench[f"est_hours_{n}"] = bench[f"est_wall_s_{n}"] / 3600
    bench["scaling_note"] = (
        "Linear extrapolation from pilot forwards only; ignores thermal throttling, "
        "MPS fragmentation, and longer sentences. Treat as ±50% uncertain."
    )
    bench["repro_tol"] = PROB_REPRO_TOL
    bench["shortfalls"] = notes.get("shortfalls")
    bench["tn_limitation"] = notes.get("tn_limitation")
    (OUT / "benchmark.json").write_text(json.dumps(bench, indent=2), encoding="utf-8")

    print("[done] sentences", notes["n_pilot_sentences"], "rows", len(result_rows))
    print("[done] shortfalls", notes.get("shortfalls"))
    print("[done] device", device, "wall_s", round(bench["wall_s"], 1), "peak_rss_mb", round(bench["peak_rss_mb"], 1))
    print("[done] outputs ->", OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", choices=["auto", "mps", "cpu"], default="auto")
    args = ap.parse_args()
    # Reduce MPS memory pressure
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    run_pilot(args.device)


if __name__ == "__main__":
    main()
