#!/usr/bin/env python3
"""
SHAP analysis for himel7/bias-detector on BABE (sentence-level).

Outputs:
- outputs/shap_samples.jsonl                 (per-sentence token attributions)
- outputs/global_word_importance.csv         (global mean|SHAP| per word)
- outputs/examples/shap_*.html               (a few SHAP HTML visualizations)

Usage:
  python shap_bias_study.py \
    --model himel7/bias-detector \
    --dataset mediabiasgroup/BABE \
    --split test \
    --n_tp 100 --n_fp 100 --n_tn 100 \
    --max_shap_examples 30 \
    --output_dir outputs
"""

import argparse
import json
import os
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from datasets import load_dataset
from sklearn.metrics import confusion_matrix
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import shap


# ----------------------------
# Utilities
# ----------------------------

def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def pick_text_column(columns: List[str]) -> str:
    """
    Heuristic selection of the text/sentence column.
    """
    preferred = ["sentence", "text", "content", "sent", "claim"]
    lower = {c.lower(): c for c in columns}
    for p in preferred:
        if p in lower:
            return lower[p]
    # fallback: first string-like column name guess
    for c in columns:
        if any(k in c.lower() for k in ["sent", "text", "content"]):
            return c
    raise ValueError(f"Could not infer text column from: {columns}")


def pick_label_column(columns: List[str]) -> str:
    """
    Heuristic selection of the label column.
    """
    preferred = ["label", "labels", "bias", "is_biased", "sentence_label"]
    lower = {c.lower(): c for c in columns}
    for p in preferred:
        if p in lower:
            return lower[p]
    # fallback: anything that looks like a label
    for c in columns:
        if any(k in c.lower() for k in ["label", "bias"]):
            return c
    raise ValueError(f"Could not infer label column from: {columns}")


def infer_positive_index(id2label: Dict[int, str]) -> int:
    """
    Try to infer which class index corresponds to the "biased" class.
    We search for labels containing 'bias' but not 'no'/'non'.
    Fallback: assume class 1 is positive.
    """
    candidates = []
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "bias" in s and not any(x in s for x in ["no", "non", "unbias", "neutral"]):
            candidates.append(i)
    if len(candidates) == 1:
        return int(candidates[0])
    # If two labels are like "BIASED"/"NOT_BIASED", prefer the one with 'biased'
    for i, lab in id2label.items():
        s = str(lab).lower()
        if "biased" in s and not any(x in s for x in ["not", "no", "non"]):
            return int(i)
    return 1


def softmax_np(logits: np.ndarray) -> np.ndarray:
    x = logits - np.max(logits, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)


def normalize_label_values(y: Any) -> np.ndarray:
    """
    Convert labels to {0,1} if possible.
    Handles strings like 'biased', 'no_bias', booleans, and ints.
    """
    if isinstance(y, (list, np.ndarray, pd.Series)):
        y_list = list(y)
    else:
        y_list = [y]

    out = []
    for v in y_list:
        if isinstance(v, (np.integer, int)):
            out.append(int(v))
        elif isinstance(v, (np.floating, float)):
            out.append(int(v))
        elif isinstance(v, (bool, np.bool_)):
            out.append(int(v))
        else:
            s = str(v).strip().lower()
            if s in ["1", "true", "biased", "bias", "yes"]:
                out.append(1)
            elif s in ["0", "false", "not_biased", "no_bias", "unbiased", "neutral", "no"]:
                out.append(0)
            else:
                # last resort: try int conversion
                try:
                    out.append(int(s))
                except Exception as e:
                    raise ValueError(f"Unrecognized label value: {v}") from e

    return np.array(out, dtype=int)


def detokenize_to_words(tokens: List[str]) -> List[str]:
    """
    Simple word reconstruction for RoBERTa/GPT2-style BPE tokens:
    - RoBERTa uses 'Ġ' to mark whitespace before a token.
    - Some tokenizers use '▁' (SentencePiece).
    - We join subword pieces into words based on these markers.
    """
    words = []
    current = ""

    def flush():
        nonlocal current
        if current:
            words.append(current)
            current = ""

    for t in tokens:
        if t in ["[CLS]", "[SEP]"]:
            continue
        # common whitespace markers
        is_new_word = t.startswith("Ġ") or t.startswith("▁")
        clean = t
        clean = clean.replace("Ġ", "")
        clean = clean.replace("▁", "")

        # skip special masking tokens in aggregation
        if clean in ["<s>", "</s>"]:
            continue

        if is_new_word:
            flush()
            current = clean
        else:
            # continuation piece
            if current == "":
                current = clean
            else:
                current += clean

    flush()

    # remove empty or pure punctuation "words" optionally (keep for analysis if you prefer)
    words = [w for w in words if w.strip() != ""]
    return words


def normalize_word_for_aggregation(word: str) -> List[str]:
    """
    Normalize a word by splitting merged tokens and stripping punctuation artifacts.
    
    Handles cases like:
    - "tuesdayquoting" -> ["tuesday", "quoting"]
    - "nationalismfueled" -> ["nationalism", "fueled"]
    - "McConnell(-.)" -> ["mcconnell"]
    - "said''" -> ["said"]
    - "arrested." -> ["arrested"]
    - "not\"\"\"\"" -> ["not"]
    
    Returns a list of normalized words (may be multiple if merged words are split).
    """
    if not word or word.strip() == "":
        return []
    
    # Strip leading/trailing whitespace
    word = word.strip()
    
    # Remove trailing/leading punctuation artifacts
    # Strip common punctuation: quotes, periods, commas, hyphens, parentheses
    word = re.sub(r'^["\'`''""\.\,\!\?\;\:\(\)\[\]\{\}\-\_]+', '', word)
    word = re.sub(r'["\'`''""\.\,\!\?\;\:\(\)\[\]\{\}\-\_]+$', '', word)
    
    # Remove repeated punctuation characters (e.g., """", ''''', ---)
    word = re.sub(r'["\'`'']+', '', word)  # Remove all quotes
    word = re.sub(r'[\-\.\,\!\?]+$', '', word)  # Remove trailing punctuation clusters
    word = re.sub(r'^[\-\.\,\!\?]+', '', word)  # Remove leading punctuation clusters
    
    if word == "":
        return []
    
    # Try to split merged words
    # Pattern 1: lowercase followed by uppercase (e.g., "tuesdayQuoting" -> ["tuesday", "Quoting"])
    parts = re.split(r'(?<=[a-z])(?=[A-Z])', word)
    
    # Pattern 2: word boundary detection - common word endings followed by lowercase start
    # This handles cases like "tuesdayquoting" where both parts are lowercase
    if len(parts) == 1 and len(word) > 6:  # Only try if single part and reasonably long
        # Common word endings that might indicate a boundary
        common_endings = ['day', 'ing', 'ed', 'ly', 'er', 'tion', 'ment', 'ism', 'ist', 'ous', 'ful', 'al']
        for ending in common_endings:
            if word.lower().endswith(ending) and len(word) > len(ending) + 3:
                # Try splitting after the ending
                prefix = word[:-len(ending)]
                suffix = word[-len(ending):]
                if len(prefix) >= 3:  # Reasonable prefix length
                    # Check if prefix looks like a word (has vowels)
                    if any(c in prefix.lower() for c in 'aeiou'):
                        parts = [prefix, suffix]
                        break
    
    # Normalize each part
    normalized_parts = []
    for part in parts:
        part = part.lower()
        # Remove any remaining punctuation
        part = re.sub(r'[^\w]', '', part)
        if part and len(part) > 0:
            normalized_parts.append(part)
    
    return normalized_parts if normalized_parts else []


def aggregate_subword_shap_to_words(tokens: List[str], shap_values: np.ndarray) -> List[Tuple[str, float]]:
    """
    Aggregate subword SHAP values to word-level SHAP by summation.
    Intelligently detects word boundaries to prevent merging separate words.

    tokens: list of token strings (as provided by SHAP masker/tokenizer)
    shap_values: array of per-token SHAP attributions (same length as tokens)
    """
    import re
    _PUNCT_RE = re.compile(r"^\W+$", re.UNICODE)
    
    # Build (word, summed_shap) by reconstructing word boundaries from markers.
    word_attribs: List[Tuple[str, float]] = []
    current_word = ""
    current_sum = 0.0
    prev_clean = ""

    def flush():
        nonlocal current_word, current_sum, prev_clean
        if current_word:
            word_attribs.append((current_word, float(current_sum)))
            current_word = ""
            current_sum = 0.0
            prev_clean = ""

    def should_split_word(prev_clean: str, current_clean: str) -> bool:
        """Detect if we should split between prev_clean and current_clean."""
        if not prev_clean or not current_clean:
            return False
        
        # Check for case change: lowercase->uppercase indicates new word
        if prev_clean and current_clean:
            if prev_clean[-1].islower() and current_clean[0].isupper():
                return True
        
        # Check for common word endings followed by what looks like a new word
        common_endings = ['day', 'ing', 'ed', 'ly', 'er', 'tion', 'ment', 'ism', 'ist', 'ous', 'ful', 'ness']
        prev_lower = prev_clean.lower()
        for ending in common_endings:
            if prev_lower.endswith(ending) and len(prev_clean) >= len(ending) + 2:
                if current_clean[0].isalpha() and current_clean[0].islower():
                    if any(c in current_clean.lower()[:3] for c in 'aeiou'):
                        return True
        
        # Punctuation at start indicates separation
        if current_clean and current_clean[0] in ',.!?;:()[]{}"\'`':
            return True
            
        return False

    for t, s in zip(tokens, shap_values):
        if t in ["[CLS]", "[SEP]"]:
            continue
        clean = t.replace("Ġ", "").replace("▁", "")
        if clean in ["<s>", "</s>"]:
            continue

        is_new_word = t.startswith("Ġ") or t.startswith("▁")
        if is_new_word:
            flush()
            current_word = clean
            current_sum = float(s)
            prev_clean = clean
        else:
            # Check if we should split based on word boundary detection
            if prev_clean and should_split_word(prev_clean, clean):
                flush()
                current_word = clean
                current_sum = float(s)
                prev_clean = clean
            else:
                # Handle hyphens as word separators
                is_hyphen = clean in ['-', '—', '–', '‑']
                if is_hyphen and current_word:
                    flush()
                    prev_clean = ""
                    continue
                
                # Handle punctuation
                is_punct = bool(_PUNCT_RE.match(clean)) and clean != ""
                if is_punct and not is_hyphen and word_attribs:
                    # Attach punctuation to previous word
                    prev_w, prev_s = word_attribs[-1]
                    word_attribs[-1] = (prev_w + clean, float(prev_s + s))
                    prev_clean = clean
                    continue
                
                if current_word == "":
                    current_word = clean
                    current_sum = float(s)
                else:
                    current_word += clean
                    current_sum += float(s)
                prev_clean = clean

    flush()
    return word_attribs


# ----------------------------
# Core pipeline
# ----------------------------

@dataclass
class SampledItem:
    text: str
    gold: int
    pred: int
    prob_pos: float


def build_predict_fn(model, tokenizer, device: torch.device, max_length: int, positive_index: int):
    """
    Returns a function f(texts: List[str]) -> np.ndarray of shape (n, 2)
    containing probabilities for each class, suitable for SHAP multi-output explanation.
    """

    def predict(texts: List[str]) -> np.ndarray:
        if hasattr(texts, "tolist"):
            texts = texts.tolist()
        elif isinstance(texts, str):
            texts = [texts]
        texts = [str(t) for t in texts]
        enc = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits.detach().cpu().numpy()
        probs = softmax_np(logits)
        return probs

    return predict


def run_inference(model, tokenizer, texts: List[str], device: torch.device, max_length: int) -> np.ndarray:
    enc = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        logits = model(**enc).logits.detach().cpu().numpy()
    probs = softmax_np(logits)
    return probs


def stratified_sample(texts: List[str], y_true: np.ndarray, y_pred: np.ndarray, p_pos: np.ndarray,
                      n_tp: int, n_fp: int, n_tn: int, seed: int) -> List[SampledItem]:
    """
    Sample TP / FP / TN instances for SHAP.
    """
    rng = np.random.default_rng(seed)
    tp_idx = np.where((y_true == 1) & (y_pred == 1))[0]
    fp_idx = np.where((y_true == 0) & (y_pred == 1))[0]
    tn_idx = np.where((y_true == 0) & (y_pred == 0))[0]

    def pick(idx: np.ndarray, n: int) -> np.ndarray:
        if len(idx) == 0:
            return np.array([], dtype=int)
        n_eff = min(n, len(idx))
        return rng.choice(idx, size=n_eff, replace=False)

    chosen = np.concatenate([pick(tp_idx, n_tp), pick(fp_idx, n_fp), pick(tn_idx, n_tn)])
    rng.shuffle(chosen)

    items: List[SampledItem] = []
    for i in chosen:
        items.append(SampledItem(
            text=texts[i],
            gold=int(y_true[i]),
            pred=int(y_pred[i]),
            prob_pos=float(p_pos[i]),
        ))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str, default="himel7/bias-detector")
    ap.add_argument("--model_suffix", type=str, default="", 
                    help="Suffix to add to output filenames (e.g., 'daroberta' for DA-RoBERTa model)")
    ap.add_argument("--dataset", type=str, default="mediabiasgroup/BABE")
    ap.add_argument("--split", type=str, default="test")
    ap.add_argument("--text_col", type=str, default="")
    ap.add_argument("--label_col", type=str, default="")
    ap.add_argument("--max_length", type=int, default=256)

    ap.add_argument("--n_tp", type=int, default=100)
    ap.add_argument("--n_fp", type=int, default=100)
    ap.add_argument("--n_tn", type=int, default=100)

    ap.add_argument("--max_shap_examples", type=int, default=30, help="Max number of sentences to run SHAP on (cost control).")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--batch_infer", type=int, default=64)

    ap.add_argument("--output_dir", type=str, default="outputs")
    args = ap.parse_args()

    set_seed(args.seed)
    ensure_dir(args.output_dir)
    ensure_dir(os.path.join(args.output_dir, "examples"))
    
    # Add suffix to output filenames if specified
    output_suffix = f"_{args.model_suffix}" if args.model_suffix else ""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- Load model + tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    model.eval()
    model.to(device)

    id2label = model.config.id2label if hasattr(model.config, "id2label") else {0: "NEG", 1: "POS"}
    positive_index = infer_positive_index(id2label)
    print(f"[INFO] id2label={id2label} | positive_index={positive_index} ({id2label.get(positive_index)})")

    # ---- Load dataset split
    ds = load_dataset(args.dataset, split=args.split)
    cols = ds.column_names
    text_col = args.text_col.strip() or pick_text_column(cols)
    label_col = args.label_col.strip() or pick_label_column(cols)
    print(f"[INFO] Using text_col='{text_col}' label_col='{label_col}' from columns={cols}")

    texts = [str(x) for x in list(ds[text_col])]
    y_true = normalize_label_values(list(ds[label_col]))

    # ---- Batch inference
    probs_all = []
    for start in range(0, len(texts), args.batch_infer):
        batch = texts[start:start + args.batch_infer]
        probs = run_inference(model, tokenizer, batch, device, args.max_length)
        probs_all.append(probs)
    probs_all = np.vstack(probs_all)

    p_pos = probs_all[:, positive_index]
    y_pred = (p_pos >= 0.5).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    print(f"[INFO] Confusion matrix @0.5: TP={tp} FP={fp} TN={tn} FN={fn}")

    # ---- Sample instances for SHAP
    sampled = stratified_sample(
        texts=texts,
        y_true=y_true,
        y_pred=y_pred,
        p_pos=p_pos,
        n_tp=args.n_tp,
        n_fp=args.n_fp,
        n_tn=args.n_tn,
        seed=args.seed
    )
    if len(sampled) == 0:
        raise RuntimeError("No samples selected. Check label normalization and thresholding.")
    print(f"[INFO] Selected {len(sampled)} samples (requested TP/FP/TN = {args.n_tp}/{args.n_fp}/{args.n_tn}).")

    # Cost control: SHAP is expensive
    sampled = sampled[: min(len(sampled), args.max_shap_examples)]
    print(f"[INFO] Running SHAP on {len(sampled)} samples (max_shap_examples={args.max_shap_examples}).")

    # ---- SHAP explainer
    # Use a transformer-friendly text masker: replaces tokens with mask token.
    masker = shap.maskers.Text(tokenizer)

    predict_fn = build_predict_fn(
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_length=args.max_length,
        positive_index=positive_index
    )

    # Create explainer (uses a partition-based method for text with this masker)
    explainer = shap.Explainer(predict_fn, masker)

    # ---- Run SHAP
    sample_texts = [s.text for s in sampled]
    # returns shap.Explanation with values shape: (n_samples, n_tokens, n_outputs)
    explanation = explainer(sample_texts)

    # ---- Export per-sentence attributions + compute global word importance
    jsonl_path = os.path.join(args.output_dir, f"shap_samples{output_suffix}.jsonl")
    global_rows = []

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(sampled):
            # tokens for this sample
            tokens = list(explanation.data[i])
            # shap values for the positive class
            # explanation.values shape can be (n, tokens, outputs)
            vals = explanation.values[i]
            if vals.ndim == 2:
                # (tokens, outputs)
                shap_pos = vals[:, positive_index]
            else:
                raise RuntimeError(f"Unexpected SHAP values shape per-sample: {vals.shape}")

            # word aggregation
            word_attribs = aggregate_subword_shap_to_words(tokens, shap_pos)

            record = {
                "text": s.text,
                "gold": s.gold,
                "pred": s.pred,
                "prob_pos": s.prob_pos,
                "tokens": tokens,
                "shap_pos": [float(x) for x in shap_pos.tolist()],
                "word_attribs": [{"word": w, "shap": v} for (w, v) in word_attribs],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

            for (w, v) in word_attribs:
                # Normalize the "word" a bit for global stats
                w_norm = re.sub(r"\s+", "", w.strip().lower())
                if w_norm == "":
                    continue
                global_rows.append({"word": w_norm, "abs_shap": abs(float(v)), "shap": float(v)})

    print(f"[INFO] Wrote per-sentence SHAP to: {jsonl_path}")

    # ---- Global importance
    gdf = pd.DataFrame(global_rows)
    if len(gdf) == 0:
        raise RuntimeError("No global rows collected; check tokenizer markers and SHAP output.")

    global_imp = (
        gdf.groupby("word")
        .agg(mean_abs_shap=("abs_shap", "mean"),
             mean_shap=("shap", "mean"),
             count=("word", "size"))
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index()
    )
    csv_path = os.path.join(args.output_dir, f"global_word_importance{output_suffix}.csv")
    global_imp.to_csv(csv_path, index=False)
    print(f"[INFO] Wrote global word importance to: {csv_path}")

    # ---- Save a few HTML visualizations
    # Note: SHAP text plots in notebooks are interactive; HTML saving is easiest via shap.plots.text and shap.save_html
    for i in range(min(5, len(sampled))):
        html_path = os.path.join(args.output_dir, "examples", f"shap{output_suffix}_{i}.html")
        # Focus the visualization on the positive class
        exp_i = explanation[i, :, positive_index]
        shap.save_html(html_path, shap.plots.text(exp_i, display=False))
        print(f"[INFO] Wrote example HTML: {html_path}")

    print("[DONE]")


if __name__ == "__main__":
    main()
