"""
Tests for the Insight Engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_pipeline.simulator import ReviewSimulator
from src.analytics.insight_engine import InsightEngine


class TestInsightEngine:
    """Test suite for InsightEngine."""

    def setup_method(self):
        self.engine = InsightEngine()
        sim = ReviewSimulator()
        self.df = sim.generate_reviews(n=200, seed=42)

    def test_generate_insights(self):
        insights = self.engine.generate_insights(self.df)
        assert "overview" in insights
        assert "product_insights" in insights
        assert "geographic_insights" in insights
        assert "temporal_trends" in insights
        assert "actionable_recommendations" in insights

    def test_overview_stats(self):
        insights = self.engine.generate_insights(self.df)
        overview = insights["overview"]
        assert overview["total_reviews"] == 200
        assert "sentiment_distribution" in overview
        assert "avg_rating" in overview

    def test_arabic_summary(self):
        insights = self.engine.generate_insights(self.df)
        summary = insights["executive_summary_ar"]
        assert isinstance(summary, str)
        assert len(summary) > 50
        assert "رامي" in summary

    def test_recommendations(self):
        insights = self.engine.generate_insights(self.df)
        recs = insights["actionable_recommendations"]
        assert isinstance(recs, list)
        for rec in recs:
            assert "priority" in rec
            assert "category" in rec

    def test_geographic_insights(self):
        insights = self.engine.generate_insights(self.df)
        geo = insights["geographic_insights"]
        assert "best_region" in geo
        assert "worst_region" in geo


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
