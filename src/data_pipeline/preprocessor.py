"""
Arabic & Algerian Darja Text Preprocessor
==========================================
Handles the unique challenges of Algerian social media text:
- MSA / Darja code-switching
- Franco-Arabic (Arabizi) transliteration
- Emoji sentiment extraction
- Diacritics and elongation normalization
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple


class ArabicPreprocessor:
    """
    Comprehensive Arabic/Darja text preprocessor designed for
    Algerian social media content analysis.
    """

    # Arabic diacritics (tashkeel)
    DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652]")

    # Tatweel (kashida) — decorative elongation
    TATWEEL = re.compile(r"\u0640")

    # Character elongation (e.g., بنييييين → بنين)
    ELONGATION = re.compile(r"(.)\1{2,}")

    # Arabic-specific punctuation normalization
    ARABIC_PUNCT = {
        "،": ",",
        "؛": ";",
        "؟": "?",
        "٪": "%",
    }

    # Letter normalization (common Algerian spelling variants)
    LETTER_NORM = {
        "إ": "ا",
        "أ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }

    # Common Algerian Darja → MSA mappings
    DARJA_NORMALIZATIONS = {
        "بزاف": "كثير",
        "واش": "ماذا",
        "كاين": "يوجد",
        "ماكانش": "لا يوجد",
        "هدرا": "كلام",
        "خويا": "أخي",
        "ختي": "أختي",
        "نتاع": "خاص ب",
        "ديال": "خاص ب",
        "كيفاش": "كيف",
        "وقتاش": "متى",
        "وين": "أين",
        "شحال": "كم",
    }

    # Franco-Arabic (Arabizi) character map
    ARABIZI_MAP = {
        "3": "ع",
        "7": "ح",
        "9": "ق",
        "5": "خ",
        "2": "ء",
        "6": "ط",
        "8": "غ",
    }

    # Emoji sentiment lexicon
    POSITIVE_EMOJIS = {"😍", "❤️", "👍", "🔥", "💯", "😋", "🤤", "💪", "⭐", "✨", "👏", "🥰", "😊"}
    NEGATIVE_EMOJIS = {"😡", "👎", "🤢", "🤮", "💔", "😤", "😠", "🚫", "⚠️", "💀", "😢", "😞"}

    def __init__(
        self,
        normalize_letters: bool = True,
        remove_diacritics: bool = True,
        normalize_elongation: bool = True,
        extract_emojis: bool = True,
        normalize_darja: bool = False,  # Optional — may alter meaning
    ):
        self.normalize_letters = normalize_letters
        self.remove_diacritics = remove_diacritics
        self.normalize_elongation = normalize_elongation
        self.extract_emojis = extract_emojis
        self.normalize_darja = normalize_darja

    def preprocess(self, text: str) -> Dict:
        """
        Full preprocessing pipeline.

        Returns:
            Dict with keys:
                - 'text': cleaned text
                - 'emojis': list of extracted emojis
                - 'emoji_sentiment': float (-1 to 1) based on emoji analysis
                - 'has_darja': bool indicating Darja presence
                - 'has_french': bool indicating French code-switching
                - 'original': original text
        """
        if not text or not isinstance(text, str):
            return {
                "text": "",
                "emojis": [],
                "emoji_sentiment": 0.0,
                "has_darja": False,
                "has_french": False,
                "original": text or "",
            }

        original = text

        # Extract emojis before cleaning
        emojis, emoji_sentiment = self._extract_emoji_sentiment(text)

        # Detect language features
        has_darja = self._detect_darja(text)
        has_french = self._detect_french(text)

        # Cleaning pipeline
        text = self._remove_urls(text)
        text = self._remove_mentions_hashtags(text)
        text = self._remove_emojis(text)

        if self.remove_diacritics:
            text = self._remove_diacritics(text)

        text = self._remove_tatweel(text)

        if self.normalize_elongation:
            text = self._normalize_elongation(text)

        if self.normalize_letters:
            text = self._normalize_arabic_letters(text)

        text = self._normalize_punctuation(text)

        if self.normalize_darja:
            text = self._normalize_darja_words(text)

        text = self._normalize_whitespace(text)

        return {
            "text": text.strip(),
            "emojis": emojis,
            "emoji_sentiment": emoji_sentiment,
            "has_darja": has_darja,
            "has_french": has_french,
            "original": original,
        }

    def clean_text(self, text: str) -> str:
        """Simple text cleaning — returns only the cleaned string."""
        result = self.preprocess(text)
        return result["text"]

    # ── Private Methods ──────────────────────────────────

    def _remove_urls(self, text: str) -> str:
        return re.sub(r"https?://\S+|www\.\S+", " ", text)

    def _remove_mentions_hashtags(self, text: str) -> str:
        text = re.sub(r"@\w+", " ", text)
        # Keep hashtag text, remove symbol
        text = re.sub(r"#(\w+)", r"\1", text)
        return text

    def _remove_emojis(self, text: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Misc symbols
            "\U0001F680-\U0001F6FF"  # Transport
            "\U0001F1E0-\U0001F1FF"  # Flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(" ", text)

    def _remove_diacritics(self, text: str) -> str:
        return self.DIACRITICS.sub("", text)

    def _remove_tatweel(self, text: str) -> str:
        return self.TATWEEL.sub("", text)

    def _normalize_elongation(self, text: str) -> str:
        return self.ELONGATION.sub(r"\1\1", text)

    def _normalize_arabic_letters(self, text: str) -> str:
        for src, tgt in self.LETTER_NORM.items():
            text = text.replace(src, tgt)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        for src, tgt in self.ARABIC_PUNCT.items():
            text = text.replace(src, tgt)
        return text

    def _normalize_darja_words(self, text: str) -> str:
        words = text.split()
        normalized = [self.DARJA_NORMALIZATIONS.get(w, w) for w in words]
        return " ".join(normalized)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text)

    def _extract_emoji_sentiment(self, text: str) -> Tuple[List[str], float]:
        """Extract emojis and compute emoji-based sentiment score."""
        emojis = []
        for char in text:
            if unicodedata.category(char).startswith(("So",)):
                emojis.append(char)
            elif char in self.POSITIVE_EMOJIS or char in self.NEGATIVE_EMOJIS:
                emojis.append(char)

        if not emojis:
            return emojis, 0.0

        pos = sum(1 for e in emojis if e in self.POSITIVE_EMOJIS)
        neg = sum(1 for e in emojis if e in self.NEGATIVE_EMOJIS)
        total = pos + neg
        if total == 0:
            return emojis, 0.0

        return emojis, (pos - neg) / total

    def _detect_darja(self, text: str) -> bool:
        """Detect Algerian Darja markers in text."""
        darja_markers = set(self.DARJA_NORMALIZATIONS.keys())
        words = set(text.split())
        return bool(words & darja_markers)

    def _detect_french(self, text: str) -> bool:
        """Detect French words (common in Algerian code-switching)."""
        french_markers = {
            "très", "bien", "bon", "pas", "mais", "avec", "pour",
            "comme", "dans", "trop", "super", "qualité", "prix",
            "produit", "goût", "naturel", "emballage",
        }
        words = set(text.lower().split())
        return bool(words & french_markers)


# ── Module-level convenience function ─────────────────

def preprocess_text(text: str, **kwargs) -> str:
    """Quick preprocessing with default settings."""
    processor = ArabicPreprocessor(**kwargs)
    return processor.clean_text(text)
