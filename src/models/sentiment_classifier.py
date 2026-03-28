"""
AraBERT-Based Sentiment Classifier
====================================
Fine-tuned transformer model for Arabic/Darja sentiment analysis.

Architecture:
    AraBERT (aubmindlab/bert-base-arabertv02) → Linear → Softmax
    3-class: Positive | Negative | Neutral

This module provides both training and inference capabilities.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from config.settings import get_settings
from src.data_pipeline.preprocessor import ArabicPreprocessor


# ── Constants ─────────────────────────────────────────────

LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}
LABEL_MAP_INV = {v: k for k, v in LABEL_MAP.items()}
LABEL_COLORS = {
    "positive": "#2D8B4E",
    "negative": "#E31E24",
    "neutral": "#F7B731",
}


class ReviewDataset:
    """PyTorch Dataset for tokenized reviews."""

    def __init__(self, texts, labels, tokenizer, max_length=256):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }


class SentimentClassifier:
    """
    Arabic Sentiment Classifier powered by AraBERT.

    Usage:
        classifier = SentimentClassifier()
        result = classifier.predict("عصير رامي بنين بزاف")
        # {'sentiment': 'positive', 'confidence': 0.94, 'scores': {...}}
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.settings = get_settings()
        self.model_name = model_name or self.settings.model.name
        self.preprocessor = ArabicPreprocessor()
        self.model = None
        self.tokenizer = None

        if TORCH_AVAILABLE:
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"

    def load_model(self):
        """Load pre-trained AraBERT model for sentiment classification."""
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch and Transformers are required. "
                "Install with: pip install torch transformers"
            )

        print(f"📥 Loading model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3,
        )
        self.model.to(self.device)
        self.model.eval()
        print(f"✅ Model loaded on {self.device}")

    def predict(self, text: str) -> Dict:
        """
        Predict sentiment for a single text.

        Args:
            text: Arabic/Darja review text.

        Returns:
            Dict with keys: sentiment, confidence, scores, preprocessed_text
        """
        if self.model is None:
            # Fallback to rule-based when model not loaded
            return self._rule_based_predict(text)

        # Preprocess
        processed = self.preprocessor.preprocess(text)
        clean_text = processed["text"]

        # Tokenize
        encoding = self.tokenizer(
            clean_text,
            max_length=self.settings.model.max_seq_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        # Inference
        with torch.no_grad():
            input_ids = encoding["input_ids"].to(self.device)
            attention_mask = encoding["attention_mask"].to(self.device)
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

        # Build result
        pred_idx = int(np.argmax(probs))
        sentiment = LABEL_MAP[pred_idx]

        # Incorporate emoji signal
        emoji_boost = processed["emoji_sentiment"] * 0.1
        scores = {
            "negative": float(probs[0]),
            "neutral": float(probs[1]),
            "positive": float(probs[2]),
        }

        return {
            "sentiment": sentiment,
            "confidence": float(probs[pred_idx]),
            "scores": scores,
            "preprocessed_text": clean_text,
            "has_darja": processed["has_darja"],
            "has_french": processed["has_french"],
            "emojis": processed["emojis"],
            "emoji_sentiment": processed["emoji_sentiment"],
        }

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Predict sentiment for a batch of texts."""
        return [self.predict(text) for text in texts]

    def _rule_based_predict(self, text: str) -> Dict:
        """
        Rule-based fallback sentiment prediction.
        Uses lexicon matching when the transformer model is not loaded.
        """
        processed = self.preprocessor.preprocess(text)
        clean = processed["text"]

        # Sentiment lexicons (Arabic + Darja)
        positive_words = {
            "بنين", "لذيذ", "مليح", "يجنن", "رائع", "خطير", "ممتاز",
            "عجبني", "أحسن", "قمة", "هايل", "واعر", "زين", "كلاس",
            "يستاهل", "نحبو", "طبيعي", "صحي", "نقي", "فريش",
            "bon", "bien", "super", "top", "meilleur", "excellent",
            "naturel", "pratique", "moderne",
        }
        negative_words = {
            "خايب", "سيء", "غالي", "ضار", "مر", "اصطناعي",
            "نقص", "تبدل", "ما عجبنيش", "مكانش", "خالص",
            "mauvais", "cher", "sucré", "merde", "baisse",
            "introuvable",
        }

        words = set(clean.split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)

        # Include emoji signal
        emoji_score = processed["emoji_sentiment"]

        total_signal = pos_count - neg_count + emoji_score

        if total_signal > 0:
            sentiment = "positive"
            confidence = min(0.6 + total_signal * 0.1, 0.95)
        elif total_signal < 0:
            sentiment = "negative"
            confidence = min(0.6 + abs(total_signal) * 0.1, 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {
                "positive": confidence if sentiment == "positive" else (1 - confidence) / 2,
                "neutral": confidence if sentiment == "neutral" else (1 - confidence) / 2,
                "negative": confidence if sentiment == "negative" else (1 - confidence) / 2,
            },
            "preprocessed_text": clean,
            "has_darja": processed["has_darja"],
            "has_french": processed["has_french"],
            "emojis": processed["emojis"],
            "emoji_sentiment": processed["emoji_sentiment"],
            "model": "rule-based",
        }

    def train(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        text_col: str = "text",
        label_col: str = "sentiment",
        output_dir: Optional[str] = None,
    ) -> Dict:
        """
        Fine-tune AraBERT on labeled reviews.

        Args:
            train_df: Training data with text and label columns.
            val_df: Optional validation data.
            text_col: Name of the text column.
            label_col: Name of the label column.
            output_dir: Directory to save the fine-tuned model.

        Returns:
            Training metrics dict.
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for training.")

        if self.tokenizer is None:
            self.load_model()

        # Convert labels to integers
        train_labels = [LABEL_MAP_INV[l] for l in train_df[label_col]]
        train_texts = train_df[text_col].tolist()

        # Preprocess texts
        train_texts = [self.preprocessor.clean_text(t) for t in train_texts]

        # Create dataset
        train_dataset = ReviewDataset(
            train_texts, train_labels,
            self.tokenizer, self.settings.model.max_seq_length,
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.settings.model.batch_size,
            shuffle=True,
        )

        # Optimizer
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.settings.model.learning_rate,
        )

        # Scheduler
        total_steps = len(train_loader) * self.settings.model.num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=int(total_steps * self.settings.model.warmup_ratio),
            num_training_steps=total_steps,
        )

        # Training loop
        self.model.train()
        metrics = {"train_loss": [], "epoch_losses": []}

        for epoch in range(self.settings.model.num_epochs):
            epoch_loss = 0.0
            correct = 0
            total = 0

            for batch in train_loader:
                optimizer.zero_grad()

                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                loss = outputs.loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()
                preds = torch.argmax(outputs.logits, dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

            avg_loss = epoch_loss / len(train_loader)
            accuracy = correct / total
            metrics["epoch_losses"].append(avg_loss)
            print(f"  Epoch {epoch+1}/{self.settings.model.num_epochs} — "
                  f"Loss: {avg_loss:.4f} — Accuracy: {accuracy:.4f}")

        # Save model
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            self.model.save_pretrained(output_path)
            self.tokenizer.save_pretrained(output_path)
            print(f"💾 Model saved to {output_path}")

        self.model.eval()
        return metrics

    def evaluate(self, test_df: pd.DataFrame, text_col="text", label_col="sentiment") -> Dict:
        """
        Evaluate model on test data.

        Returns:
            Dict with accuracy, f1_macro, classification_report, confusion_matrix
        """
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
        )

        predictions = self.predict_batch(test_df[text_col].tolist())
        y_pred = [p["sentiment"] for p in predictions]
        y_true = test_df[label_col].tolist()

        return {
            "accuracy": accuracy_score(y_true, y_pred),
            "f1_macro": f1_score(y_true, y_pred, average="macro"),
            "classification_report": classification_report(y_true, y_pred),
            "confusion_matrix": confusion_matrix(
                y_true, y_pred,
                labels=["positive", "neutral", "negative"],
            ).tolist(),
        }
