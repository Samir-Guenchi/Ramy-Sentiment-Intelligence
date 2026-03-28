"""
📊 Executive Overview Page
===========================
High-level KPIs, sentiment distribution, and recent reviews.
"""

import json

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_overview(df):
    """Render the executive overview dashboard page."""

    # ── Header ───────────────────────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Ramy Sentiment Intelligence</h1>
        <p>نظام ذكاء اصطناعي لتحليل مشاعر المستهلكين | AI-Powered Consumer Insights</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    total = len(df)
    pos_count = len(df[df["sentiment"] == "positive"])
    neg_count = len(df[df["sentiment"] == "negative"])
    avg_rating = df["rating"].mean()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total:,}</div>
            <div class="kpi-label">📝 Total Reviews</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        pos_pct = round(pos_count / total * 100, 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #2D8B4E;">{pos_pct}%</div>
            <div class="kpi-label">😊 Positive Sentiment</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        neg_pct = round(neg_count / total * 100, 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #E31E24;">{neg_pct}%</div>
            <div class="kpi-label">😞 Negative Sentiment</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color: #F7B731;">{avg_rating:.1f}/5</div>
            <div class="kpi-label">⭐ Average Rating</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ───────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Sentiment Distribution")
        sentiment_counts = df["sentiment"].value_counts()
        fig = go.Figure(data=[go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.5,
            marker_colors=["#2D8B4E", "#E31E24", "#F7B731"],
            textinfo="percent+label",
            textfont=dict(size=14),
        )])
        fig.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🏭 Sentiment by Product")
        product_sentiment = df.groupby(["product", "sentiment"]).size().reset_index(name="count")
        fig = px.bar(
            product_sentiment,
            x="product",
            y="count",
            color="sentiment",
            color_discrete_map={
                "positive": "#2D8B4E",
                "negative": "#E31E24",
                "neutral": "#F7B731",
            },
            barmode="group",
        )
        fig.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Reviews",
            legend_title="Sentiment",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Platform Breakdown ───────────────────────────────────
    st.subheader("📱 Reviews by Platform")
    platform_data = df.groupby(["platform", "sentiment"]).size().reset_index(name="count")
    fig = px.bar(
        platform_data,
        x="platform",
        y="count",
        color="sentiment",
        color_discrete_map={
            "positive": "#2D8B4E",
            "negative": "#E31E24",
            "neutral": "#F7B731",
        },
        barmode="stack",
    )
    fig.update_layout(
        template="plotly_dark",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Recent Reviews ───────────────────────────────────────
    st.subheader("📝 Recent Reviews")
    recent = df.sort_values("timestamp", ascending=False).head(10)

    for _, row in recent.iterrows():
        sentiment_class = f"sentiment-{row['sentiment']}"
        st.markdown(
            f"""
            <div style="background: #1a1a2e; padding: 1rem; border-radius: 8px;
                        margin-bottom: 0.5rem; border-left: 3px solid
                        {'#2D8B4E' if row['sentiment']=='positive' else '#E31E24' if row['sentiment']=='negative' else '#F7B731'};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ccc; direction: rtl; flex: 1;">{row['text']}</span>
                    <span class="{sentiment_class}" style="margin-left: 1rem; white-space: nowrap;">
                        {row['sentiment'].upper()}
                    </span>
                </div>
                <div style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">
                    {row['product']} • {row['platform']} • {row['wilaya']} • ⭐ {row['rating']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
