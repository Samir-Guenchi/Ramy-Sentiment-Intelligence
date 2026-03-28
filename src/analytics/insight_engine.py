"""
Business Intelligence Insight Engine
======================================
Generates actionable insights from sentiment analysis results.
Produces structured reports for Ramy's decision-makers.
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config.settings import get_settings


class InsightEngine:
    """
    Transforms raw sentiment data into actionable business intelligence.

    Capabilities:
        - Geographic sentiment analysis (per-wilaya)
        - Temporal trend detection
        - Product comparison analytics
        - Automated insight generation
        - Arabic executive summary generation
    """

    def __init__(self):
        self.settings = get_settings()

    def generate_insights(self, df: pd.DataFrame) -> Dict:
        """
        Generate complete business intelligence report from review data.

        Args:
            df: DataFrame with columns: text, product, sentiment, aspects,
                wilaya, timestamp, rating, platform

        Returns:
            Comprehensive insights dictionary.
        """
        insights = {
            "generated_at": datetime.now().isoformat(),
            "total_reviews": len(df),
            "overview": self._overview_stats(df),
            "product_insights": self._product_insights(df),
            "geographic_insights": self._geographic_insights(df),
            "temporal_trends": self._temporal_trends(df),
            "aspect_insights": self._aspect_insights(df),
            "platform_breakdown": self._platform_breakdown(df),
            "actionable_recommendations": self._generate_recommendations(df),
            "executive_summary_ar": self._generate_arabic_summary(df),
        }

        return insights

    def _overview_stats(self, df: pd.DataFrame) -> Dict:
        """Compute high-level overview statistics."""
        sentiment_dist = df["sentiment"].value_counts().to_dict()
        total = len(df)

        return {
            "total_reviews": total,
            "sentiment_distribution": sentiment_dist,
            "sentiment_percentages": {
                k: round(v / total * 100, 1)
                for k, v in sentiment_dist.items()
            },
            "avg_rating": round(df["rating"].mean(), 2),
            "unique_products": df["product"].nunique(),
            "unique_wilayas": df["wilaya"].nunique(),
            "date_range": {
                "start": str(df["timestamp"].min()),
                "end": str(df["timestamp"].max()),
            },
        }

    def _product_insights(self, df: pd.DataFrame) -> Dict:
        """Generate per-product sentiment analysis."""
        products = {}

        for product, group in df.groupby("product"):
            sentiment_dist = group["sentiment"].value_counts().to_dict()
            total = len(group)

            products[product] = {
                "total_reviews": total,
                "avg_rating": round(group["rating"].mean(), 2),
                "sentiment_distribution": sentiment_dist,
                "sentiment_score": round(
                    (sentiment_dist.get("positive", 0) - sentiment_dist.get("negative", 0))
                    / total * 100, 1
                ),
                "top_platform": group["platform"].mode().iloc[0] if len(group) > 0 else "N/A",
                "top_wilaya": group["wilaya"].mode().iloc[0] if len(group) > 0 else "N/A",
            }

        # Sort by sentiment score
        products = dict(
            sorted(products.items(), key=lambda x: x[1]["sentiment_score"], reverse=True)
        )

        return products

    def _geographic_insights(self, df: pd.DataFrame) -> Dict:
        """Analyze sentiment by geographic region (wilaya)."""
        geo = {}

        for wilaya, group in df.groupby("wilaya"):
            total = len(group)
            if total < 3:  # Skip wilayas with too few reviews
                continue

            sentiment_dist = group["sentiment"].value_counts().to_dict()
            geo[wilaya] = {
                "total_reviews": total,
                "sentiment_score": round(
                    (sentiment_dist.get("positive", 0) - sentiment_dist.get("negative", 0))
                    / total * 100, 1
                ),
                "dominant_sentiment": group["sentiment"].mode().iloc[0],
                "top_product": group["product"].mode().iloc[0],
            }

        # Find best and worst regions
        if geo:
            best = max(geo.items(), key=lambda x: x[1]["sentiment_score"])
            worst = min(geo.items(), key=lambda x: x[1]["sentiment_score"])
        else:
            best = worst = ("N/A", {"sentiment_score": 0})

        return {
            "per_wilaya": geo,
            "best_region": {"name": best[0], **best[1]},
            "worst_region": {"name": worst[0], **worst[1]},
        }

    def _temporal_trends(self, df: pd.DataFrame) -> Dict:
        """Detect temporal sentiment trends."""
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["month"] = df["timestamp"].dt.to_period("M").astype(str)

        monthly = {}
        for month, group in df.groupby("month"):
            total = len(group)
            sentiment_dist = group["sentiment"].value_counts().to_dict()
            monthly[month] = {
                "total_reviews": total,
                "sentiment_score": round(
                    (sentiment_dist.get("positive", 0) - sentiment_dist.get("negative", 0))
                    / total * 100, 1
                ),
                "avg_rating": round(group["rating"].mean(), 2),
            }

        # Trend detection
        scores = [(m, d["sentiment_score"]) for m, d in sorted(monthly.items())]
        if len(scores) >= 2:
            trend = "improving" if scores[-1][1] > scores[0][1] else "declining"
        else:
            trend = "stable"

        return {
            "monthly": monthly,
            "overall_trend": trend,
        }

    def _aspect_insights(self, df: pd.DataFrame) -> Dict:
        """Analyze aspect-level sentiments across all reviews."""
        aspect_stats = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "total": 0})

        for _, row in df.iterrows():
            try:
                aspects = json.loads(row["aspects"]) if isinstance(row["aspects"], str) else row["aspects"]
            except (json.JSONDecodeError, TypeError):
                continue

            for aspect, sentiment in aspects.items():
                aspect_stats[aspect]["total"] += 1
                aspect_stats[aspect][sentiment] += 1

        # Compute ratios
        result = {}
        for aspect, stats in aspect_stats.items():
            total = stats["total"]
            if total > 0:
                result[aspect] = {
                    "total_mentions": total,
                    "positive_ratio": round(stats["positive"] / total * 100, 1),
                    "negative_ratio": round(stats["negative"] / total * 100, 1),
                    "neutral_ratio": round(stats["neutral"] / total * 100, 1),
                    "sentiment_score": round(
                        (stats["positive"] - stats["negative"]) / total * 100, 1
                    ),
                }

        return result

    def _platform_breakdown(self, df: pd.DataFrame) -> Dict:
        """Analyze sentiment distribution per platform."""
        platforms = {}
        for platform, group in df.groupby("platform"):
            total = len(group)
            sentiment_dist = group["sentiment"].value_counts().to_dict()
            platforms[platform] = {
                "total_reviews": total,
                "sentiment_distribution": sentiment_dist,
                "avg_rating": round(group["rating"].mean(), 2),
                "sentiment_score": round(
                    (sentiment_dist.get("positive", 0) - sentiment_dist.get("negative", 0))
                    / total * 100, 1
                ),
            }
        return platforms

    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Generate actionable business recommendations."""
        recommendations = []
        aspect_data = self._aspect_insights(df)
        geo_data = self._geographic_insights(df)
        product_data = self._product_insights(df)

        # Aspect-based recommendations
        for aspect, data in aspect_data.items():
            if data["negative_ratio"] > 40:
                aspect_ar = self.settings.aspects.aspect_labels_ar.get(aspect, aspect)
                recommendations.append({
                    "priority": "high",
                    "category": "product_improvement",
                    "aspect": aspect,
                    "message_en": f"{data['negative_ratio']}% of reviews mentioning '{aspect}' "
                                  f"are negative. Immediate attention needed.",
                    "message_ar": f"{data['negative_ratio']}% من المراجعات المتعلقة ب"
                                  f"'{aspect_ar}' سلبية. يتطلب اهتماماً فورياً.",
                })

        # Geographic recommendations
        worst = geo_data.get("worst_region", {})
        if worst.get("sentiment_score", 0) < -20:
            recommendations.append({
                "priority": "medium",
                "category": "regional_strategy",
                "message_en": f"Region '{worst.get('name')}' has the lowest sentiment "
                              f"score ({worst.get('sentiment_score')}%). "
                              f"Consider targeted marketing or quality improvements.",
                "message_ar": f"ولاية '{worst.get('name')}' لديها أدنى معدل رضا "
                              f"({worst.get('sentiment_score')}%). "
                              f"يُنصح بحملة تسويقية مستهدفة.",
            })

        # Product recommendations
        for product, data in product_data.items():
            if data["sentiment_score"] < -10:
                recommendations.append({
                    "priority": "high",
                    "category": "product_review",
                    "message_en": f"Product '{product}' has a negative sentiment "
                                  f"score ({data['sentiment_score']}%). Review product quality.",
                    "message_ar": f"منتج '{product}' لديه معدل رضا سلبي "
                                  f"({data['sentiment_score']}%). مراجعة جودة المنتج مطلوبة.",
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))

        return recommendations

    def _generate_arabic_summary(self, df: pd.DataFrame) -> str:
        """
        Generate an executive summary in Arabic.
        This is the INNOVATION feature: Generative Insight Engine.
        """
        overview = self._overview_stats(df)
        total = overview["total_reviews"]
        pos_pct = overview["sentiment_percentages"].get("positive", 0)
        neg_pct = overview["sentiment_percentages"].get("negative", 0)
        avg_rating = overview["avg_rating"]

        geo = self._geographic_insights(df)
        best_region = geo.get("best_region", {}).get("name", "غير محدد")
        worst_region = geo.get("worst_region", {}).get("name", "غير محدد")

        aspect_data = self._aspect_insights(df)
        worst_aspect = None
        worst_neg = 0
        for aspect, data in aspect_data.items():
            if data["negative_ratio"] > worst_neg:
                worst_neg = data["negative_ratio"]
                worst_aspect = self.settings.aspects.aspect_labels_ar.get(aspect, aspect)

        summary = f"""
📊 تقرير تحليل مشاعر المستهلكين — رامي

تم تحليل {total} مراجعة من وسائل التواصل الاجتماعي.

📈 النتائج الرئيسية:
• {pos_pct}% من المراجعات إيجابية و {neg_pct}% سلبية
• متوسط التقييم: {avg_rating}/5
• أفضل ولاية من حيث الرضا: {best_region}
• أضعف ولاية من حيث الرضا: {worst_region}
"""

        if worst_aspect:
            summary += f"• الجانب الأكثر انتقاداً: {worst_aspect} ({worst_neg}% سلبي)\n"

        summary += """
💡 التوصيات:
يُنصح فريق رامي بالتركيز على تحسين الجوانب ذات التقييم المنخفض
وتعزيز التواجد في الولايات ذات الرضا الضعيف.

— نظام الذكاء الاصطناعي لتحليل المشاعر | رامي
"""

        return summary.strip()
