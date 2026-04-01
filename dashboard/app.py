"""
🧠 Ramy Sentiment Intelligence Dashboard
==========================================
Main Streamlit application entry point.
Multi-page dashboard with Ramy branding.
"""

import streamlit as st

# ── Page Config (must be first Streamlit command) ──────────
st.set_page_config(
    page_title="Ramy Sentiment Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', 'Noto Sans Arabic', sans-serif;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #E31E24 0%, #B71C1C 50%, #2D8B4E 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(227, 30, 36, 0.3);
    }

    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #F7B731;
    }

    .kpi-label {
        font-size: 0.9rem;
        color: #aaa;
        margin-top: 0.5rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }

    /* Sentiment badges */
    .sentiment-positive {
        background: #2D8B4E;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .sentiment-negative {
        background: #E31E24;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .sentiment-neutral {
        background: #F7B731;
        color: #1a1a2e;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Academic badge */
    .expo-badge {
        background: linear-gradient(135deg, #6C63FF, #3F51B5);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Ramy Intelligence")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "📊 Executive Overview",
            "🔍 Sentiment Explorer",
            "🎯 Aspect Analysis",
            "🗺️ Geographic Insights",
            "🧪 Live Analyzer",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        '<div class="expo-badge">🎓 AI EXPO 2026 — Blida 1</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.caption("Industry Track • Product Review Analysis")
    st.caption("Partner: **Ramy Group** 🇩🇿")


# ── Load Data ──────────────────────────────────────────────
@st.cache_data
def load_review_data():
    """Load review data for dashboard, with schema fallback for train CSV files."""
    import os
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    from src.data_pipeline.simulator import ReviewSimulator
    import pandas as pd

    configured_path = os.getenv("REVIEW_DATA_PATH", "").strip()
    if configured_path:
        configured_file = Path(configured_path)
        if configured_file.exists():
            sep = ";" if configured_file.suffix.lower() == ".csv" else ","
            df = pd.read_csv(configured_file, sep=sep)
            # Adapt training-style schema (text;product;label) for dashboard pages.
            if "label" in df.columns and "sentiment" not in df.columns:
                df = df.rename(columns={"label": "sentiment"})
            if "rating" not in df.columns:
                df["rating"] = 3
            if "platform" not in df.columns:
                df["platform"] = "dataset"
            if "wilaya" not in df.columns:
                df["wilaya"] = "غير محدد"
            if "timestamp" not in df.columns:
                df["timestamp"] = pd.Timestamp.now().isoformat()
            if "aspects" not in df.columns:
                df["aspects"] = "{}"
            return df

    sample_path = project_root / "data" / "samples" / "reviews.csv"

    if sample_path.exists():
        return pd.read_csv(sample_path)
    else:
        # Generate on-the-fly
        sim = ReviewSimulator()
        df = sim.generate_reviews(n=2000)
        sim.save_reviews(df)
        return df


# ── Page Router ────────────────────────────────────────────
df = load_review_data()

if page == "📊 Executive Overview":
    from pages.overview import render_overview
    render_overview(df)

elif page == "🔍 Sentiment Explorer":
    from pages.sentiment_explorer import render_sentiment_explorer
    render_sentiment_explorer(df)

elif page == "🎯 Aspect Analysis":
    from pages.aspect_analysis import render_aspect_analysis
    render_aspect_analysis(df)

elif page == "🗺️ Geographic Insights":
    from pages.geo_insights import render_geo_insights
    render_geo_insights(df)

elif page == "🧪 Live Analyzer":
    from pages.live_analyzer import render_live_analyzer
    render_live_analyzer()
