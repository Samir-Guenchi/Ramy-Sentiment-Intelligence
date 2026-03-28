"""
Arabic Text Utilities
======================
Helper functions for Arabic/Darja text processing.
"""

import re
from typing import List


class ArabicTextUtils:
    """Static utility methods for Arabic text operations."""

    @staticmethod
    def is_arabic(text: str) -> bool:
        """Check if text contains Arabic characters."""
        arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
        return bool(arabic_pattern.search(text))

    @staticmethod
    def arabic_word_count(text: str) -> int:
        """Count Arabic words in text."""
        arabic_words = re.findall(r"[\u0600-\u06FF\u0750-\u077F]+", text)
        return len(arabic_words)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract hashtags from social media text."""
        return re.findall(r"#(\w+)", text)

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract @mentions from social media text."""
        return re.findall(r"@(\w+)", text)

    @staticmethod
    def detect_language_mix(text: str) -> dict:
        """
        Detect the language composition of text.

        Returns:
            Dict with percentages of Arabic, Latin (French/English), and other characters.
        """
        if not text:
            return {"arabic": 0, "latin": 0, "other": 0}

        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        latin_chars = len(re.findall(r"[a-zA-ZÀ-ÿ]", text))
        total = arabic_chars + latin_chars

        if total == 0:
            return {"arabic": 0, "latin": 0, "other": 100}

        return {
            "arabic": round(arabic_chars / total * 100, 1),
            "latin": round(latin_chars / total * 100, 1),
            "other": round(max(0, 100 - (arabic_chars + latin_chars) / max(len(text), 1) * 100), 1),
        }

    @staticmethod
    def reshape_arabic(text: str) -> str:
        """
        Reshape Arabic text for proper display in matplotlib/wordcloud.
        Requires arabic_reshaper and python-bidi packages.
        """
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except ImportError:
            return text

    @staticmethod
    def get_stop_words() -> set:
        """Return Arabic stop words set for NLP tasks."""
        return {
            "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه",
            "ذلك", "تلك", "التي", "الذي", "الذين", "هو", "هي",
            "هم", "أنا", "نحن", "أنت", "أنتم", "كان", "كانت",
            "يكون", "ليس", "لم", "لن", "قد", "ثم", "أو", "و",
            "أن", "إن", "بعد", "قبل", "بين", "كل", "بعض",
            "هل", "ما", "لا", "نعم", "أي", "كيف", "أين",
            "متى", "لماذا", "حتى", "عند", "منذ", "خلال",
        }
