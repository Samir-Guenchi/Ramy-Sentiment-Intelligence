"""
🔍 Sentiment Explorer Page
============================
Deep-dive into sentiment trends, word clouds, and filtering.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_sentiment_explorer(df):
    """Render the sentiment explorer page."""

    st.markdown("""
    <div class="main-header">
        <h1>🔍 Sentiment Explorer</h1>
        <p>استكشاف عميق لمشاعر المستهلكين | Deep Sentiment Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_products = st.multiselect(
            "🏭 Products",
            options=df["product"].unique(),
            default=df["product"].unique(),
        )

    with col2:
        selected_sentiment = st.multiselect(
            "💭 Sentiment",
            options=["positive", "negative", "neutral"],
            default=["positive", "negative", "neutral"],
        )

    with col3:
        selected_platforms = st.multiselect(
            "📱 Platform",
            options=df["platform"].unique(),
            default=df["platform"].unique(),
        )

    # Apply filters
    filtered = df[
        (df["product"].isin(selected_products)) &
        (df["sentiment"].isin(selected_sentiment)) &
        (df["platform"].isin(selected_platforms))
    ]

    st.markdown(f"**Showing {len(filtered):,} reviews**")

    # ── Sentiment Timeline ───────────────────────────────────
    st.subheader("📈 Sentiment Over Time")
    filtered_copy = filtered.copy()
    filtered_copy["timestamp"] = pd.to_datetime(filtered_copy["timestamp"])
    filtered_copy["week"] = filtered_copy["timestamp"].dt.to_period("W").astype(str)

    timeline = filtered_copy.groupby(["week", "sentiment"]).size().reset_index(name="count")

    fig = px.line(
        timeline,
        x="week",
        y="count",
        color="sentiment",
        color_discrete_map={
            "positive": "#2D8B4E",
            "negative": "#E31E24",
            "neutral": "#F7B731",
        },
        markers=True,
    )
    fig.update_layout(
        template="plotly_dark",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Week",
        yaxis_title="Number of Reviews",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Rating Distribution ──────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("⭐ Rating Distribution")
        fig = px.histogram(
            filtered,
            x="rating",
            color="sentiment",
            color_discrete_map={
                "positive": "#2D8B4E",
                "negative": "#E31E24",
                "neutral": "#F7B731",
            },
            nbins=5,
            barmode="overlay",
            opacity=0.7,
        )
        fig.update_layout(
            template="plotly_dark",
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📊 Sentiment Breakdown")
        sentiment_pct = filtered["sentiment"].value_counts(normalize=True) * 100
        fig = go.Figure(data=[go.Bar(
            x=sentiment_pct.index,
            y=sentiment_pct.values,
            marker_color=["#2D8B4E", "#E31E24", "#F7B731"],
            text=[f"{v:.1f}%" for v in sentiment_pct.values],
            textposition="auto",
        )])
        fig.update_layout(
            template="plotly_dark",
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Percentage",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Word Cloud Section ───────────────────────────────────
    st.subheader("☁️ Word Cloud")
    st.info("💡 Word cloud requires `wordcloud` and `arabic-reshaper` packages. "
            "Install them to enable this feature.")

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        # Combine all review texts
        text_positive = " ".join(filtered[filtered["sentiment"] == "positive"]["text"].tolist())
        text_negative = " ".join(filtered[filtered["sentiment"] == "negative"]["text"].tolist())

        col_wc1, col_wc2 = st.columns(2)

        with col_wc1:
            st.markdown("**✅ Positive Reviews**")
            if text_positive.strip():
                wc = WordCloud(
                    width=600, height=300,
                    background_color="#0f1117",
                    colormap="Greens",
                    font_path=None,  # Set to Arabic font path if available
                ).generate(text_positive)
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                fig.patch.set_facecolor("#0f1117")
                st.pyplot(fig)
            else:
                st.write("No positive reviews to display.")

        with col_wc2:
            st.markdown("**❌ Negative Reviews**")
            if text_negative.strip():
                wc = WordCloud(
                    width=600, height=300,
                    background_color="#0f1117",
                    colormap="Reds",
                    font_path=None,
                ).generate(text_negative)
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                fig.patch.set_facecolor("#0f1117")
                st.pyplot(fig)
            else:
                st.write("No negative reviews to display.")

    except ImportError:
        st.caption("Install: `pip install wordcloud matplotlib`")

    # ── Search Reviews ───────────────────────────────────────
    st.subheader("🔎 Search Reviews")
    search_query = st.text_input("Search in reviews (Arabic/French/English)")

    if search_query:
        matches = filtered[filtered["text"].str.contains(search_query, case=False, na=False)]
        st.write(f"Found **{len(matches)}** matching reviews")

        for _, row in matches.head(20).iterrows():
            color = "#2D8B4E" if row["sentiment"] == "positive" else "#E31E24" if row["sentiment"] == "negative" else "#F7B731"
            st.markdown(
                f'<div style="direction:rtl; background:#1a1a2e; padding:0.8rem; '
                f'border-radius:8px; margin-bottom:0.3rem; border-left:3px solid {color};">'
                f'{row["text"]}</div>',
                unsafe_allow_html=True,
            )
