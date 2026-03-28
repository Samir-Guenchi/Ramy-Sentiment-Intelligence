"""
🗺️ Geographic Insights Page
==============================
Per-wilaya sentiment mapping across Algeria.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd


def render_geo_insights(df):
    """Render the geographic insights page."""

    st.markdown("""
    <div class="main-header">
        <h1>🗺️ Geographic Intelligence</h1>
        <p>تحليل المشاعر حسب الولايات | Per-Wilaya Sentiment Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Compute Per-Wilaya Stats ─────────────────────────────
    geo_data = []
    for wilaya, group in df.groupby("wilaya"):
        total = len(group)
        if total < 2:
            continue
        pos = len(group[group["sentiment"] == "positive"])
        neg = len(group[group["sentiment"] == "negative"])
        score = round((pos - neg) / total * 100, 1)
        geo_data.append({
            "wilaya": wilaya,
            "total_reviews": total,
            "positive": pos,
            "negative": neg,
            "neutral": total - pos - neg,
            "sentiment_score": score,
            "avg_rating": round(group["rating"].mean(), 2),
            "top_product": group["product"].mode().iloc[0] if len(group) > 0 else "N/A",
        })

    geo_df = pd.DataFrame(geo_data).sort_values("sentiment_score", ascending=False)

    if geo_df.empty:
        st.warning("Not enough geographic data to display.")
        return

    # ── Top & Bottom Regions ─────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 Top 5 Regions (Highest Satisfaction)")
        top5 = geo_df.head(5)
        for _, row in top5.iterrows():
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, rgba(45,139,78,0.3) 0%, rgba(0,0,0,0) 100%);
                        padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;
                        border-left: 3px solid #2D8B4E;">
                <strong style="color: #2D8B4E;">{row['wilaya']}</strong>
                <span style="color: #aaa; float: left;">Score: {row['sentiment_score']:+.1f}% • {row['total_reviews']} reviews • ⭐ {row['avg_rating']}</span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.subheader("🔴 Bottom 5 Regions (Lowest Satisfaction)")
        bottom5 = geo_df.tail(5).iloc[::-1]
        for _, row in bottom5.iterrows():
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, rgba(227,30,36,0.3) 0%, rgba(0,0,0,0) 100%);
                        padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;
                        border-left: 3px solid #E31E24;">
                <strong style="color: #E31E24;">{row['wilaya']}</strong>
                <span style="color: #aaa; float: left;">Score: {row['sentiment_score']:+.1f}% • {row['total_reviews']} reviews • ⭐ {row['avg_rating']}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Bar Chart ────────────────────────────────────────────
    st.subheader("📊 Sentiment Score by Wilaya")

    # Color bars by sentiment
    colors = ["#2D8B4E" if s > 0 else "#E31E24" if s < 0 else "#F7B731"
              for s in geo_df["sentiment_score"]]

    fig = go.Figure(data=[go.Bar(
        x=geo_df["wilaya"],
        y=geo_df["sentiment_score"],
        marker_color=colors,
        text=[f"{s:+.1f}%" for s in geo_df["sentiment_score"]],
        textposition="outside",
    )])

    fig.update_layout(
        template="plotly_dark",
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Wilaya (ولاية)",
        yaxis_title="Sentiment Score (%)",
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Wilaya Detail View ───────────────────────────────────
    st.subheader("🔎 Wilaya Detail")

    selected_wilaya = st.selectbox(
        "Select a wilaya",
        options=geo_df["wilaya"].tolist(),
    )

    if selected_wilaya:
        wilaya_reviews = df[df["wilaya"] == selected_wilaya]
        wilaya_stats = geo_df[geo_df["wilaya"] == selected_wilaya].iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reviews", wilaya_stats["total_reviews"])
        with col2:
            st.metric("Sentiment Score", f"{wilaya_stats['sentiment_score']:+.1f}%")
        with col3:
            st.metric("Avg Rating", f"{wilaya_stats['avg_rating']}/5")
        with col4:
            st.metric("Top Product", wilaya_stats["top_product"])

        # Product breakdown for this wilaya
        product_breakdown = wilaya_reviews.groupby(["product", "sentiment"]).size().reset_index(name="count")

        fig = px.bar(
            product_breakdown,
            x="product",
            y="count",
            color="sentiment",
            color_discrete_map={
                "positive": "#2D8B4E",
                "negative": "#E31E24",
                "neutral": "#F7B731",
            },
            barmode="group",
            title=f"Product Sentiment in {selected_wilaya}",
        )
        fig.update_layout(
            template="plotly_dark",
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Sample reviews from this wilaya
        st.markdown(f"**Sample reviews from {selected_wilaya}:**")
        for _, row in wilaya_reviews.head(5).iterrows():
            color = "#2D8B4E" if row["sentiment"] == "positive" else "#E31E24" if row["sentiment"] == "negative" else "#F7B731"
            st.markdown(
                f'<div style="direction:rtl; background:#1a1a2e; padding:0.8rem; '
                f'border-radius:8px; margin-bottom:0.3rem; border-left:3px solid {color};">'
                f'{row["text"]}</div>',
                unsafe_allow_html=True,
            )
