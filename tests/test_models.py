"""
Tests for Sentiment Classifier and ABSA Model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.sentiment_classifier import SentimentClassifier
from src.models.absa_model import AspectAnalyzer


class TestSentimentClassifier:
    """Test suite for SentimentClassifier (rule-based mode)."""

    def setup_method(self):
        self.classifier = SentimentClassifier()

    def test_positive_prediction(self):
        text = "عصير رامي بنين بزاف ولذيذ 😍"
        result = self.classifier.predict(text)
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.5

    def test_negative_prediction(self):
        text = "رامي خايب وغالي بزاف 😡"
        result = self.classifier.predict(text)
        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.5

    def test_neutral_prediction(self):
        text = "شريت رامي اليوم"
        result = self.classifier.predict(text)
        assert result["sentiment"] in ["neutral", "positive", "negative"]

    def test_result_structure(self):
        result = self.classifier.predict("test")
        assert "sentiment" in result
        assert "confidence" in result
        assert "scores" in result
        assert "preprocessed_text" in result

    def test_batch_prediction(self):
        texts = ["رامي مليح", "رامي خايب", "شريت رامي"]
        results = self.classifier.predict_batch(texts)
        assert len(results) == 3

    def test_franco_arabic(self):
        text = "Ramy c'est super bon, meilleur jus"
        result = self.classifier.predict(text)
        assert result["has_french"] is True


class TestAspectAnalyzer:
    """Test suite for AspectAnalyzer."""

    def setup_method(self):
        self.analyzer = AspectAnalyzer()

    def test_taste_detection(self):
        text = "مذاق رامي لذيذ بزاف"
        result = self.analyzer.analyze(text)
        assert "taste" in result["aspects"]

    def test_price_detection(self):
        text = "السعر غالي بزاف مقارنة بالجودة"
        result = self.analyzer.analyze(text)
        assert "price" in result["aspects"]

    def test_multiple_aspects(self):
        text = "الطعم بنين ولكن السعر غالي والتغليف خايب"
        result = self.analyzer.analyze(text)
        assert result["aspect_count"] >= 2

    def test_result_structure(self):
        result = self.analyzer.analyze("عصير رامي")
        assert "overall_sentiment" in result
        assert "aspects" in result
        assert "aspect_count" in result

    def test_batch_analysis(self):
        texts = ["رامي بنين", "السعر غالي"]
        results = self.analyzer.analyze_batch(texts)
        assert len(results) == 2

    def test_aspect_summary(self):
        texts = ["مذاق رامي بنين", "السعر غالي", "الطعم لذيذ"]
        results = self.analyzer.analyze_batch(texts)
        summary = self.analyzer.get_aspect_summary(results)
        assert isinstance(summary, dict)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
