"""
AraBERT-Based Sentiment/Intent Classifier
==========================================
Fine-tuned transformer model for Arabic/Darja analysis with configurable labels.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import torch
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

DEFAULT_LABEL_COLORS = {
    "positive": "#2D8B4E",
    "negative": "#E31E24",
    "neutral": "#F7B731",
    "improvement": "#1F6FEB",
    "question": "#8B5CF6",
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
        self.labels = list(self.settings.model.sentiment_labels)
        self.label_to_idx = {label: idx for idx, label in enumerate(self.labels)}
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        self.label_colors = {
            label: DEFAULT_LABEL_COLORS.get(label, "#94A3B8") for label in self.labels
        }
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
            num_labels=self.settings.model.num_labels_sentiment,
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
        sentiment = self.idx_to_label[pred_idx]
        scores = {
            label: float(probs[idx]) for idx, label in enumerate(self.labels)
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
        clean_lower = clean.lower()

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

        question_markers = {
            "?", "؟", "واش", "علاش", "كيفاه", "متى", "وين", "هل", "why", "when", "where"
        }
        improvement_markers = {
            "لازم", "يلزم", "نتمنى", "حبذا", "ياليت", "اقتراح", "زيدو", "نقصو", "من الافضل"
        }
        has_question = ("?" in clean_lower) or ("؟" in clean_lower) or any(
            marker in clean_lower.split() for marker in question_markers
        )
        has_improvement = any(marker in clean_lower for marker in improvement_markers)

        # Include emoji signal
        emoji_score = processed["emoji_sentiment"]

        total_signal = pos_count - neg_count + emoji_score

        if total_signal > 0:
            sentiment = "positive"
            confidence = min(0.6 + total_signal * 0.1, 0.95)
        elif total_signal < 0:
            sentiment = "negative"
            confidence = min(0.6 + abs(total_signal) * 0.1, 0.95)
        elif has_question and "question" in self.label_to_idx:
            sentiment = "question"
            confidence = 0.65
        elif has_improvement and "improvement" in self.label_to_idx:
            sentiment = "improvement"
            confidence = 0.65
        else:
            sentiment = "neutral"
            confidence = 0.5

        scores = {label: 0.0 for label in self.labels}
        if sentiment in scores:
            scores[sentiment] = confidence

        remaining = max(1e-6, 1.0 - confidence)
        other_labels = [label for label in self.labels if label != sentiment]
        if other_labels:
            share = remaining / len(other_labels)
            for label in other_labels:
                scores[label] = share

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": scores,
            "preprocessed_text": clean,
            "has_darja": processed["has_darja"],
            "has_french": processed["has_french"],
            "emojis": processed["emojis"],
            "emoji_sentiment": processed["emoji_sentiment"],
            "model": "rule-based",
        }

    def train(
        self,
        train_df,
        val_df=None,
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
        if pd is None:
            raise ImportError("pandas is required for training.")

        if self.tokenizer is None:
            self.load_model()

        def to_idx(label: str) -> int:
            norm = str(label).strip().lower()
            if norm not in self.label_to_idx:
                raise ValueError(
                    f"Unknown label '{label}'. Allowed labels: {self.labels}"
                )
            return self.label_to_idx[norm]

        # Convert labels to integers
        train_labels = [to_idx(l) for l in train_df[label_col]]
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
        metrics = {"epoch_losses": [], "epoch_accuracies": []}
        best_val_f1 = -1.0

        if output_dir is None:
            output_dir = self.settings.model.output_dir
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

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
            metrics["epoch_accuracies"].append(accuracy)
            print(f"  Epoch {epoch+1}/{self.settings.model.num_epochs} — "
                  f"Loss: {avg_loss:.4f} — Accuracy: {accuracy:.4f}")

            if val_df is not None and len(val_df) > 0:
                val_metrics = self.evaluate(val_df, text_col=text_col, label_col=label_col)
                metrics[f"epoch_{epoch+1}_val_f1_macro"] = val_metrics["f1_macro"]
                print(f"    Validation F1-macro: {val_metrics['f1_macro']:.4f}")

                if val_metrics["f1_macro"] > best_val_f1:
                    best_val_f1 = val_metrics["f1_macro"]
                    best_path = output_path / "best"
                    best_path.mkdir(parents=True, exist_ok=True)
                    self.model.save_pretrained(best_path)
                    self.tokenizer.save_pretrained(best_path)

        # Save model
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        print(f"💾 Model saved to {output_path}")

        self.model.eval()
        return metrics

    def evaluate(self, test_df, text_col="text", label_col="sentiment") -> Dict:
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
        if pd is None:
            raise ImportError("pandas is required for evaluation.")

        predictions = self.predict_batch(test_df[text_col].tolist())
        y_pred = [p["sentiment"] for p in predictions]
        y_true = [str(label).strip().lower() for label in test_df[label_col].tolist()]

        return {
            "accuracy": accuracy_score(y_true, y_pred),
            "f1_macro": f1_score(y_true, y_pred, average="macro", labels=self.labels),
            "classification_report": classification_report(
                y_true,
                y_pred,
                labels=self.labels,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                y_true, y_pred,
                labels=self.labels,
            ).tolist(),
            "labels": self.labels,
        }
