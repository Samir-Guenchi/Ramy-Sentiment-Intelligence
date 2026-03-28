"""
Realistic Product Review Simulator
===================================
Generates synthetic but realistic Arabic/Darja product reviews
for Ramy products, mimicking actual Algerian social media language.

The simulator models:
- Realistic sentiment distributions (~55% pos, 25% neg, 20% neutral)
- Algerian Darja + MSA + Franco-Arabic code-switching
- Platform-specific patterns (Facebook, Instagram, YouTube)
- Geographic distribution across Algerian wilayas
- Temporal patterns (seasonal trends, product launches)
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from config.settings import get_settings


class ReviewSimulator:
    """
    Generates realistic synthetic product reviews for Ramy products
    in Arabic, Algerian Darja, and Franco-Arabic.
    """

    # ── Review Templates ──────────────────────────────────────────

    POSITIVE_TEMPLATES = {
        "taste": [
            "عصير رامي {variant} بزاف بنين والله 😍",
            "المذاق نتاع رامي {variant} يجنن، أحسن عصير في السوق",
            "Ramy {variant} trop bon, le goût est naturel 👍",
            "ماشاء الله على الطعم، رامي {variant} ديما في القمة",
            "ولادي يحبو رامي {variant} بزاف، كل يوم يطلبوه",
            "جربت رامي {variant} الجديد، المذاق خطير 🔥",
            "أنا ديما نشري رامي {variant} لأن الطعم طبيعي",
            "رامي {variant} le meilleur jus en Algérie sans discussion",
            "الطعم فريش ونقي، رامي {variant} ما يتبدلش 💯",
            "عصير رامي {variant} يروي العطش ومذاقه رائع ⭐",
        ],
        "price": [
            "سعر رامي معقول بالنسبة للجودة، يستاهل",
            "Le prix de Ramy est raisonnable, qualité/prix top 👍",
            "رامي سومو مليح مقارنة بالمنافسين",
            "والله السعر هايل، مقارنة بعصائر أخرى رامي أحسن",
            "في متناول الجميع وجودة عالية، هذا هو رامي 💪",
        ],
        "packaging": [
            "التغليف نتاع رامي الجديد واعر 😍 عجبني بزاف",
            "L'emballage de Ramy est moderne et pratique",
            "العلبة الجديدة مليحة وعملية، design réussi",
            "الشكل الجديد نتاع القارورة يجنن ✨",
            "التصميم الجديد كلاس، رامي دايما يتطور 👏",
        ],
        "quality": [
            "جودة رامي ماشي كيما المنتجات الأخرى، فرق كبير",
            "Qualité supérieure, on sent que c'est du naturel 🌿",
            "رامي منتج جزائري ونفتخر بيه، جودة عالمية",
            "الجودة ديال رامي تبان من أول رشفة",
            "رامي مليح خاطر 100% طبيعي بلا مواد كيميائية",
        ],
        "availability": [
            "نلقى رامي في كل مكان، الحمد لله دايما متوفر",
            "Ramy disponible partout, même dans les petits magasins",
            "رامي كاين في كل الحوانيت، هذا هو القوة 💪",
        ],
        "health": [
            "رامي طبيعي وصحي، نشربه بلا ما نخمم",
            "عصير رامي مليح للصحة، فيه فيتامينات طبيعية",
            "Ramy c'est sain et naturel, je le recommande 🌿",
        ],
    }

    NEGATIVE_TEMPLATES = {
        "taste": [
            "عصير رامي {variant} ولّا ما عندوش طعم قاع 😞",
            "المذاق تبدل بزاف، ماكانش كيما بكري",
            "Ramy {variant} trop sucré, on sent plus le fruit",
            "والله طعم رامي تبدّل، فيه بزاف سكر دروك ⚠️",
            "جربت رامي {variant} وما عجبنيش، طعم اصطناعي",
            "ولادي ما حبوش رامي {variant} الجديد، قالو طعمو غريب",
            "الطعم مش طبيعي كيما بكري، رامي لازم يراجع الوصفة",
        ],
        "price": [
            "رامي ولّا غالي بزاف، السعر طلع بلا سبب 😤",
            "Le prix a augmenté mais la qualité a baissé 👎",
            "السوم نتاع رامي ما يسواش، كاين أحسن منو وأرخص",
            "بزاف غالي مقارنة بالكمية، لازم يراجعو السعر",
        ],
        "packaging": [
            "التغليف خايب، القارورة تسرّب 😡",
            "L'emballage de merde, ça coule de partout",
            "العلبة تفتحت وحدها في الثلاجة، تغليف سيء",
            "الكرتون نتاع رامي يتمزق بسهولة 👎",
        ],
        "quality": [
            "الجودة نقصت بزاف هاد العام، رامي خاب 👎",
            "Qualité en baisse, c'est plus comme avant",
            "لقيت حاجة غريبة في العصير، الجودة مكانش",
            "رامي ولّا كيما العصائر الرخيصة، وين الجودة؟",
        ],
        "availability": [
            "ما نلقاش رامي {variant} في بلادنا، دايما خالص",
            "Ramy {variant} introuvable depuis des semaines 😞",
            "مكانش رامي في الحانوت، لازم نمشي نقلب عليه",
        ],
        "health": [
            "رامي فيه بزاف سكر، مانيش صحي 🚫",
            "Trop de sucre dans Ramy, pas bon pour les diabétiques",
            "فيه مواد حافظة بزاف، مش مليح للصغار ⚠️",
            "رامي يقولك طبيعي ولكن شوف المكونات 😤",
        ],
    }

    NEUTRAL_TEMPLATES = [
        "شريت رامي {variant} اليوم من الحانوت",
        "J'ai acheté Ramy {variant}, on verra",
        "رامي {variant} كاين في السوبيرات نتاع {wilaya}",
        "مقارنة بين رامي و {competitor}، كل واحد عندو ميزته",
        "شكون يعرف رامي {variant} يجي في حجم كبير؟",
        "واش رامي عندهم منتجات جداد؟",
        "رامي عندهم تشكيلة واسعة من العصائر",
        "شفت pub نتاع رامي في التلفزيون",
        "كل يوم نشري عصير، مرات رامي مرات حاجة أخرى",
    ]

    COMPETITORS = ["جنّات", "نقاوس", "فريال", "سليم", "تانغو"]
    PLATFORMS = ["facebook", "instagram", "youtube"]

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.products = self.settings.products
        self.wilayas = self.settings.wilayas

    def generate_reviews(
        self,
        n: int = 2000,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate n realistic synthetic reviews.

        Args:
            n: Number of reviews to generate.
            seed: Random seed for reproducibility.

        Returns:
            DataFrame with columns:
                id, text, product, variant, sentiment, aspects,
                platform, wilaya, timestamp, rating
        """
        random.seed(seed)
        reviews = []

        # Sentiment distribution: ~55% pos, 25% neg, 20% neutral
        sentiments = (
            ["positive"] * int(n * 0.55)
            + ["negative"] * int(n * 0.25)
            + ["neutral"] * int(n * 0.20)
        )
        # Fill remainder
        while len(sentiments) < n:
            sentiments.append(random.choice(["positive", "negative", "neutral"]))
        random.shuffle(sentiments)

        for i, sentiment in enumerate(sentiments):
            review = self._generate_single_review(i + 1, sentiment)
            reviews.append(review)

        df = pd.DataFrame(reviews)
        return df

    def save_reviews(
        self,
        df: pd.DataFrame,
        output_dir: Optional[Path] = None,
        formats: List[str] = None,
    ):
        """Save reviews to disk in specified formats."""
        if formats is None:
            formats = ["csv", "json"]
        if output_dir is None:
            output_dir = self.settings.data.samples_dir

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if "csv" in formats:
            df.to_csv(output_dir / "reviews.csv", index=False, encoding="utf-8-sig")

        if "json" in formats:
            df.to_json(
                output_dir / "reviews.json",
                orient="records",
                force_ascii=False,
                indent=2,
            )

        print(f"✅ Saved {len(df)} reviews to {output_dir}")

    def _generate_single_review(self, review_id: int, sentiment: str) -> Dict:
        """Generate a single review with full metadata."""
        # Pick random product
        product_key = random.choice(list(self.products.keys()))
        product = self.products[product_key]
        variant = random.choice(product["variants"])

        # Pick random aspect(s)
        if sentiment == "neutral":
            template = random.choice(self.NEUTRAL_TEMPLATES)
            text = template.format(
                variant=variant,
                wilaya=random.choice(self.wilayas),
                competitor=random.choice(self.COMPETITORS),
            )
            aspects = {}
            rating = random.choice([3, 3, 3, 4])
        else:
            templates = (
                self.POSITIVE_TEMPLATES if sentiment == "positive"
                else self.NEGATIVE_TEMPLATES
            )
            aspect = random.choice(list(templates.keys()))
            template = random.choice(templates[aspect])
            text = template.format(variant=variant)
            aspects = {
                aspect: sentiment,
            }
            # Sometimes add a secondary aspect
            if random.random() < 0.3:
                other_aspect = random.choice(
                    [a for a in templates.keys() if a != aspect]
                )
                aspects[other_aspect] = sentiment

            rating = (
                random.choice([4, 5, 5, 5]) if sentiment == "positive"
                else random.choice([1, 1, 2, 2])
            )

        # Generate timestamp (last 6 months)
        days_ago = random.randint(0, 180)
        timestamp = datetime.now() - timedelta(days=days_ago)

        return {
            "id": review_id,
            "text": text,
            "product": product["name_ar"],
            "product_key": product_key,
            "variant": variant,
            "sentiment": sentiment,
            "aspects": json.dumps(aspects, ensure_ascii=False),
            "platform": random.choice(self.PLATFORMS),
            "wilaya": random.choice(self.wilayas),
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "rating": rating,
        }


# ── CLI Entry Point ──────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Ramy Review Simulator")
    print("=" * 40)

    sim = ReviewSimulator()
    df = sim.generate_reviews(n=2000)

    print(f"\n📊 Generated {len(df)} reviews")
    print(f"\n📈 Sentiment Distribution:")
    print(df["sentiment"].value_counts().to_string())
    print(f"\n🏭 Product Distribution:")
    print(df["product"].value_counts().to_string())
    print(f"\n📱 Platform Distribution:")
    print(df["platform"].value_counts().to_string())

    sim.save_reviews(df)
    print("\n✅ Done!")
