#!/usr/bin/env python3
"""BASIL SHAP attribution generator — resumable, long-running.

Builds per-sentence SHAP attributions for both bias-detector and DA-RoBERTa
across the strata required by the BASIL SHAP phase (magnitude, bias-type,
three-way FP partition, shared lex-only FN). Writes append-only JSONL caches
keyed by (triplet_uuid, outlet_idx, sentence_idx) — safe to interrupt and
resume by re-running the same command.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python basil_shap_generate.py [--limit N] [--seed 7] \
      [--models biasdetector,daroberta]

Outputs (under outputs/basil_shap/):
  manifest.csv                  full (model, sentence_id, stratum) listing
  samples_biasdetector.jsonl    per-sentence SHAP records, bias-detector
  samples_daroberta.jsonl       per-sentence SHAP records, DA-RoBERTa
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import torch
import shap
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from basil_eval import MODELS, load_joined


# ---------------------------------------------------------------------------
# Copied verbatim from analysis.py so this script doesn't transitively import
# `datasets` (and any other heavy top-level deps in analysis.py). Behaviour
# must stay identical to the original BABE pipeline — do not modify.
# ---------------------------------------------------------------------------

def softmax_np(logits: np.ndarray) -> np.ndarray:
    x = logits - np.max(logits, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)


def infer_positive_index(id2label):
    candidates = []
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "bias" in s and not any(x in s for x in ["no", "non", "unbias", "neutral"]):
            candidates.append(i)
    if len(candidates) == 1:
        return int(candidates[0])
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "biased" in s and not any(x in s for x in ["not", "no", "non"]):
            return int(i)
    return 1


def build_predict_fn(model, tokenizer, device, max_length, positive_index):
    def predict(texts):
        # SHAP's Text masker hands us a numpy ndarray of np.str_ items.
        # transformers 5.x's tokenizer rejects numpy types — coerce to plain
        # Python str / list[str] before calling.
        if hasattr(texts, "tolist"):
            texts = texts.tolist()
        elif isinstance(texts, str):
            texts = [texts]
        texts = [str(t) for t in texts]
        enc = tokenizer(texts, padding=True, truncation=True,
                        max_length=max_length, return_tensors="pt")
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits.detach().cpu().numpy()
        return softmax_np(logits)
    return predict


_PUNCT_RE = re.compile(r"^\W+$", re.UNICODE)


def aggregate_subword_shap_to_words(tokens, shap_values, *,
                                    merge_punct_into_previous: bool = True
                                    ) -> List[Tuple[str, float]]:
    """Aggregate per-token SHAP into per-word attributions.

    Copied verbatim from analysis.ipynb cell 3 — the version that actually
    produced the stored BABE word_attribs in outputs/shap_samples237.jsonl
    and outputs/shap_samples_daroberta.jsonl. The simpler variant in
    analysis.py is a divergent copy that does not handle whitespace-cued
    word boundaries (the format produced by shap 0.51's Text masker).

    Handles three token styles:
      * Whitespace-cued (modern shap.maskers.Text): tokens like
        ['A ', 'push ', 'by ', 'late', '-', 'term ']. Leading/trailing space
        in the raw token marks word boundaries.
      * Ġ/▁-prefixed (legacy BPE marker): each Ġ/▁ token starts a new word.
      * Continuations (no marker, no whitespace): glue onto the running word
        — so 'erupt' + 'ing ' → 'erupting'.

    `merge_punct_into_previous=True` attaches pure-punctuation tokens to the
    preceding word (matches the BABE-stored format, e.g. 'viral.').
    """
    out: List[Tuple[str, float]] = []
    cur_word = ""
    cur_sum = 0.0
    prev_clean = ""

    def flush():
        nonlocal cur_word, cur_sum, prev_clean
        w = cur_word.strip()
        if w != "":
            out.append((w, float(cur_sum)))
        cur_word = ""
        cur_sum = 0.0
        prev_clean = ""

    def should_split_word(prev_clean: str, current_clean: str) -> bool:
        if not prev_clean or not current_clean:
            return False
        if prev_clean[-1].islower() and current_clean[0].isupper():
            return True
        common_endings = ['day', 'ing', 'ed', 'ly', 'er', 'tion', 'ment',
                          'ism', 'ist', 'ous', 'ful', 'ness']
        pl = prev_clean.lower()
        for ending in common_endings:
            if pl.endswith(ending) and len(prev_clean) >= len(ending) + 2:
                if current_clean[0].isalpha() and current_clean[0].islower():
                    if any(c in current_clean.lower()[:3] for c in 'aeiou'):
                        return True
        if current_clean and current_clean[0] in ',.!?;:()[]{}"\'`':
            return True
        return False

    for t, s in zip(tokens, shap_values):
        if t is None:
            continue
        if t == "":
            flush()
            continue

        raw = t
        has_roberta_marker = raw.startswith("Ġ") or raw.startswith("▁")
        if has_roberta_marker:
            flush()
            clean = raw.replace("Ġ", "").replace("▁", "")
            prev_clean = ""
        else:
            clean = raw.strip()
            if prev_clean and should_split_word(prev_clean, clean):
                flush()
                prev_clean = ""

        if clean in {"[CLS]", "[SEP]", "<s>", "</s>"}:
            flush()
            continue

        starts_new_word = (not has_roberta_marker
                           and len(raw) > 0 and raw[0].isspace())
        is_punct = bool(_PUNCT_RE.match(clean)) and clean != ""
        is_hyphen = clean in ['-', '—', '–', '‑']

        if starts_new_word:
            flush()
            prev_clean = ""

        if is_punct and merge_punct_into_previous and out and not is_hyphen:
            prev_w, prev_s = out[-1]
            out[-1] = (prev_w + clean, float(prev_s + s))
            prev_clean = clean
            continue
        elif is_hyphen:
            if cur_word:
                flush()
            prev_clean = ""
            continue

        cur_word += clean
        cur_sum += float(s)
        prev_clean = clean

        if (not has_roberta_marker and len(raw) > 0 and raw[-1].isspace()):
            flush()
            prev_clean = ""

    flush()
    return out


# ---------------------------------------------------------------------------


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs" / "basil_shap"
MANIFEST_PATH = OUT_DIR / "manifest.csv"

SEED = 7
MAX_LENGTH = 256
KEY_COLS = ["triplet_uuid", "outlet_idx", "sentence_idx"]

STRATA_CAPS = {
    "magnitude_TP":   100,
    "magnitude_FP":   100,
    "magnitude_TN":   100,
    "magnitude_FN":   100,
    "bias_type_lex":  100,
    "bias_type_inf":  100,
    "bias_type_both": None,
    "fp_shared":      100,
    "fp_bd_only":     100,
    "fp_dr_only":     100,
    "fn_shared_lex":  100,
}


def pick(rng, idx_array, n):
    """Sample without replacement; if n is None or >= len, return shuffled all."""
    idx = np.asarray(idx_array, dtype=int)
    if n is None or n >= len(idx):
        copy = idx.copy()
        rng.shuffle(copy)
        return copy
    return rng.choice(idx, size=n, replace=False)


def cap_for(stratum, limit):
    default = STRATA_CAPS[stratum]
    if limit is None:
        return default
    if default is None:
        return limit
    return min(limit, default)


def build_manifest(df, seed, limit):
    """Construct the per-stratum sample assignments deterministically.

    Returns DataFrame[model, stratum, triplet_uuid, outlet_idx, sentence_idx].
    A sentence may appear under multiple (model, stratum) tuples; SHAP is
    computed once per (model, sentence_key) and the cache dedupes downstream.
    """
    rng = np.random.default_rng(seed)
    bd, dr = "biasdetector", "daroberta"
    rows = []

    def emit(model, stratum, positions):
        for i in positions:
            r = df.iloc[i]
            rows.append({
                "model": model,
                "stratum": stratum,
                "triplet_uuid": r.triplet_uuid,
                "outlet_idx": int(r.outlet_idx),
                "sentence_idx": int(r.sentence_idx),
            })

    bd_tp = np.where((df.biased == 1) & (df[f"pred_{bd}"] == 1))[0]
    bd_fp = np.where((df.biased == 0) & (df[f"pred_{bd}"] == 1))[0]
    bd_tn = np.where((df.biased == 0) & (df[f"pred_{bd}"] == 0))[0]
    dr_tp = np.where((df.biased == 1) & (df[f"pred_{dr}"] == 1))[0]
    dr_fp = np.where((df.biased == 0) & (df[f"pred_{dr}"] == 1))[0]
    dr_tn = np.where((df.biased == 0) & (df[f"pred_{dr}"] == 0))[0]

    emit(bd, "magnitude_TP", pick(rng, bd_tp, cap_for("magnitude_TP", limit)))
    emit(bd, "magnitude_FP", pick(rng, bd_fp, cap_for("magnitude_FP", limit)))
    emit(bd, "magnitude_TN", pick(rng, bd_tn, cap_for("magnitude_TN", limit)))
    emit(dr, "magnitude_TP", pick(rng, dr_tp, cap_for("magnitude_TP", limit)))
    emit(dr, "magnitude_FP", pick(rng, dr_fp, cap_for("magnitude_FP", limit)))
    emit(dr, "magnitude_TN", pick(rng, dr_tn, cap_for("magnitude_TN", limit)))

    bd_lex  = np.where((df.biased == 1) & (df[f"pred_{bd}"] == 1) & (df.has_lex == 1) & (df.has_inf == 0))[0]
    bd_inf  = np.where((df.biased == 1) & (df[f"pred_{bd}"] == 1) & (df.has_inf == 1) & (df.has_lex == 0))[0]
    bd_both = np.where((df.biased == 1) & (df[f"pred_{bd}"] == 1) & (df.has_both_types == 1))[0]
    dr_lex  = np.where((df.biased == 1) & (df[f"pred_{dr}"] == 1) & (df.has_lex == 1) & (df.has_inf == 0))[0]
    dr_inf  = np.where((df.biased == 1) & (df[f"pred_{dr}"] == 1) & (df.has_inf == 1) & (df.has_lex == 0))[0]
    dr_both = np.where((df.biased == 1) & (df[f"pred_{dr}"] == 1) & (df.has_both_types == 1))[0]

    emit(bd, "bias_type_lex",  pick(rng, bd_lex,  cap_for("bias_type_lex",  limit)))
    emit(bd, "bias_type_inf",  pick(rng, bd_inf,  cap_for("bias_type_inf",  limit)))
    emit(bd, "bias_type_both", pick(rng, bd_both, cap_for("bias_type_both", limit)))
    emit(dr, "bias_type_lex",  pick(rng, dr_lex,  cap_for("bias_type_lex",  limit)))
    emit(dr, "bias_type_inf",  pick(rng, dr_inf,  cap_for("bias_type_inf",  limit)))
    emit(dr, "bias_type_both", pick(rng, dr_both, cap_for("bias_type_both", limit)))

    shared_fp  = np.where((df.biased == 0) & (df[f"pred_{bd}"] == 1) & (df[f"pred_{dr}"] == 1))[0]
    bd_only_fp = np.where((df.biased == 0) & (df[f"pred_{bd}"] == 1) & (df[f"pred_{dr}"] == 0))[0]
    dr_only_fp = np.where((df.biased == 0) & (df[f"pred_{bd}"] == 0) & (df[f"pred_{dr}"] == 1))[0]

    shared_fp_sel = pick(rng, shared_fp, cap_for("fp_shared", limit))
    emit(bd, "fp_shared", shared_fp_sel)
    emit(dr, "fp_shared", shared_fp_sel)  # same sentences for both models

    emit(bd, "fp_bd_only", pick(rng, bd_only_fp, cap_for("fp_bd_only", limit)))
    emit(dr, "fp_dr_only", pick(rng, dr_only_fp, cap_for("fp_dr_only", limit)))

    shared_fn_lex = np.where(
        (df.biased == 1) & (df.has_lex == 1) & (df.has_inf == 0)
        & (df[f"pred_{bd}"] == 0) & (df[f"pred_{dr}"] == 0)
    )[0]
    shared_fn_sel = pick(rng, shared_fn_lex, cap_for("fn_shared_lex", limit))
    emit(bd, "fn_shared_lex", shared_fn_sel)
    emit(dr, "fn_shared_lex", shared_fn_sel)

    # magnitude_FN is appended AFTER all earlier strata so the shared RNG
    # state for those strata is preserved across runs — keeps the existing
    # SHAP cache valid when this stratum is added later.
    bd_fn = np.where((df.biased == 1) & (df[f"pred_{bd}"] == 0))[0]
    dr_fn = np.where((df.biased == 1) & (df[f"pred_{dr}"] == 0))[0]
    emit(bd, "magnitude_FN", pick(rng, bd_fn, cap_for("magnitude_FN", limit)))
    emit(dr, "magnitude_FN", pick(rng, dr_fn, cap_for("magnitude_FN", limit)))

    # Deberta magnitude strata appended last (same reason as above): adding
    # these doesn't touch the RNG state used for any of the bd/dr emits.
    if "pred_deberta" in df.columns:
        db = "deberta"
        db_tp = np.where((df.biased == 1) & (df[f"pred_{db}"] == 1))[0]
        db_fp = np.where((df.biased == 0) & (df[f"pred_{db}"] == 1))[0]
        db_tn = np.where((df.biased == 0) & (df[f"pred_{db}"] == 0))[0]
        db_fn = np.where((df.biased == 1) & (df[f"pred_{db}"] == 0))[0]
        emit(db, "magnitude_TP", pick(rng, db_tp, cap_for("magnitude_TP", limit)))
        emit(db, "magnitude_FP", pick(rng, db_fp, cap_for("magnitude_FP", limit)))
        emit(db, "magnitude_TN", pick(rng, db_tn, cap_for("magnitude_TN", limit)))
        emit(db, "magnitude_FN", pick(rng, db_fn, cap_for("magnitude_FN", limit)))

    return pd.DataFrame(rows)


def load_cache_keys(jsonl_path):
    if not jsonl_path.exists():
        return set()
    keys = set()
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                keys.add((rec["triplet_uuid"], int(rec["outlet_idx"]), int(rec["sentence_idx"])))
            except (json.JSONDecodeError, KeyError):
                continue
    return keys


def run_shap_for_model(suffix, hf_id, sentence_keys_df, df_indexed, device):
    """sentence_keys_df: DataFrame with KEY_COLS for this model (unique rows)."""
    jsonl_path = OUT_DIR / f"samples_{suffix}.jsonl"
    cached = load_cache_keys(jsonl_path)

    sentence_keys_df = sentence_keys_df.drop_duplicates(subset=KEY_COLS).reset_index(drop=True)
    pending = []
    for _, r in sentence_keys_df.iterrows():
        key = (r.triplet_uuid, int(r.outlet_idx), int(r.sentence_idx))
        if key not in cached:
            pending.append(key)

    if not pending:
        print(f"[{suffix}] All {len(sentence_keys_df)} sentences already cached. Skipping model load.")
        return

    print(f"[{suffix}] Loading {hf_id}")
    tokenizer = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(hf_id)
    model.eval()
    model.to(device)

    id2label = model.config.id2label if hasattr(model.config, "id2label") else {0: "NEG", 1: "POS"}
    positive_index = infer_positive_index(id2label)
    print(f"[{suffix}] id2label={id2label} → positive_index={positive_index}")

    predict_fn = build_predict_fn(model, tokenizer, device, MAX_LENGTH, positive_index)
    masker = shap.maskers.Text(tokenizer)
    explainer = shap.Explainer(predict_fn, masker)

    print(f"[{suffix}] Running SHAP on {len(pending)} sentences "
          f"({len(cached)} already cached)")
    start = time.time()
    wrote = 0
    skipped = 0

    with open(jsonl_path, "a", encoding="utf-8") as f:
        for i, key in enumerate(pending):
            try:
                row = df_indexed.loc[key]
            except KeyError:
                print(f"  [WARN] sentence {key} not in df, skipping")
                skipped += 1
                continue

            text = str(row.text)
            try:
                explanation = explainer([text])
            except Exception as e:
                print(f"  [WARN] SHAP failed on {key}: {e}")
                skipped += 1
                continue

            tokens = list(explanation.data[0])
            vals = explanation.values[0]
            if vals.ndim != 2:
                print(f"  [WARN] unexpected SHAP shape {vals.shape} on {key}, skipping")
                skipped += 1
                continue
            shap_pos = vals[:, positive_index]

            word_attribs = aggregate_subword_shap_to_words(tokens, shap_pos)

            prob_pos = float(row[f"prob_{suffix}"])
            gold = int(row.biased)
            pred = int(prob_pos >= 0.5)

            record = {
                "model": suffix,
                "triplet_uuid": row.triplet_uuid,
                "outlet_idx": int(row.outlet_idx),
                "sentence_idx": int(row.sentence_idx),
                "text": text,
                "gold": gold,
                "pred": pred,
                "prob_pos": prob_pos,
                "biased": int(row.biased),
                "has_lex": int(row.has_lex) if not pd.isna(row.has_lex) else 0,
                "has_inf": int(row.has_inf) if not pd.isna(row.has_inf) else 0,
                "has_both_types": int(row.has_both_types) if not pd.isna(row.has_both_types) else 0,
                "quote_status": "" if pd.isna(row.quote_status) else str(row.quote_status),
                "tokens": tokens,
                "shap_pos": [float(x) for x in shap_pos.tolist()],
                "word_attribs": [{"word": w, "shap": v} for (w, v) in word_attribs],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            wrote += 1

            done = i + 1
            elapsed = time.time() - start
            per = elapsed / done
            remaining = len(pending) - done
            if done == 1 or done % 10 == 0 or done == len(pending):
                eta_min = (per * remaining) / 60
                print(f"  [{suffix}] [{done:>4}/{len(pending)}] "
                      f"wrote={wrote} skipped={skipped}  "
                      f"{per:.1f}s/sent  elapsed {elapsed/60:.1f}m  ETA {eta_min:.1f}m")

    print(f"[{suffix}] done — wrote {wrote} new records, skipped {skipped}, "
          f"in {(time.time()-start)/60:.1f}m")

    del model
    if device.type == "cuda":
        torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap each stratum at N (smoke test). Default: no cap.")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--models", type=str, default="biasdetector,daroberta",
                    help="Comma-separated model suffixes to run.")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    selected = [m.strip() for m in args.models.split(",") if m.strip()]
    model_id_map = dict(MODELS)
    for s in selected:
        if s not in model_id_map:
            raise SystemExit(f"Unknown model suffix '{s}'. Known: {list(model_id_map)}")

    print("Loading BASIL joined frame ...")
    df = load_joined().reset_index(drop=True)
    print(f"  {len(df)} sentences total")

    print(f"Building manifest (seed={args.seed}, limit={args.limit}) ...")
    manifest = build_manifest(df, args.seed, args.limit)
    manifest.to_csv(MANIFEST_PATH, index=False)
    print(f"  Wrote {MANIFEST_PATH} ({len(manifest)} rows)")

    counts = (manifest
              .groupby(["model", "stratum"])
              .apply(lambda g: g[KEY_COLS].drop_duplicates().shape[0],
                     include_groups=False)
              .reset_index(name="n_sentences"))
    print("  Per-(model, stratum) unique sentence counts:")
    print(counts.to_string(index=False))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    df_indexed = df.set_index(KEY_COLS, drop=False)

    for suffix in selected:
        sub = manifest[manifest.model == suffix][KEY_COLS]
        run_shap_for_model(suffix, model_id_map[suffix], sub, df_indexed, device)

    print("[DONE]")


if __name__ == "__main__":
    main()
