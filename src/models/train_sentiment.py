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
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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


def load_unlabeled_csv(path: Path):
    import pandas as pd  # type: ignore[reportMissingImports]

    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for parts in reader:
            if len(parts) < 1:
                continue
            text = parts[0].strip()
            if not text:
                continue
            product = parts[1].strip() if len(parts) > 1 else ""
            rows.append({"text": text, "product": product})
    return pd.DataFrame(rows)


def resolve_train_val_paths(
    train_file: str,
    val_file: str,
    data_dir: Path,
) -> Tuple[Path, Path]:
    """Resolve train/val files from explicit paths or common files in data folder."""
    if train_file and val_file:
        return Path(train_file), Path(val_file)

    candidates = [
        (
            data_dir / "augmented" / "Ramy_data_train_target_1500.csv",
            data_dir / "augmented" / "Ramy_data_val_target_1500.csv",
        ),
        (
            data_dir / "augmented" / "Ramy_data_balanced_train.csv",
            data_dir / "augmented" / "Ramy_data_balanced_val.csv",
        ),
    ]

    for train_path, val_path in candidates:
        if train_path.exists() and val_path.exists():
            return train_path, val_path

    raise FileNotFoundError(
        "Could not resolve train/val files from data folder. "
        "Pass --train-file and --val-file explicitly."
    )


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Train Ramy sentiment model.")
    parser.add_argument(
        "--trainer",
        choices=["transformer", "competition"],
        default="transformer",
        help="Training backend: transformer fine-tuning or classical competition ensemble.",
    )
    parser.add_argument(
        "--train-file",
        default="",
        help="Path to train CSV file. If omitted, auto-resolved from data folder.",
    )
    parser.add_argument(
        "--val-file",
        default="",
        help="Path to validation CSV file. If omitted, auto-resolved from data folder.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(settings.data.data_dir),
        help="Root data directory used for auto file resolution.",
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
    parser.add_argument(
        "--unlabeled-file",
        default="",
        help="Optional unlabeled CSV used for pseudo-labeling (semicolon format).",
    )
    parser.add_argument(
        "--enable-pseudo-labeling",
        action="store_true",
        help="Enable pseudo-labeling from --unlabeled-file.",
    )
    parser.add_argument(
        "--pseudo-label-min-confidence",
        type=float,
        default=0.92,
        help="Minimum confidence for pseudo-labeled rows.",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Number of StratifiedGroupKFold splits.",
    )
    parser.add_argument(
        "--disable-tta",
        action="store_true",
        help="Disable test-time augmentation at inference/evaluation.",
    )
    parser.add_argument(
        "--model-name",
        default=settings.model.name,
        help="Transformer model name for fine-tuning mode.",
    )
    parser.add_argument(
        "--device",
        default="",
        help="Optional device override for transformer mode (e.g. cuda, cpu).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=settings.model.num_epochs,
        help="Number of epochs for transformer fine-tuning mode.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.model.batch_size,
        help="Batch size for transformer fine-tuning mode.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=settings.model.learning_rate,
        help="Learning rate for transformer fine-tuning mode.",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    train_path, val_path = resolve_train_val_paths(
        train_file=args.train_file,
        val_file=args.val_file,
        data_dir=data_dir,
    )

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

    if args.trainer == "competition":
        from src.models.competition_pipeline import (
            CompetitionConfig,
            CompetitionSentimentPipeline,
        )

        unlabeled_df = None
        if args.unlabeled_file:
            unlabeled_path = Path(args.unlabeled_file)
            if not unlabeled_path.exists():
                raise FileNotFoundError(f"Unlabeled file not found: {unlabeled_path}")
            unlabeled_df = load_unlabeled_csv(unlabeled_path)

        competition_cfg = CompetitionConfig(
            n_splits=max(2, int(args.cv_folds)),
            enable_pseudo_labeling=bool(args.enable_pseudo_labeling),
            pseudo_label_min_confidence=float(args.pseudo_label_min_confidence),
            enable_tta=not bool(args.disable_tta),
        )

        pipeline = CompetitionSentimentPipeline(
            labels=settings.model.sentiment_labels,
            config=competition_cfg,
        )

        train_metrics = pipeline.fit(
            train_df=train_df,
            text_col="text",
            label_col="sentiment",
            unlabeled_df=unlabeled_df,
        )
        pipeline.save(args.output_dir)
        eval_metrics = pipeline.evaluate(
            df=val_df,
            text_col="text",
            label_col="sentiment",
        )
    else:
        from src.models.sentiment_classifier import SentimentClassifier

        try:
            import torch
            cuda_ok = torch.cuda.is_available()
            gpu_name = torch.cuda.get_device_name(0) if cuda_ok else "N/A"
        except Exception:
            cuda_ok = False
            gpu_name = "N/A"

        if not cuda_ok and (not args.device or args.device == "cuda"):
            print("Warning: CUDA is not available. Training will run on CPU.")

        settings.model.num_epochs = int(args.epochs)
        settings.model.batch_size = int(args.batch_size)
        settings.model.learning_rate = float(args.learning_rate)

        classifier = SentimentClassifier(
            model_name=args.model_name,
            device=args.device or None,
        )

        print(f"Transformer fine-tuning device: {classifier.device}")
        if gpu_name != "N/A":
            print(f"Detected GPU: {gpu_name}")

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
    print(f"Train file: {train_path}")
    print(f"Validation file: {val_path}")
    print(f"Trainer: {args.trainer}")
    print(f"Validation accuracy: {eval_metrics['accuracy']:.4f}")
    print(f"Validation F1-macro: {eval_metrics['f1_macro']:.4f}")
    if args.trainer == "competition" and "cv_f1_macro" in train_metrics:
        print(f"CV F1-macro (OOF): {train_metrics['cv_f1_macro']:.4f}")
    print(f"Saved model artifacts to: {args.output_dir}")
    print(f"Saved metrics to: {metrics_path}")


if __name__ == "__main__":
    main()
