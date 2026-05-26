#!/usr/bin/env python3
"""BABE FN SHAP generator — appends 100 FN per model to the existing caches.

The original BABE pipeline (analysis.py) sampled only TP/FP/TN, so the
existing caches outputs/shap_samples.jsonl (bias-detector) and
outputs/shap_samples_daroberta.jsonl (DA-RoBERTa) have zero FN records.
This script fills that gap so the Fig 3 counterpart with all four
prediction categories can be plotted for BABE.

Loads BABE test split directly from the HuggingFace hub parquet (the venv
doesn't have `datasets` installed). Runs inference on all 1000 BABE-test
sentences, samples FNs deterministically (seed=7), runs SHAP with the same
pipeline as analysis.py / basil_shap_generate.py, appends to the existing
JSONL. Resumable — re-running skips records already in the cache (by text).

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python babe_shap_fn.py [--n_fn 100] [--seed 7]

Outputs (appended to existing files):
  outputs/shap_samples.jsonl
  outputs/shap_samples_daroberta.jsonl
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
from huggingface_hub import hf_hub_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer


# ---------------------------------------------------------------------------
# SHAP pipeline — copied verbatim from basil_shap_generate.py so this script
# is self-contained and matches the BASIL pipeline exactly. Do not modify.
# ---------------------------------------------------------------------------

def softmax_np(logits):
    x = logits - np.max(logits, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)


def infer_positive_index(id2label):
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "biased" in s and not any(x in s for x in ["not", "no", "non"]):
            return int(i)
    return 1


def build_predict_fn(model, tokenizer, device, max_length, positive_index):
    def predict(texts):
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
OUT_DIR = ROOT / "outputs"

MODELS = [
    ("biasdetector", "himel7/bias-detector", OUT_DIR / "shap_samples.jsonl"),
    ("daroberta",    "mediabiasgroup/DA-RoBERTa-BABE-FT",
     OUT_DIR / "shap_samples_daroberta.jsonl"),
    ("deberta",      str(ROOT / "models" / "deberta-base-babe-ft"),
     OUT_DIR / "shap_samples_deberta.jsonl"),
]

MAX_LENGTH = 256
BABE_PARQUET = "data/test-00000-of-00001.parquet"


def load_babe_test():
    path = hf_hub_download(repo_id="mediabiasgroup/BABE",
                           filename=BABE_PARQUET, repo_type="dataset")
    df = pd.read_parquet(path)
    print(f"  BABE test: {len(df)} sentences, columns={list(df.columns)}")
    return df.reset_index(drop=True)


def existing_texts(jsonl_path):
    """Set of texts already SHAP'd, so re-runs don't double-write."""
    seen = set()
    if not jsonl_path.exists():
        return seen
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["text"])
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


def run_inference(model, tokenizer, texts, device, max_length, batch=32):
    """Full softmax probability for each of the inputs."""
    out = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(texts), batch):
            chunk = texts[start:start + batch]
            enc = tokenizer(chunk, padding=True, truncation=True,
                            max_length=max_length, return_tensors="pt")
            enc = {k: v.to(device) for k, v in enc.items()}
            logits = model(**enc).logits.detach().cpu().numpy()
            out.append(softmax_np(logits))
    return np.vstack(out)


def run_for_model(suffix, hf_id, jsonl_path, df, n_fn, seed, device):
    print(f"\n=== {suffix} ({hf_id}) ===")
    print(f"  Loading model")
    tokenizer = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(hf_id)
    model.to(device)

    id2label = model.config.id2label if hasattr(model.config, "id2label") else {0: "NEG", 1: "POS"}
    positive_index = infer_positive_index(id2label)
    print(f"  id2label={id2label} → positive_index={positive_index}")

    texts = df["text"].astype(str).tolist()
    labels = df["label"].astype(int).to_numpy()

    print(f"  Inference on {len(texts)} sentences")
    probs = run_inference(model, tokenizer, texts, device, MAX_LENGTH)
    p_pos = probs[:, positive_index]
    y_pred = (p_pos >= 0.5).astype(int)

    tp = int(((labels == 1) & (y_pred == 1)).sum())
    fp = int(((labels == 0) & (y_pred == 1)).sum())
    tn = int(((labels == 0) & (y_pred == 0)).sum())
    fn = int(((labels == 1) & (y_pred == 0)).sum())
    print(f"  Confusion @0.5: TP={tp} FP={fp} TN={tn} FN={fn}")

    fn_idx = np.where((labels == 1) & (y_pred == 0))[0]
    rng = np.random.default_rng(seed)
    n_pick = min(n_fn, len(fn_idx))
    picked = rng.choice(fn_idx, size=n_pick, replace=False)
    print(f"  Picked {n_pick} FN sentences for SHAP")

    seen = existing_texts(jsonl_path)
    pending = [i for i in picked if texts[i] not in seen]
    print(f"  {len(pending)} new, {n_pick - len(pending)} already cached by text")

    if not pending:
        print(f"  Nothing to do for {suffix}")
        del model
        return

    predict_fn = build_predict_fn(model, tokenizer, device, MAX_LENGTH, positive_index)
    masker = shap.maskers.Text(tokenizer)
    explainer = shap.Explainer(predict_fn, masker)

    start = time.time()
    wrote = 0
    skipped = 0
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for i_pos, idx in enumerate(pending):
            text = texts[idx]
            try:
                exp = explainer([text])
            except Exception as e:
                print(f"    [WARN] SHAP failed on idx={idx}: {e}")
                skipped += 1
                continue

            tokens = list(exp.data[0])
            vals = exp.values[0]
            if vals.ndim != 2:
                print(f"    [WARN] unexpected shape {vals.shape} on idx={idx}")
                skipped += 1
                continue
            shap_pos = vals[:, positive_index]
            word_attribs = aggregate_subword_shap_to_words(tokens, shap_pos)

            record = {
                "text": text,
                "gold": int(labels[idx]),
                "pred": int(y_pred[idx]),
                "prob_pos": float(p_pos[idx]),
                "tokens": tokens,
                "shap_pos": [float(x) for x in shap_pos.tolist()],
                "word_attribs": [{"word": w, "shap": v} for (w, v) in word_attribs],
                "uuid": str(df.iloc[idx]["uuid"]) if "uuid" in df.columns else "",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            wrote += 1

            done = i_pos + 1
            elapsed = time.time() - start
            per = elapsed / done
            remaining = len(pending) - done
            if done == 1 or done % 10 == 0 or done == len(pending):
                eta_min = (per * remaining) / 60
                print(f"    [{done:>3}/{len(pending)}] "
                      f"wrote={wrote} skipped={skipped}  "
                      f"{per:.1f}s/sent  elapsed {elapsed/60:.1f}m  ETA {eta_min:.1f}m")

    print(f"  Done — wrote {wrote}, skipped {skipped}, "
          f"{(time.time()-start)/60:.1f}m total")

    del model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_fn", type=int, default=100)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--models", type=str, default="biasdetector,daroberta,deberta")
    args = ap.parse_args()

    print("Loading BABE test split ...")
    df = load_babe_test()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    selected = {m.strip() for m in args.models.split(",") if m.strip()}
    for suffix, hf_id, path in MODELS:
        if suffix in selected:
            run_for_model(suffix, hf_id, path, df, args.n_fn, args.seed, device)

    print("\n[DONE]")


if __name__ == "__main__":
    main()
