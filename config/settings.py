"""
Centralized configuration for Ramy Sentiment Intelligence System.
Uses environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class ModelConfig:
    """NLP model configuration."""
    name: str = os.getenv("MODEL_NAME", "aubmindlab/bert-base-arabertv02")
    cache_dir: str = os.getenv("MODEL_CACHE_DIR", str(BASE_DIR / "models_cache"))
    max_seq_length: int = int(os.getenv("MAX_SEQ_LENGTH", "256"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "16"))
    num_labels_sentiment: int = 3  # Positive, Negative, Neutral
    learning_rate: float = 2e-5
    num_epochs: int = 5
    warmup_ratio: float = 0.1


@dataclass
class DataConfig:
    """Data pipeline configuration."""
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    raw_dir: Path = field(default=None)
    processed_dir: Path = field(default=None)
    samples_dir: Path = field(default=None)
    num_simulated_reviews: int = 2000
    test_split: float = 0.2
    val_split: float = 0.1

    def __post_init__(self):
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.samples_dir = self.data_dir / "samples"


@dataclass
class AspectConfig:
    """Aspect-Based Sentiment Analysis configuration."""
    aspects: List[str] = field(default_factory=lambda: [
        "taste",       # المذاق
        "price",       # السعر
        "packaging",   # التغليف
        "availability",# التوفر
        "quality",     # الجودة
        "health",      # الصحة
    ])
    aspect_labels_ar: dict = field(default_factory=lambda: {
        "taste": "المذاق",
        "price": "السعر",
        "packaging": "التغليف",
        "availability": "التوفر",
        "quality": "الجودة",
        "health": "الصحة",
    })

    # Keywords for aspect detection (Arabic + Darja)
    aspect_keywords: dict = field(default_factory=lambda: {
        "taste": [
            "مذاق", "طعم", "نكهة", "بنين", "لذيذ", "bnin", "goût",
            "حلو", "مر", "حامض", "سكر", "ماكلش", "يجنن",
        ],
        "price": [
            "سعر", "ثمن", "غالي", "رخيص", "prix", "cher", "سوم",
            "مكاش", "يسوا", "فلوس", "دينار",
        ],
        "packaging": [
            "تغليف", "علبة", "قارورة", "غلاف", "emballage", "bouteille",
            "بلاستيك", "كرتون", "شكل", "ديزاين",
        ],
        "availability": [
            "متوفر", "نلقاه", "مكانش", "يخلص", "disponible",
            "حانوت", "سوبيرات", "مغازة", "يلقى",
        ],
        "quality": [
            "جودة", "qualité", "نوعية", "مليح", "خايب", "صحي",
            "طبيعي", "naturel", "bio", "زين",
        ],
        "health": [
            "صحة", "سكر", "سكري", "كالوري", "santé", "sucre",
            "مواد حافظة", "كيميائي", "طبيعي", "ضار",
        ],
    })


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    port: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    language: str = os.getenv("DASHBOARD_LANGUAGE", "ar")
    theme_primary: str = "#E31E24"   # Ramy Red
    theme_secondary: str = "#2D8B4E" # Ramy Green
    theme_accent: str = "#F7B731"    # Ramy Gold
    theme_bg: str = "#0F1117"        # Dark background
    page_title: str = "Ramy Sentiment Intelligence"
    page_icon: str = "🧠"


# Algerian Wilayas for geographic analysis
WILAYAS = [
    "أدرار", "الشلف", "الأغواط", "أم البواقي", "باتنة", "بجاية", "بسكرة",
    "بشار", "البليدة", "البويرة", "تمنراست", "تبسة", "تلمسان", "تيارت",
    "تيزي وزو", "الجزائر", "الجلفة", "جيجل", "سطيف", "سعيدة",
    "سكيكدة", "سيدي بلعباس", "عنابة", "قالمة", "قسنطينة", "المدية",
    "مستغانم", "المسيلة", "معسكر", "ورقلة", "وهران", "البيض",
    "إليزي", "برج بوعريريج", "بومرداس", "الطارف", "تندوف",
    "تيسمسيلت", "الوادي", "خنشلة", "سوق أهراس", "تيبازة",
    "ميلة", "عين الدفلى", "النعامة", "عين تموشنت", "غرداية",
    "غليزان", "تيميمون", "برج باجي مختار", "أولاد جلال",
    "بني عباس", "إن صالح", "إن قزام", "توقرت",
    "جانت", "المغير", "المنيعة", "عين قزام",
]

# Ramy product catalog
RAMY_PRODUCTS = {
    "ramy_juice": {
        "name_ar": "عصير رامي",
        "name_fr": "Ramy Jus",
        "category": "juice",
        "variants": ["برتقال", "تفاح", "مانجو", "فواكه مشكلة", "عنب", "أناناس"],
    },
    "ramy_up": {
        "name_ar": "رامي أب",
        "name_fr": "Ramy Up",
        "category": "juice",
        "variants": ["برتقال", "مانجو", "كوكتيل"],
    },
    "ramy_drink": {
        "name_ar": "رامي درينك",
        "name_fr": "Ramy Drink",
        "category": "soft_drink",
        "variants": ["ليمون", "برتقال", "فراولة"],
    },
    "ramy_water": {
        "name_ar": "مياه رامي",
        "name_fr": "Ramy Water",
        "category": "water",
        "variants": ["طبيعي", "غازي"],
    },
    "ramy_dairy": {
        "name_ar": "حليب رامي",
        "name_fr": "Ramy Lait",
        "category": "dairy",
        "variants": ["حليب كامل", "حليب نصف دسم", "ياغورت"],
    },
}


@dataclass
class Settings:
    """Main settings container."""
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    aspects: AspectConfig = field(default_factory=AspectConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    wilayas: List[str] = field(default_factory=lambda: WILAYAS)
    products: dict = field(default_factory=lambda: RAMY_PRODUCTS)


_settings = None


def get_settings() -> Settings:
    """Get or create singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
