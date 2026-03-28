"""
🎯 Aspect Analysis Page
========================
ABSA visualization — radar charts, heatmaps, and per-aspect drill-down.
"""

import json
from collections import defaultdict

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ASPECT_LABELS = {
    "taste": "المذاق (Taste)",
    "price": "السعر (Price)",
    "packaging": "التغليف (Packaging)",
    "availability": "التوفر (Availability)",
    "quality": "الجودة (Quality)",
    "health": "الصحة (Health)",
}

ASPECT_ICONS = {
    "taste": "🍊",
    "price": "💰",
    "packaging": "📦",
    "availability": "🏪",
    "quality": "✨",
    "health": "🏥",
}


def render_aspect_analysis(df):
    """Render the aspect analysis page."""

    st.markdown("""
    <div class="main-header">
        <h1>🎯 Aspect-Based Sentiment Analysis</h1>
        <p>تحليل المشاعر حسب الجوانب | Per-Aspect Product Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # Parse aspects from JSON
    aspect_stats = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "total": 0})

    for _, row in df.iterrows():
        try:
            aspects = json.loads(row["aspects"]) if isinstance(row["aspects"], str) else {}
        except (json.JSONDecodeError, TypeError):
            continue

        for aspect, sentiment in aspects.items():
            aspect_stats[aspect]["total"] += 1
            aspect_stats[aspect][sentiment] += 1

    if not aspect_stats:
        st.warning("No aspect data available. Run the ABSA pipeline first.")
        return

    # ── Radar Chart ──────────────────────────────────────────
    st.subheader("🎯 Aspect Sentiment Radar")

    aspects = list(ASPECT_LABELS.keys())
    pos_ratios = []
    neg_ratios = []

    for aspect in aspects:
        data = aspect_stats.get(aspect, {"positive": 0, "negative": 0, "total": 1})
        total = max(data["total"], 1)
        pos_ratios.append(data["positive"] / total * 100)
        neg_ratios.append(data["negative"] / total * 100)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=pos_ratios + [pos_ratios[0]],
        theta=[ASPECT_LABELS[a] for a in aspects] + [ASPECT_LABELS[aspects[0]]],
        fill="toself",
        name="Positive %",
        line_color="#2D8B4E",
        fillcolor="rgba(45, 139, 78, 0.3)",
    ))

    fig.add_trace(go.Scatterpolar(
        r=neg_ratios + [neg_ratios[0]],
        theta=[ASPECT_LABELS[a] for a in aspects] + [ASPECT_LABELS[aspects[0]]],
        fill="toself",
        name="Negative %",
        line_color="#E31E24",
        fillcolor="rgba(227, 30, 36, 0.3)",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
            bgcolor="rgba(0,0,0,0)",
        ),
        template="plotly_dark",
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Aspect KPI Cards ─────────────────────────────────────
    st.subheader("📊 Aspect Scores")

    cols = st.columns(3)
    for i, aspect in enumerate(aspects):
        data = aspect_stats.get(aspect, {"positive": 0, "negative": 0, "total": 0})
        total = max(data["total"], 1)
        score = round((data["positive"] - data["negative"]) / total * 100, 1)
        icon = ASPECT_ICONS.get(aspect, "📌")
        label = ASPECT_LABELS.get(aspect, aspect)

        color = "#2D8B4E" if score > 0 else "#E31E24" if score < 0 else "#F7B731"

        with cols[i % 3]:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="font-size: 2rem;">{icon}</div>
                <div class="kpi-value" style="color: {color};">{score:+.1f}%</div>
                <div class="kpi-label">{label}</div>
                <div style="color: #666; font-size: 0.8rem;">{data['total']} mentions</div>
            </div>
            <br>
            """, unsafe_allow_html=True)

    # ── Aspect Heatmap ───────────────────────────────────────
    st.subheader("🔥 Aspect × Product Heatmap")

    # Build heatmap data
    products = df["product"].unique()
    heatmap_data = []

    for product in products:
        product_df = df[df["product"] == product]
        product_aspects = defaultdict(lambda: {"pos": 0, "neg": 0, "total": 0})

        for _, row in product_df.iterrows():
            try:
                aspects_dict = json.loads(row["aspects"]) if isinstance(row["aspects"], str) else {}
            except (json.JSONDecodeError, TypeError):
                continue

            for aspect, sentiment in aspects_dict.items():
                product_aspects[aspect]["total"] += 1
                if sentiment == "positive":
                    product_aspects[aspect]["pos"] += 1
                elif sentiment == "negative":
                    product_aspects[aspect]["neg"] += 1

        row_data = {"product": product}
        for aspect in aspects:
            data = product_aspects.get(aspect, {"pos": 0, "neg": 0, "total": 1})
            total = max(data["total"], 1)
            row_data[ASPECT_LABELS[aspect]] = round(
                (data["pos"] - data["neg"]) / total * 100, 1
            )
        heatmap_data.append(row_data)

    import pandas as pd
    heatmap_df = pd.DataFrame(heatmap_data).set_index("product")

    fig = px.imshow(
        heatmap_df.values,
        x=heatmap_df.columns.tolist(),
        y=heatmap_df.index.tolist(),
        color_continuous_scale=["#E31E24", "#F7B731", "#2D8B4E"],
        aspect="auto",
        text_auto=".1f",
    )
    fig.update_layout(
        template="plotly_dark",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Aspect",
        yaxis_title="Product",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Aspect Detail Drill-down ─────────────────────────────
    st.subheader("🔎 Aspect Deep Dive")

    selected_aspect = st.selectbox(
        "Select an aspect to explore",
        options=list(ASPECT_LABELS.keys()),
        format_func=lambda x: f"{ASPECT_ICONS.get(x, '')} {ASPECT_LABELS[x]}",
    )

    if selected_aspect:
        # Filter reviews mentioning this aspect
        aspect_reviews = []
        for _, row in df.iterrows():
            try:
                aspects_dict = json.loads(row["aspects"]) if isinstance(row["aspects"], str) else {}
            except (json.JSONDecodeError, TypeError):
                continue
            if selected_aspect in aspects_dict:
                aspect_reviews.append({
                    "text": row["text"],
                    "sentiment": aspects_dict[selected_aspect],
                    "product": row["product"],
                    "wilaya": row["wilaya"],
                })

        if aspect_reviews:
            aspect_df = pd.DataFrame(aspect_reviews)
            st.write(f"**{len(aspect_df)} reviews** mention **{ASPECT_LABELS[selected_aspect]}**")

            # Show sentiment distribution for this aspect
            fig = px.pie(
                aspect_df,
                names="sentiment",
                color="sentiment",
                color_discrete_map={
                    "positive": "#2D8B4E",
                    "negative": "#E31E24",
                    "neutral": "#F7B731",
                },
                hole=0.5,
            )
            fig.update_layout(
                template="plotly_dark",
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show sample reviews
            for _, row in aspect_df.head(5).iterrows():
                color = "#2D8B4E" if row["sentiment"] == "positive" else "#E31E24" if row["sentiment"] == "negative" else "#F7B731"
                st.markdown(
                    f'<div style="direction:rtl; background:#1a1a2e; padding:0.8rem; '
                    f'border-radius:8px; margin-bottom:0.3rem; border-left:3px solid {color};">'
                    f'{row["text"]} — <span style="color:#666;">{row["product"]}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(f"No reviews found for {ASPECT_LABELS[selected_aspect]}")
