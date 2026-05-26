"""Run SHAP on a single BASIL sentence with both bias-detector and
DA-RoBERTa-BABE-FT, and save the two HTML heatmaps used in the Figure 1
redesign (shared false positive, "same mechanism, different calibration").

The sentence was selected from the 100 shared-FP set in
outputs/basil_shap/basil_shap_fp_shared_paired.csv based on:
  * Both models predict BIASED with prob >= 0.90 (gold = non-biased)
  * Top-3 SHAP tokens by |value| identical across the two models (Jaccard = 1.00)
  * bias-detector magnitude > DA-RoBERTa on the shared tokens
"""

import os

import numpy as np
import shap
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


SENTENCE = "And who, exactly, sucked as much as the other side?"

MODELS = [
    ("biasdetector", "himel7/bias-detector"),
    ("daroberta", "mediabiasgroup/DA-RoBERTa-BABE-FT"),
]

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "outputs", "examples",
)
MAX_LENGTH = 256


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


def run(suffix, hf_id, device):
    print(f"[{suffix}] loading {hf_id}")
    tokenizer = AutoTokenizer.from_pretrained(hf_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(hf_id)
    model.eval().to(device)

    id2label = getattr(model.config, "id2label", {0: "NEG", 1: "POS"})
    pos_idx = infer_positive_index(id2label)
    print(f"[{suffix}] id2label={id2label} positive_index={pos_idx}")

    predict_fn = build_predict_fn(model, tokenizer, device, MAX_LENGTH, pos_idx)
    probs = predict_fn([SENTENCE])[0]
    print(f"[{suffix}] prob(BIASED) = {probs[pos_idx]:.4f}  prob(NON) = {probs[1 - pos_idx]:.4f}")

    masker = shap.maskers.Text(tokenizer)
    explainer = shap.Explainer(predict_fn, masker)
    explanation = explainer([SENTENCE])

    # Build a fresh single-output Explanation. Slicing in shap 0.51 preserves
    # `output_names = "Output 1"`, which both adds an "f_Output 1" label and
    # disables the red/blue colormap in the force-plot rendering.
    exp_pos = shap.Explanation(
        values=np.asarray(explanation.values[0])[:, pos_idx],
        base_values=float(np.asarray(explanation.base_values[0])[pos_idx]),
        data=list(explanation.data[0]),
    )

    out_path = os.path.join(OUT_DIR, f"figure1_redesign_{suffix}.html")
    html = shap.plots.text(exp_pos, display=False)
    # SHAP 0.51 + numpy 2.x bug: rgb fill values get serialized as
    # `rgb(np.float64(255.0), np.float64(0.0), ...)` which is invalid CSS
    # and renders as black. Strip the np.float64() wrappers.
    import re as _re
    html = _re.sub(r"np\.float64\(([^)]*)\)", r"\1", html)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[{suffix}] wrote {out_path}")

    # quick console summary of top tokens for sanity
    tokens = list(explanation.data[0])
    vals = explanation.values[0][:, pos_idx]
    ranked = sorted(zip(tokens, vals), key=lambda x: abs(x[1]), reverse=True)[:8]
    print(f"[{suffix}] top tokens by |SHAP|:")
    for t, v in ranked:
        print(f"    {t!r:>20} : {v:+.4f}")
    print()

    del model


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}\n")
    for suffix, hf_id in MODELS:
        run(suffix, hf_id, device)


if __name__ == "__main__":
    main()
