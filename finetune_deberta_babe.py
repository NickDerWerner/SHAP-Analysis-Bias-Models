"""Fine-tune microsoft/deberta-v3-base on BABE for binary bias classification.

Outputs a HuggingFace-format checkpoint at ./models/deberta-v3-base-babe-ft/
that the rest of the SHAP pipeline can load via AutoModel.from_pretrained()
exactly like the other two models.

Usage (from the SHAP Analysis Bias Models/ directory):
    .venv/bin/python finetune_deberta_babe.py

Optional flags: --epochs --batch_size --lr --seed
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from huggingface_hub import hf_hub_download
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)

MODEL_ID = "microsoft/deberta-base"
ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "models" / "deberta-base-babe-ft"
TRAINER_DIR = ROOT / "models" / "_trainer_runs" / "deberta-base-babe"

BABE_REPO = "mediabiasgroup/BABE"
TRAIN_PARQUET = "data/train-00000-of-00001.parquet"
TEST_PARQUET = "data/test-00000-of-00001.parquet"

MAX_LEN = 256


def load_babe_split(filename: str) -> pd.DataFrame:
    path = hf_hub_download(repo_id=BABE_REPO, filename=filename, repo_type="dataset")
    return pd.read_parquet(path)


class BabeDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.encodings = tokenizer(
            list(texts),
            truncation=True,
            max_length=MAX_LEN,
            padding=False,
        )
        self.labels = [int(x) for x in labels]

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    if isinstance(logits, tuple):
        logits = logits[0]
    logits = np.nan_to_num(np.asarray(logits), nan=0.0, posinf=1e4, neginf=-1e4)
    probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
    preds = probs.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1,
        "f1_biased": f1_score(labels, preds, pos_label=1, zero_division=0),
        "precision_macro": precision,
        "recall_macro": recall,
        "auprc_biased": average_precision_score(labels, probs[:, 1]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight_decay", type=float, default=0.01)
    ap.add_argument("--warmup_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val_frac", type=float, default=0.1)
    args = ap.parse_args()

    set_seed(args.seed)
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    print(f"torch: {torch.__version__} | MPS available: {torch.backends.mps.is_available()}")

    print(f"Loading BABE train/test from {BABE_REPO} ...")
    train_df = load_babe_split(TRAIN_PARQUET)
    test_df = load_babe_split(TEST_PARQUET)
    print(f"  train: {len(train_df)} rows, label counts: {train_df['label'].value_counts().to_dict()}")
    print(f"  test : {len(test_df)} rows, label counts: {test_df['label'].value_counts().to_dict()}")

    tr_texts, va_texts, tr_labels, va_labels = train_test_split(
        train_df["text"].astype(str).tolist(),
        train_df["label"].astype(int).tolist(),
        test_size=args.val_frac,
        stratify=train_df["label"].astype(int).tolist(),
        random_state=args.seed,
    )
    print(f"  split: {len(tr_texts)} train / {len(va_texts)} val")

    print(f"Loading tokenizer + model: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        num_labels=2,
        id2label={0: "Non-biased", 1: "Biased"},
        label2id={"Non-biased": 0, "Biased": 1},
    )

    train_ds = BabeDataset(tr_texts, tr_labels, tokenizer)
    val_ds = BabeDataset(va_texts, va_labels, tokenizer)
    test_ds = BabeDataset(test_df["text"].astype(str).tolist(),
                         test_df["label"].astype(int).tolist(),
                         tokenizer)

    if TRAINER_DIR.exists():
        shutil.rmtree(TRAINER_DIR)
    TRAINER_DIR.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(TRAINER_DIR),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        max_grad_norm=1.0,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=1,
        logging_steps=50,
        seed=args.seed,
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    print("Starting training ...")
    trainer.train()

    print("\n=== Validation metrics (best checkpoint) ===")
    val_metrics = trainer.evaluate(eval_dataset=val_ds)
    for k, v in val_metrics.items():
        print(f"  {k}: {v}")

    print("\n=== Test metrics (BABE test split) ===")
    test_metrics = trainer.evaluate(eval_dataset=test_ds)
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"\nSaved final model to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
