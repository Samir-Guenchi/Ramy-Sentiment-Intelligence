"""
🧪 Live Analyzer Page
=======================
INNOVATION: Real-time review analysis.
Type or paste any Arabic/Darja text and get instant AI analysis.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def render_live_analyzer():
    """Render the live analyzer page."""

    st.markdown("""
    <div class="main-header">
        <h1>🧪 Live Sentiment Analyzer</h1>
        <p>محلل المشاعر المباشر | Real-Time AI Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    > **✨ Innovation Feature**: Type or paste any Arabic, Algerian Darja, or Franco-Arabic
    > review and get instant sentiment analysis with aspect detection.
    """)

    # ── Input ────────────────────────────────────────────────
    sample_texts = [
        "عصير رامي برتقال بزاف بنين والسعر معقول 😍",
        "Ramy Up trop sucré, le goût n'est pas naturel 👎",
        "التغليف الجديد واعر ولكن السعر غالي بزاف",
        "ما نلقاش رامي في الحوانيت نتاع بلادنا 😞",
        "رامي أحسن عصير في الجزائر، جودة عالمية 🔥",
        "فيه بزاف سكر، مش مليح للصحة ⚠️",
    ]

    st.markdown("**💡 Try a sample:**")
    selected_sample = st.selectbox(
        "Select a sample review",
        options=[""] + sample_texts,
        format_func=lambda x: x if x else "— Select a sample —",
    )

    user_input = st.text_area(
        "✍️ Enter your review text (Arabic / Darja / Franco-Arabic)",
        value=selected_sample,
        height=120,
        placeholder="اكتب مراجعتك هنا...",
    )

    if st.button("🚀 Analyze", type="primary", use_container_width=True):
        if not user_input.strip():
            st.warning("Please enter some text to analyze.")
            return

        with st.spinner("🧠 Analyzing with AI..."):
            # Import models
            from src.models.sentiment_classifier import SentimentClassifier
            from src.models.absa_model import AspectAnalyzer

            classifier = SentimentClassifier()
            analyzer = AspectAnalyzer(sentiment_classifier=classifier)

            # Run analysis
            result = analyzer.analyze(user_input)

        # ── Display Results ──────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Analysis Results")

        # Overall sentiment
        sentiment = result["overall_sentiment"]
        confidence = result["overall_confidence"]

        sentiment_config = {
            "positive": {"emoji": "😊", "color": "#2D8B4E", "label": "إيجابي (Positive)"},
            "negative": {"emoji": "😞", "color": "#E31E24", "label": "سلبي (Negative)"},
            "neutral": {"emoji": "😐", "color": "#F7B731", "label": "محايد (Neutral)"},
        }

        config = sentiment_config.get(sentiment, sentiment_config["neutral"])

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {config['color']}22, {config['color']}11);
                    padding: 2rem; border-radius: 16px; text-align: center;
                    border: 2px solid {config['color']};">
            <div style="font-size: 4rem;">{config['emoji']}</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: {config['color']}; margin: 0.5rem 0;">
                {config['label']}
            </div>
            <div style="font-size: 1.2rem; color: #aaa;">
                Confidence: {confidence:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Confidence gauge
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🎯 Confidence Breakdown**")
            scores = result.get("overall_confidence", confidence)

            # Simple bar for sentiment scores
            pred_result = classifier.predict(user_input)
            if "scores" in pred_result:
                for sent, score in pred_result["scores"].items():
                    cfg = sentiment_config.get(sent, {})
                    bar_color = cfg.get("color", "#aaa")
                    st.markdown(
                        f'<div style="margin-bottom:0.3rem;">'
                        f'<span style="color:#ccc; width:80px; display:inline-block;">{sent.capitalize()}</span>'
                        f'<div style="background:#1a1a2e; border-radius:4px; overflow:hidden; display:inline-block; width:60%; height:20px; vertical-align:middle;">'
                        f'<div style="background:{bar_color}; width:{score*100}%; height:100%;"></div>'
                        f'</div>'
                        f'<span style="color:#aaa; margin-left:8px;">{score:.1%}</span></div>',
                        unsafe_allow_html=True,
                    )

        with col2:
            st.markdown("**🔍 Text Properties**")
            st.write(f"- **Has Darja**: {'✅ Yes' if result['has_darja'] else '❌ No'}")
            st.write(f"- **Has French**: {'✅ Yes' if result['has_french'] else '❌ No'}")
            st.write(f"- **Preprocessed**: `{result['preprocessed_text'][:100]}...`" if len(result['preprocessed_text']) > 100 else f"- **Preprocessed**: `{result['preprocessed_text']}`")

        # ── Aspect Results ───────────────────────────────────
        if result["aspects"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🎯 Detected Aspects")

            aspect_icons = {
                "taste": "🍊", "price": "💰", "packaging": "📦",
                "availability": "🏪", "quality": "✨", "health": "🏥",
            }

            cols = st.columns(min(len(result["aspects"]), 3))
            for i, (aspect, data) in enumerate(result["aspects"].items()):
                icon = aspect_icons.get(aspect, "📌")
                cfg = sentiment_config.get(data["sentiment"], {})

                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div style="font-size: 2rem;">{icon}</div>
                        <div style="font-size: 1rem; font-weight: 600; color: white; margin: 0.5rem 0;">
                            {data.get('label_ar', aspect)}
                        </div>
                        <div class="sentiment-{data['sentiment']}" style="display: inline-block;">
                            {data['sentiment'].upper()}
                        </div>
                        <div style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">
                            Confidence: {data['confidence']:.1%}
                        </div>
                        <div style="color: #555; font-size: 0.75rem; margin-top: 0.3rem;">
                            Keywords: {', '.join(data.get('keywords_found', [])[:3])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No specific product aspects detected in this text.")

        # ── Raw JSON ─────────────────────────────────────────
        with st.expander("🔧 Raw Analysis Output (JSON)"):
            import json
            st.json(result)
