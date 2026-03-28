"""
Aspect-Based Sentiment Analysis (ABSA) Model
==============================================
Extracts product aspects from reviews and determines per-aspect sentiment.

Aspects:
    1. المذاق (Taste)      4. التوفر (Availability)
    2. السعر (Price)       5. الجودة (Quality)
    3. التغليف (Packaging)  6. الصحة (Health)

Architecture:
    Step 1: Aspect Detection — keyword + contextual matching
    Step 2: Aspect Sentiment — per-aspect sentiment classification
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from config.settings import get_settings
from src.data_pipeline.preprocessor import ArabicPreprocessor
from src.models.sentiment_classifier import SentimentClassifier


class AspectAnalyzer:
    """
    Aspect-Based Sentiment Analysis for Ramy product reviews.

    Combines keyword-based aspect detection with transformer-based
    sentiment classification for each detected aspect.

    Usage:
        analyzer = AspectAnalyzer()
        result = analyzer.analyze("عصير رامي بنين ولكن غالي بزاف")
        # {
        #   'aspects': {
        #     'taste': {'detected': True, 'sentiment': 'positive', 'confidence': 0.88},
        #     'price': {'detected': True, 'sentiment': 'negative', 'confidence': 0.82},
        #   },
        #   'overall_sentiment': 'positive',
        #   'aspect_count': 2
        # }
    """

    def __init__(self, sentiment_classifier: Optional[SentimentClassifier] = None):
        self.settings = get_settings()
        self.preprocessor = ArabicPreprocessor()
        self.classifier = sentiment_classifier or SentimentClassifier()
        self.aspect_keywords = self.settings.aspects.aspect_keywords
        self.aspect_labels_ar = self.settings.aspects.aspect_labels_ar

        # Extended context windows for aspect-sentiment linking
        self.positive_modifiers = {
            "بنين", "مليح", "لذيذ", "رائع", "ممتاز", "هايل", "واعر",
            "يجنن", "خطير", "قمة", "أحسن", "طبيعي", "صحي", "نقي",
            "كلاس", "زين", "يستاهل", "معقول", "عملي", "متوفر",
            "bon", "bien", "super", "top", "meilleur", "naturel",
            "excellent", "pratique", "disponible", "raisonnable",
        }

        self.negative_modifiers = {
            "خايب", "سيء", "غالي", "ضار", "مر", "اصطناعي", "كيميائي",
            "نقص", "تبدل", "مكانش", "خالص", "يسرّب", "يتمزق",
            "mauvais", "cher", "sucré", "baisse", "introuvable",
            "artificiel",
        }

    def analyze(self, text: str) -> Dict:
        """
        Perform full aspect-based sentiment analysis.

        Args:
            text: The review text in Arabic/Darja.

        Returns:
            Dictionary containing detected aspects with their sentiments.
        """
        processed = self.preprocessor.preprocess(text)
        clean_text = processed["text"]
        words = clean_text.split()
        words_set = set(words)

        # Step 1: Detect aspects
        detected_aspects = {}
        for aspect, keywords in self.aspect_keywords.items():
            # Check for keyword matches
            matched_keywords = []
            for keyword in keywords:
                if keyword in clean_text:
                    matched_keywords.append(keyword)

            if matched_keywords:
                # Step 2: Determine per-aspect sentiment
                aspect_sentiment = self._classify_aspect_sentiment(
                    clean_text, words_set, matched_keywords, processed
                )
                detected_aspects[aspect] = {
                    "detected": True,
                    "sentiment": aspect_sentiment["sentiment"],
                    "confidence": aspect_sentiment["confidence"],
                    "keywords_found": matched_keywords,
                    "label_ar": self.aspect_labels_ar[aspect],
                }

        # Overall sentiment
        overall = self.classifier.predict(text)

        # Compute aspect summary
        aspect_sentiments = [a["sentiment"] for a in detected_aspects.values()]
        sentiment_counts = {
            "positive": aspect_sentiments.count("positive"),
            "negative": aspect_sentiments.count("negative"),
            "neutral": aspect_sentiments.count("neutral"),
        }

        return {
            "text": text,
            "preprocessed_text": clean_text,
            "overall_sentiment": overall["sentiment"],
            "overall_confidence": overall["confidence"],
            "aspects": detected_aspects,
            "aspect_count": len(detected_aspects),
            "aspect_sentiment_summary": sentiment_counts,
            "has_darja": processed["has_darja"],
            "has_french": processed["has_french"],
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze a batch of reviews."""
        return [self.analyze(text) for text in texts]

    def get_aspect_summary(self, results: List[Dict]) -> Dict:
        """
        Generate an aggregate summary across multiple reviews.

        Args:
            results: List of analyze() results.

        Returns:
            Aggregate statistics per aspect.
        """
        summary = {}

        for aspect in self.aspect_keywords.keys():
            aspect_data = {
                "total_mentions": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_confidence": 0.0,
                "all_keywords": [],
            }

            confidences = []
            for result in results:
                if aspect in result["aspects"]:
                    asp = result["aspects"][aspect]
                    aspect_data["total_mentions"] += 1
                    aspect_data[asp["sentiment"]] += 1
                    confidences.append(asp["confidence"])
                    aspect_data["all_keywords"].extend(asp["keywords_found"])

            if confidences:
                aspect_data["avg_confidence"] = sum(confidences) / len(confidences)

            # Compute sentiment ratio
            total = aspect_data["total_mentions"]
            if total > 0:
                aspect_data["positive_ratio"] = aspect_data["positive"] / total
                aspect_data["negative_ratio"] = aspect_data["negative"] / total
                aspect_data["neutral_ratio"] = aspect_data["neutral"] / total
            else:
                aspect_data["positive_ratio"] = 0
                aspect_data["negative_ratio"] = 0
                aspect_data["neutral_ratio"] = 0

            # Top keywords
            keyword_freq = defaultdict(int)
            for kw in aspect_data["all_keywords"]:
                keyword_freq[kw] += 1
            aspect_data["top_keywords"] = sorted(
                keyword_freq.items(), key=lambda x: x[1], reverse=True
            )[:5]
            del aspect_data["all_keywords"]

            summary[aspect] = aspect_data

        return summary

    def _classify_aspect_sentiment(
        self,
        text: str,
        words_set: set,
        matched_keywords: List[str],
        processed: Dict,
    ) -> Dict:
        """
        Classify sentiment for a specific aspect using context window analysis.
        """
        # Check for positive/negative modifiers near aspect keywords
        pos_signal = len(words_set & self.positive_modifiers)
        neg_signal = len(words_set & self.negative_modifiers)

        # Check negation patterns
        negation_patterns = ["ما", "مش", "ماشي", "لا", "بلا", "مكانش", "pas", "ne"]
        has_negation = any(neg in text for neg in negation_patterns)

        # Emoji signal
        emoji_signal = processed.get("emoji_sentiment", 0)

        # Compute final sentiment
        total_signal = pos_signal - neg_signal + emoji_signal

        # Negation flips sentiment
        if has_negation and abs(total_signal) > 0:
            # Only flip if negation is near a sentiment word
            total_signal *= -0.5  # Partial flip (negation is noisy)

        if total_signal > 0:
            sentiment = "positive"
            confidence = min(0.6 + abs(total_signal) * 0.08, 0.95)
        elif total_signal < 0:
            sentiment = "negative"
            confidence = min(0.6 + abs(total_signal) * 0.08, 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {"sentiment": sentiment, "confidence": confidence}
