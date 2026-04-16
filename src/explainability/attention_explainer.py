"""
Attention-Based Explainable AI for Arabic Sentiment Analysis
=============================================================

This module extracts and visualises attention-based token attributions
from the fine-tuned AraBERT model, answering the question:
    "WHY did the model predict this sentiment?"

Techniques implemented:
    1. Attention Rollout  — aggregated multi-layer attention flow
    2. Gradient × Attention — gradient-weighted attention for class-specific saliency
    3. Token Attribution Map — human-readable word-level importance scores

These are model-intrinsic explanations (no external library needed) that
work with any HuggingFace Transformer model.

Author: Ramy Sentiment Intelligence Team (AI EXPO 2026)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    import torch.nn.functional as F
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ── Utility ──────────────────────────────────────────────────


def _merge_subword_scores(
    tokens: List[str],
    scores: np.ndarray,
    tokenizer_type: str = "wordpiece",
) -> List[Tuple[str, float]]:
    """
    Merge sub-word token scores back into whole-word scores.

    AraBERT uses WordPiece tokenisation, so a word like "عصيرات" may be
    split into ["عصير", "##ات"].  We sum the sub-word contributions.
    """
    merged: List[Tuple[str, float]] = []
    current_word = ""
    current_score = 0.0

    for tok, sc in zip(tokens, scores):
        if tok in ("[CLS]", "[SEP]", "[PAD]", "<s>", "</s>", "<pad>"):
            continue
        if tok.startswith("##"):
            current_word += tok[2:]
            current_score += float(sc)
        else:
            if current_word:
                merged.append((current_word, current_score))
            current_word = tok
            current_score = float(sc)

    if current_word:
        merged.append((current_word, current_score))

    return merged


def _normalize_scores(scores: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Normalize attribution scores using contribution share.

    Min-max scaling can force the lowest token to 0 even when it still
    contributes non-trivially. For short customer comments, share-based
    normalization is more stable and easier to interpret.
    """
    if not scores:
        return scores

    arr = np.array([max(0.0, float(s)) for _, s in scores], dtype=np.float64)
    if arr.size == 0:
        return scores

    # Add a very small floor to avoid misleading exact-0 values caused by
    # tiny numerical differences in very short sequences.
    arr = arr + 1e-8
    total = float(arr.sum())
    if total <= 0:
        uniform = 1.0 / len(scores)
        return [(w, uniform) for w, _ in scores]

    arr = arr / total
    return [(w, float(v)) for (w, _), v in zip(scores, arr)]


# ── Core Explainer ───────────────────────────────────────────


class AttentionExplainer:
    """
    Provides attention-based model explanations for sentiment predictions.

    Three explanation strategies are available:

        1. ``attention_rollout``
           Computes aggregated attention flow across all layers. This
           captures how information propagates through the transformer.

        2. ``gradient_attention``
           Multiplies attention weights by input-gradient magnitudes.
           This is class-specific — it shows which tokens are important
           *for the predicted class* specifically.

        3. ``combined``
           Mean of both methods, giving a balanced attribution score.

    Usage::

        explainer = AttentionExplainer("models/checkpoints/h100_arabert_ft/final_model")
        result = explainer.explain("عصير رامي بنين والسعر مناسب")
        # result = {
        #   'text': '...',
        #   'predicted_class': 'positive',
        #   'confidence': 0.993,
        #   'word_attributions': [('عصير', 0.12), ('رامي', 0.31), ('بنين', 0.89), ...],
        #   'top_positive_tokens': [('بنين', 0.89), ('مناسب', 0.71), ...],
        #   'top_negative_tokens': [],
        #   'explanation_text': "The model predicted 'positive' because ..."
        # }
    """

    SENTIMENT_EMOJI = {
        "positive": "😊",
        "negative": "😞",
        "neutral": "😐",
        "improvement": "💡",
        "question": "❓",
    }

    def __init__(
        self,
        model_path: str | Path,
        device: Optional[str] = None,
    ) -> None:
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch and Transformers are required for explainability. "
                "Install with: pip install torch transformers"
            )

        self.model_path = Path(model_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_path),
            output_attentions=True,
        )
        self.model.to(self.device)
        self.model.eval()

        # Read id2label from model config
        self.id2label = self.model.config.id2label
        self.label2id = self.model.config.label2id

    # ── Public API ────────────────────────────────────────

    def explain(
        self,
        text: str,
        method: str = "combined",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate an explanation for a single text prediction.

        Args:
            text: Input text (Arabic/Darija/French).
            method: One of 'attention_rollout', 'gradient_attention', 'combined'.
            top_k: Number of top tokens to highlight.

        Returns:
            Dictionary with prediction, attributions, and natural-language explanation.
        """
        encoding = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            return_offsets_mapping=False,
        )
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0].cpu().tolist())

        # ── Forward pass with attentions ──
        if method in ("gradient_attention", "combined"):
            # Need gradients for gradient×attention
            embeddings = self.model.get_input_embeddings()(input_ids)
            embeddings.requires_grad_(True)
            embeddings.retain_grad()

            outputs = self.model(
                inputs_embeds=embeddings,
                attention_mask=attention_mask,
                output_attentions=True,
            )
        else:
            with torch.no_grad():
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    output_attentions=True,
                )

        logits = outputs.logits
        attentions = outputs.attentions  # tuple of (batch, heads, seq, seq)

        # ── Prediction ──
        probs = F.softmax(logits, dim=-1)[0]
        pred_idx = int(torch.argmax(probs).item())
        pred_class = self.id2label.get(pred_idx, str(pred_idx))
        confidence = float(probs[pred_idx].item())
        all_scores = {
            self.id2label.get(i, str(i)): float(probs[i].item())
            for i in range(len(probs))
        }

        # ── Compute attributions ──
        seq_len = input_ids.shape[1]

        if method == "attention_rollout" or method == "combined":
            rollout_scores = self._attention_rollout(attentions, seq_len)
        else:
            rollout_scores = np.zeros(seq_len)

        if method == "gradient_attention" or method == "combined":
            grad_attn_scores = self._gradient_attention(
                logits, embeddings, attentions, pred_idx, seq_len
            )
        else:
            grad_attn_scores = np.zeros(seq_len)

        # ── Combine ──
        if method == "combined":
            raw_scores = 0.5 * rollout_scores + 0.5 * grad_attn_scores
        elif method == "attention_rollout":
            raw_scores = rollout_scores
        else:
            raw_scores = grad_attn_scores

        # ── Merge sub-words ──
        word_scores = _merge_subword_scores(tokens, raw_scores)
        word_scores = _normalize_scores(word_scores)

        # ── Sort by importance ──
        sorted_scores = sorted(word_scores, key=lambda x: x[1], reverse=True)
        top_tokens = sorted_scores[:top_k]

        # ── Generate natural-language explanation ──
        explanation = self._generate_explanation(
            text=text,
            pred_class=pred_class,
            confidence=confidence,
            top_tokens=top_tokens,
        )

        return {
            "text": text,
            "predicted_class": pred_class,
            "confidence": confidence,
            "all_scores": all_scores,
            "word_attributions": word_scores,
            "top_tokens": top_tokens,
            "method": method,
            "explanation_text": explanation,
            "emoji": self.SENTIMENT_EMOJI.get(pred_class, ""),
        }

    def explain_batch(
        self,
        texts: List[str],
        method: str = "combined",
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Explain a batch of texts (sequential for accuracy)."""
        return [self.explain(t, method=method, top_k=top_k) for t in texts]

    def generate_html_highlight(
        self,
        result: Dict[str, Any],
        title: Optional[str] = None,
    ) -> str:
        """
        Generate an HTML snippet that highlights tokens by importance.

        Positive-sentiment words are highlighted in green; negative in red;
        neutral in blue — scaled by attribution strength.
        """
        pred = result["predicted_class"]
        conf = result["confidence"]
        emoji = result.get("emoji", "")
        word_attrs = result["word_attributions"]

        # Colour mapping based on predicted sentiment
        if pred in ("positive",):
            base_color = (45, 139, 78)   # green
        elif pred in ("negative",):
            base_color = (227, 30, 36)   # red
        elif pred in ("improvement",):
            base_color = (31, 111, 235)  # blue
        elif pred in ("question",):
            base_color = (139, 92, 246)  # purple
        else:
            base_color = (247, 183, 49)  # gold

        html_parts = []
        for word, score in word_attrs:
            alpha = max(0.08, min(score, 1.0))
            r, g, b = base_color
            bg = f"rgba({r},{g},{b},{alpha:.2f})"
            border_style = f"border-bottom: 2px solid rgba({r},{g},{b},{min(alpha*2, 1.0):.2f})"
            html_parts.append(
                f'<span style="background:{bg};{border_style};padding:2px 4px;'
                f'margin:1px;border-radius:4px;display:inline-block;'
                f'direction:rtl;unicode-bidi:embed" '
                f'title="Score: {score:.3f}">{word}</span>'
            )

        highlights = " ".join(html_parts)

        title_html = f"<h3>{title}</h3>" if title else ""

        return f"""
        <div style="font-family:'Noto Sans Arabic','Inter',sans-serif;
                    padding:16px;background:#f8f9fa;border-radius:12px;
                    margin-bottom:12px;border:1px solid #e2e8f0;">
            {title_html}
            <div style="margin-bottom:8px;">
                <strong>Prediction:</strong>
                <span style="background:{'#2D8B4E' if pred=='positive' else '#E31E24' if pred=='negative' else '#F7B731'};
                      color:white;padding:4px 12px;border-radius:20px;font-size:0.9rem;">
                    {emoji} {pred.upper()} ({conf:.1%})
                </span>
            </div>
            <div style="direction:rtl;text-align:right;line-height:2.2;font-size:1.1rem;">
                {highlights}
            </div>
        </div>
        """

    # ── Private Methods ───────────────────────────────────

    def _attention_rollout(
        self,
        attentions: Tuple[torch.Tensor, ...],
        seq_len: int,
    ) -> np.ndarray:
        """
        Attention Rollout (Abnar & Zuidema, 2020).

        Recursively multiplies attention matrices across layers, adding
        residual connections (identity matrix). This captures the total
        information flow from input tokens to the [CLS] token.
        """
        # Average across heads
        att_mats = []
        for att in attentions:
            # att shape: (batch, heads, seq, seq)
            avg = att[0].mean(dim=0).detach().cpu().numpy()  # (seq, seq)
            att_mats.append(avg)

        # Rollout: multiply layer by layer with residual
        rollout = np.eye(seq_len)
        for att in att_mats:
            # Add residual connection
            att_with_residual = 0.5 * att + 0.5 * np.eye(seq_len)
            # Re-normalise rows
            row_sums = att_with_residual.sum(axis=-1, keepdims=True)
            att_with_residual = att_with_residual / np.clip(row_sums, 1e-9, None)
            rollout = rollout @ att_with_residual

        # CLS token is at position 0 — get its attention to all other tokens
        cls_attention = rollout[0]
        return cls_attention

    def _gradient_attention(
        self,
        logits: torch.Tensor,
        embeddings: torch.Tensor,
        attentions: Tuple[torch.Tensor, ...],
        target_class: int,
        seq_len: int,
    ) -> np.ndarray:
        """
        Gradient × Attention attribution.

        Multiplies the attention weights by the gradient of the target class
        logit w.r.t. the input embeddings. This gives class-specific saliency.
        """
        # Backward pass for the target class
        self.model.zero_grad()
        logits[0, target_class].backward(retain_graph=True)

        if embeddings.grad is None:
            return np.zeros(seq_len)

        # Gradient magnitude per token
        grad_norms = embeddings.grad[0].norm(dim=-1).detach().cpu().numpy()

        # Average attention across all layers and heads for [CLS]
        attn_to_cls = np.zeros(seq_len)
        for att in attentions:
            avg = att[0].mean(dim=0).detach().cpu().numpy()
            attn_to_cls += avg[0]  # attention FROM [CLS] TO each token
        attn_to_cls /= len(attentions)

        # Element-wise product
        attribution = grad_norms * attn_to_cls
        return attribution

    def _generate_explanation(
        self,
        text: str,
        pred_class: str,
        confidence: float,
        top_tokens: List[Tuple[str, float]],
    ) -> str:
        """Generate a human-readable natural-language explanation."""
        emoji = self.SENTIMENT_EMOJI.get(pred_class, "")

        informative = [(w, s) for w, s in top_tokens if s >= 0.05]
        display_tokens = informative[:3] if informative else top_tokens[:3]
        token_str = ", ".join([f'"{w}" ({s:.0%})' for w, s in display_tokens])

        if not token_str:
            token_str = "no strong token-level signal"

        explanations = {
            "positive": f"{emoji} The model classified this as POSITIVE with {confidence:.1%} confidence. "
                        f"Top relative tokens: {token_str}. "
                        "Scores are relative within this sentence, not standalone word sentiment labels.",
            "negative": f"{emoji} The model classified this as NEGATIVE with {confidence:.1%} confidence. "
                        f"Top relative tokens: {token_str}. "
                        "Scores are relative within this sentence, not standalone word sentiment labels.",
            "neutral":  f"{emoji} The model classified this as NEUTRAL with {confidence:.1%} confidence. "
                        f"Top relative tokens: {token_str}. "
                        "Signal is diffuse, so no single token dominates the decision.",
            "improvement": f"{emoji} The model detected an IMPROVEMENT SUGGESTION with {confidence:.1%} confidence. "
                           f"Top relative tokens: {token_str}. "
                           "Scores are relative within this sentence, not standalone word sentiment labels.",
            "question": f"{emoji} The model detected a QUESTION with {confidence:.1%} confidence. "
                        f"Top relative tokens: {token_str}. "
                        "Scores are relative within this sentence, not standalone word sentiment labels.",
        }

        return explanations.get(
            pred_class,
            f"The model predicted '{pred_class}' with {confidence:.1%} confidence."
        )
