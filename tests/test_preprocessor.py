"""
Tests for the Arabic/Darja Text Preprocessor.
"""

from src.data_pipeline.preprocessor import ArabicPreprocessor


class TestArabicPreprocessor:
    """Test suite for ArabicPreprocessor."""

    def setup_method(self):
        self.processor = ArabicPreprocessor()

    def test_basic_preprocessing(self):
        text = "عصير رامي بنين بزاف  😍"
        result = self.processor.preprocess(text)
        assert result["text"] != ""
        assert result["original"] == text

    def test_diacritics_removal(self):
        text = "عَصِيرٌ رَامِي"
        result = self.processor.preprocess(text)
        assert "َ" not in result["text"]
        assert "ِ" not in result["text"]
        assert "ٌ" not in result["text"]

    def test_elongation_normalization(self):
        text = "بنييييييين"
        result = self.processor.preprocess(text)
        # Should normalize to max 2 repeated chars
        assert "ييييي" not in result["text"]

    def test_url_removal(self):
        text = "شوفو هاد الرابط https://example.com عصير رامي"
        result = self.processor.preprocess(text)
        assert "https" not in result["text"]
        assert "example.com" not in result["text"]

    def test_emoji_extraction(self):
        text = "رامي ممتاز 😍👍🔥"
        result = self.processor.preprocess(text)
        assert len(result["emojis"]) > 0
        assert result["emoji_sentiment"] > 0  # Positive emojis

    def test_negative_emoji_detection(self):
        text = "رامي خايب 😡👎"
        result = self.processor.preprocess(text)
        assert result["emoji_sentiment"] < 0  # Negative emojis

    def test_darja_detection(self):
        text = "بزاف بنين هاذ العصير"
        result = self.processor.preprocess(text)
        assert result["has_darja"] is True

    def test_french_detection(self):
        text = "Ramy c'est très bon produit"
        result = self.processor.preprocess(text)
        assert result["has_french"] is True

    def test_empty_input(self):
        result = self.processor.preprocess("")
        assert result["text"] == ""
        assert result["emojis"] == []

    def test_none_input(self):
        result = self.processor.preprocess(None)
        assert result["text"] == ""

    def test_letter_normalization(self):
        processor = ArabicPreprocessor(normalize_letters=True)
        text = "إنتاج أفضل"
        result = processor.preprocess(text)
        # إ and أ should be normalized to ا
        assert "إ" not in result["text"]
        assert "أ" not in result["text"]

    def test_clean_text_shortcut(self):
        text = "عصير رامي 😍 https://test.com"
        clean = self.processor.clean_text(text)
        assert isinstance(clean, str)
        assert "https" not in clean


# Run tests
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
