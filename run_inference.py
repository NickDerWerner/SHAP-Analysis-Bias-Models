"""Zero-shot inference of a HF bias classifier over the BASIL master CSV.

Writes a sidecar predictions CSV with columns:
  triplet_uuid, outlet_idx, sentence_idx, prob_biased, pred

Keyed on (triplet_uuid, outlet_idx, sentence_idx) — the only uniquely
identifying tuple in the master CSV. `article_uuid` is not unique: 3 hpo
articles share a uuid with another file in the corpus.

prob_biased is preserved at full precision so the metrics step can re-threshold
without re-running inference.

Usage:
  python run_inference.py --model himel7/bias-detector \
      --model_suffix biasdetector
  python run_inference.py --model mediabiasgroup/DA-RoBERTa-BABE-FT \
      --model_suffix daroberta
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "basil_sentences.csv"
OUT_DIR = ROOT / "outputs" / "basil"


def pick_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def biased_label_index(model):
    """Return the class index meaning 'biased'.

    Mirrors the heuristic in analysis.py: prefer the label containing 'bias'
    but not a negation marker. Falls back to class 1 (HF default positive).
    """
    id2label = {int(k): str(v) for k, v in model.config.id2label.items()}
    if len(id2label) != 2:
        sys.exit(f"Expected 2-class model, got id2label={id2label}")

    negations = ("no", "non", "not", "un", "neutral")
    candidates = [
        idx for idx, name in id2label.items()
        if "bias" in name.lower()
        and not any(neg in name.lower() for neg in negations)
    ]
    if len(candidates) == 1:
        return candidates[0]
    print(
        f"Warning: ambiguous id2label={id2label}; assuming class 1 is biased.",
        file=sys.stderr,
    )
    return 1


def load_sentences():
    rows = []
    with CSV_PATH.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(
                (
                    r["triplet_uuid"],
                    int(r["outlet_idx"]),
                    int(r["sentence_idx"]),
                    r["text"],
                )
            )
    return rows


def run_batch(texts, tokenizer, model, device, biased_idx, max_length):
    enc = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        logits = model(**enc).logits
    probs = torch.softmax(logits, dim=-1)[:, biased_idx]
    return probs.detach().cpu().tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--model_suffix",
        required=True,
        help="Used in the output filename; must not be empty.",
    )
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_length", type=int, default=256)
    args = parser.parse_args()

    if not args.model_suffix.strip():
        sys.exit("--model_suffix must be a non-empty identifier (e.g. 'biasdetector').")

    device = pick_device()
    print(f"Loading {args.model} onto {device}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    model.eval().to(device)
    biased_idx = biased_label_index(model)
    print(f"  id2label = {model.config.id2label}; biased index = {biased_idx}")

    sentences = load_sentences()
    print(
        f"Running on {len(sentences)} sentences, "
        f"batch {args.batch_size}, max_len {args.max_length}..."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"predictions_{args.model_suffix}.csv"
    start = time.time()
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["triplet_uuid", "outlet_idx", "sentence_idx", "prob_biased", "pred"]
        )
        for i in range(0, len(sentences), args.batch_size):
            chunk = sentences[i : i + args.batch_size]
            texts = [s[3] for s in chunk]
            probs = run_batch(texts, tokenizer, model, device, biased_idx, args.max_length)
            for (triplet, outlet, sid, _), p in zip(chunk, probs):
                writer.writerow([triplet, outlet, sid, f"{p:.6f}", int(p >= 0.5)])
            done = min(i + args.batch_size, len(sentences))
            if (i // args.batch_size) % 20 == 0 or done == len(sentences):
                elapsed = time.time() - start
                print(f"  {done}/{len(sentences)}  [{elapsed:.1f}s]")

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
