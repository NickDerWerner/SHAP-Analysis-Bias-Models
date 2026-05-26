#!/usr/bin/env python3
"""Compute AUPRC on the BABE test set for both bias-classifier checkpoints.

Re-runs inference (no cached probabilities exist; analysis.py only caches
the SHAP-sampled subset). Parallels the BASIL AUPRC analysis.

Usage:
  cd "SHAP Analysis Bias Models"
  .venv/bin/python scripts/babe_auprc.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from huggingface_hub import hf_hub_download
from sklearn.metrics import average_precision_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer


ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "outputs" / "babe_auprc.txt"

MODELS = [
    ("biasdetector", "bias-detector",       "himel7/bias-detector"),
    ("daroberta",    "DA-RoBERTa-BABE-FT",  "mediabiasgroup/DA-RoBERTa-BABE-FT"),
    ("deberta",      "DeBERTa-base BABE-FT",
                     str(ROOT / "models" / "deberta-base-babe-ft")),
]
MAX_LENGTH = 256
BATCH = 32


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


def run_inference(model, tokenizer, texts, device):
    out = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(texts), BATCH):
            chunk = texts[start:start + BATCH]
            enc = tokenizer(chunk, padding=True, truncation=True,
                            max_length=MAX_LENGTH, return_tensors="pt")
            enc = {k: v.to(device) for k, v in enc.items()}
            logits = model(**enc).logits.detach().cpu().numpy()
            out.append(softmax_np(logits))
    return np.vstack(out)


def main():
    print("Loading BABE test split ...")
    path = hf_hub_download(repo_id="mediabiasgroup/BABE",
                           filename="data/test-00000-of-00001.parquet",
                           repo_type="dataset")
    df = pd.read_parquet(path).reset_index(drop=True)
    texts = df["text"].astype(str).tolist()
    y_true = df["label"].astype(int).to_numpy()
    n = len(y_true)
    prevalence = float(y_true.mean())
    print(f"  n={n}, positives={int(y_true.sum())}, prevalence={prevalence:.4f}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    results = []
    for suffix, display, hf_id in MODELS:
        print(f"\n[{suffix}] loading {hf_id}")
        tokenizer = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(hf_id).to(device)
        id2label = model.config.id2label if hasattr(model.config, "id2label") else {0: "NEG", 1: "POS"}
        pos_idx = infer_positive_index(id2label)
        print(f"  id2label={id2label} → positive_index={pos_idx}")

        probs = run_inference(model, tokenizer, texts, device)
        p_pos = probs[:, pos_idx]
        auprc = float(average_precision_score(y_true, p_pos))
        lift = auprc - prevalence
        lift_x = auprc / prevalence if prevalence > 0 else float("nan")
        results.append((display, auprc, lift, lift_x))
        print(f"  AUPRC = {auprc:.4f}   lift = {lift:+.4f}   ratio = {lift_x:.3f}x baseline")
        del model

    lines = []
    lines.append("BABE test set — AUPRC")
    lines.append("=" * 60)
    lines.append(f"n = {n}")
    lines.append(f"positives = {int(y_true.sum())} ({prevalence*100:.2f}%)")
    lines.append(f"prevalence baseline (random classifier AUPRC) = {prevalence:.4f}")
    lines.append("")
    lines.append(f"{'model':<22} {'AUPRC':>8} {'lift':>10} {'ratio':>10}")
    lines.append("-" * 60)
    for display, auprc, lift, lift_x in results:
        lines.append(f"{display:<22} {auprc:>8.4f} {lift:>+10.4f} {lift_x:>9.3f}x")
    lines.append("")
    lines.append("lift  = AUPRC - prevalence")
    lines.append("ratio = AUPRC / prevalence (how many times better than random)")

    text = "\n".join(lines) + "\n"
    OUT_PATH.write_text(text)
    print()
    print(text, end="")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
