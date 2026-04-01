"""
Train/evaluate sentiment model from CSV files.

Expected CSV format:
    text;product;label
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.sentiment_classifier import SentimentClassifier
from config.settings import get_settings


def load_semicolon_csv(path: Path):
    import pandas as pd  # type: ignore[reportMissingImports]

    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for parts in reader:
            if len(parts) < 3:
                continue
            text = parts[0].strip()
            product = parts[1].strip()
            label = parts[2].strip().lower()
            if not text or not label:
                continue
            rows.append({"text": text, "product": product, "sentiment": label})
    return pd.DataFrame(rows)


def main() -> None:
    import pandas as pd  # type: ignore[reportMissingImports]
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Train Ramy sentiment model.")
    parser.add_argument(
        "--train-file",
        default="data/augmented/Ramy_data_train_target_1500.csv",
        help="Path to train CSV file.",
    )
    parser.add_argument(
        "--val-file",
        default="data/augmented/Ramy_data_val_target_1500.csv",
        help="Path to validation CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        default=settings.model.output_dir,
        help="Directory to save model/checkpoints.",
    )
    parser.add_argument(
        "--metrics-output",
        default="data/processed/sentiment_eval_metrics.json",
        help="Path to save evaluation metrics json.",
    )
    args = parser.parse_args()

    train_path = Path(args.train_file)
    val_path = Path(args.val_file)

    if not train_path.exists():
        raise FileNotFoundError(f"Train file not found: {train_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation file not found: {val_path}")

    train_df = load_semicolon_csv(train_path)
    val_df = load_semicolon_csv(val_path)

    if train_df.empty:
        raise ValueError("Train dataset is empty after parsing.")
    if val_df.empty:
        raise ValueError("Validation dataset is empty after parsing.")

    classifier = SentimentClassifier()
    train_metrics = classifier.train(
        train_df=train_df,
        val_df=val_df,
        text_col="text",
        label_col="sentiment",
        output_dir=args.output_dir,
    )

    eval_metrics = classifier.evaluate(
        test_df=val_df,
        text_col="text",
        label_col="sentiment",
    )

    metrics_payload = {
        "train": train_metrics,
        "validation": eval_metrics,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
    }

    metrics_path = Path(args.metrics_output)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Train rows: {len(train_df)}")
    print(f"Validation rows: {len(val_df)}")
    print(f"Validation accuracy: {eval_metrics['accuracy']:.4f}")
    print(f"Validation F1-macro: {eval_metrics['f1_macro']:.4f}")
    print(f"Saved model artifacts to: {args.output_dir}")
    print(f"Saved metrics to: {metrics_path}")


if __name__ == "__main__":
    main()
