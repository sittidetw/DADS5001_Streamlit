
import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from theme import PAGE_CSS, PLOTLY_TEMPLATE, COLOR_SEQ, CHART_LAYOUT, GRID_COLOR, apply_chart_style, render_sidebar_filters

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Logistics & Weight – ShipInsight", page_icon="📦", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Data
# ──────────────────────────────────────────────
# ── Sidebar Filters (renders on every page) ───────────────────
_filtered = render_sidebar_filters()
if _filtered is None:
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]
ai_mode = st.session_state.get("ai_mode", False)


def qr(query: str) -> pd.DataFrame:
    return duckdb.query(query).to_df()


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown("## 📦 Logistics & Weight Analytics")
st.caption("Operational efficiency analysis through physical dimensions, weight categories, and cargo optimization.")
st.divider()

# ──────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────
weight_kpi = qr("""
    SELECT
        AVG("Actual Weight (kg)") AS avg_actual,
        AVG("Volumetric Weight (kg)") AS avg_volumetric,
        AVG("Chargeable Weight (kg)") AS avg_chargeable,
        SUM("Actual Weight (kg)") AS total_weight,
        COUNT(DISTINCT "Weight Type") AS weight_types,
        SUM(CASE WHEN "Chargeable Weight (kg)" > "Actual Weight (kg)" THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS volumetric_charged_pct
    FROM filtered
""")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Total Weight Shipped", f"{weight_kpi['total_weight'].iloc[0]:,.0f} kg")
with c2:
    st.metric("Avg Actual Weight", f"{weight_kpi['avg_actual'].iloc[0]:,.1f} kg")
with c3:
    st.metric("Avg Volumetric Weight", f"{weight_kpi['avg_volumetric'].iloc[0]:,.1f} kg")
with c4:
    st.metric("Avg Chargeable Weight", f"{weight_kpi['avg_chargeable'].iloc[0]:,.1f} kg")
with c5:
    st.metric("Volumetric Charged %", f"{weight_kpi['volumetric_charged_pct'].iloc[0]:.1f}%")

st.divider()

# ──────────────────────────────────────────────
# Seasonal Weight & Revenue Trends
# ──────────────────────────────────────────────
st.markdown("### 📈 Seasonal Weight & Revenue Trends")
st.markdown('''<div class="insight-box">
💡 <strong>What does this chart show?</strong> The <span style="color:#8338EC;"><strong>purple line</strong></span> tracks each month\'s total physical weight shipped (left axis). The <span style="color:#A7F3D0;"><strong>green bars</strong></span> show monthly revenue (right axis) so you can see if revenue follows the same seasonal pattern as workload. The <span style="color:#FFB703;"><strong>gold dashed line</strong></span> shows the overall weight trend. Peaks = busiest months. Use this to plan staffing, warehouse space & carrier contracts.
</div>''', unsafe_allow_html=True)

import numpy as np

trend_data = qr("""
    SELECT 
        DATE_TRUNC('month', "Order Date") AS month,
        SUM("Actual Weight (kg)") AS total_weight,
        SUM("Revenue") AS total_revenue
    FROM filtered
    WHERE "Order Date" IS NOT NULL
    GROUP BY 1
    ORDER BY 1
""")
trend_data["month"] = pd.to_datetime(trend_data["month"])
trend_data["month_str"] = trend_data["month"].dt.strftime('%b %Y')

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

# Green bars for Monthly Revenue (secondary y-axis)
fig_trend.add_trace(
    go.Bar(
        x=trend_data["month_str"], 
        y=trend_data["total_revenue"],
        name="Monthly Revenue", 
        marker_color="#A7F3D0",
        opacity=0.8,
        hovertemplate="%{x}<br>Revenue: ฿%{y:,.0f}<extra></extra>"
    ), secondary_y=True
)

# Purple line for Total Actual Weight (primary y-axis)
fig_trend.add_trace(
    go.Scatter(
        x=trend_data["month_str"], 
        y=trend_data["total_weight"],
        name="Total Actual Weight", 
        mode="lines+markers",
        line=dict(color="#8338EC", width=3), 
        marker=dict(size=9, color="#3B82F6", line=dict(color="#8338EC", width=2)),
        hovertemplate="%{x}<br>Weight: %{y:,.0f} kg<extra></extra>"
    ), secondary_y=False
)

# Gold dashed line for Weight Trend (primary y-axis)
if len(trend_data) > 1:
    x_numeric = np.arange(len(trend_data))
    z = np.polyfit(x_numeric, trend_data["total_weight"], 1)
    p = np.poly1d(z)
    
    fig_trend.add_trace(
        go.Scatter(
            x=trend_data["month_str"], 
            y=p(x_numeric),
            name="Weight Trend", 
            mode="lines",
            line=dict(color="#FFB703", width=2.5, dash="dash"),
            hoverinfo="skip"
        ), secondary_y=False
    )

    # Annotations for Peak and Low
    max_idx = trend_data["total_weight"].idxmax()
    min_idx = trend_data["total_weight"].idxmin()
    
    max_x = trend_data.loc[max_idx, "month_str"]
    max_y = trend_data.loc[max_idx, "total_weight"]
    
    min_x = trend_data.loc[min_idx, "month_str"]
    min_y = trend_data.loc[min_idx, "total_weight"]
    
    fig_trend.add_annotation(
        x=max_x, y=max_y,
        text=f"<span style='color:#ef4444'>▲</span> <span style='color:#10b981'>Peak: {max_y:,.0f} kg</span>",
        showarrow=True, arrowhead=1, arrowcolor="#fff",
        bgcolor="#1F2937", bordercolor="#374151", borderpad=4,
        ay=-40
    )
    
    fig_trend.add_annotation(
        x=min_x, y=min_y,
        text=f"<span style='color:#ef4444'>▼ Low: {min_y:,.0f} kg</span>",
        showarrow=True, arrowhead=1, arrowcolor="#fff",
        bgcolor="#1F2937", bordercolor="#374151", borderpad=4,
        ay=40
    )

fig_trend.update_layout(
    template=PLOTLY_TEMPLATE, height=480,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
fig_trend.update_yaxes(title_text="Total Actual Weight (kg)", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
fig_trend.update_yaxes(title_text="Revenue (฿)", secondary_y=True, showgrid=False)
fig_trend.update_xaxes(gridcolor="rgba(255,255,255,0.05)", tickangle=-45)

st.plotly_chart(fig_trend, use_container_width=True)

# ──────────────────────────────────────────────
# Weight Type Analysis
# ──────────────────────────────────────────────
st.divider()
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 Shipments & Revenue by Weight Type")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Weight type distribution reveals the cargo profile. Heavy/Extra-heavy types typically generate higher per-unit revenue but require specialized handling and pricing.</div>', unsafe_allow_html=True)

    wt = qr("""
        SELECT
            "Weight Type" AS weight_type,
            COUNT(*) AS shipments,
            SUM("Revenue") AS revenue,
            AVG("Revenue") AS avg_revenue,
            AVG("Actual Weight (kg)") AS avg_weight
        FROM filtered
        GROUP BY weight_type ORDER BY revenue DESC
    """)

    fig_wt = make_subplots(specs=[[{"secondary_y": True}]])

    fig_wt.add_trace(
        go.Bar(
            x=wt["weight_type"], y=wt["shipments"],
            name="Shipment Count", marker_color="#00B4D8",
            hovertemplate="%{x}<br>Shipments: %{y:,.0f}<extra></extra>"
        ), secondary_y=False
    )
    fig_wt.add_trace(
        go.Scatter(
            x=wt["weight_type"], y=wt["avg_revenue"],
            name="Avg Revenue", mode="lines+markers",
            line=dict(color="#FFB703", width=2.5), marker=dict(size=8, symbol="diamond"),
            hovertemplate="%{x}<br>Avg Rev: ฿%{y:,.0f}<extra></extra>"
        ), secondary_y=True
    )

    fig_wt.update_layout(
        template=PLOTLY_TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig_wt.update_yaxes(title_text="Shipments", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
    fig_wt.update_yaxes(title_text="Avg Revenue (฿)", secondary_y=True, gridcolor="rgba(255,255,255,0.05)")
    fig_wt.update_xaxes(gridcolor="rgba(255,255,255,0.05)")

    st.plotly_chart(fig_wt, use_container_width=True)

with col_right:
    st.markdown("### 📐 Weight Type Composition (Treemap)")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> A treemap provides a proportional view of how weight types contribute to overall revenue, making it easy to spot dominant segments at a glance.</div>', unsafe_allow_html=True)

    fig_tree = px.treemap(
        wt, path=["weight_type"], values="revenue",
        color="avg_revenue", color_continuous_scale=["#0E4D64", "#00B4D8", "#00D4AA"],
        hover_data={"shipments": ":,.0f", "avg_revenue": ":,.0f"},
    )
    fig_tree.update_layout(
        template=PLOTLY_TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_tree, use_container_width=True)

# ──────────────────────────────────────────────
# Package Dimensions Distribution
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 📏 Package Dimensions Distribution")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Understanding the distribution of Width, Length, and Height helps optimize cargo spacing, container loading, and identify opportunities for standardized packaging to reduce volumetric costs.</div>', unsafe_allow_html=True)

dim_data = qr("""
    SELECT
        "Weight Type" AS weight_type,
        "Width (cm)" AS width,
        "Length (cm)" AS length,
        "Height (cm)" AS height
    FROM filtered
    USING SAMPLE 8000
""")

# Melt for violin plot
dim_melted = dim_data.melt(
    id_vars=["weight_type"],
    value_vars=["width", "length", "height"],
    var_name="dimension", value_name="value"
)
dim_melted["dimension"] = dim_melted["dimension"].map({"width": "Width (cm)", "length": "Length (cm)", "height": "Height (cm)"})

fig_dim = px.violin(
    dim_melted, x="dimension", y="value", color="dimension",
    box=True, points=False,
    color_discrete_sequence=["#00D4AA", "#00B4D8", "#FFB703"],
    labels={"dimension": "Dimension", "value": "Measurement (cm)"},
)
fig_dim.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
)
fig_dim.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
fig_dim.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_dim, use_container_width=True)

# ──────────────────────────────────────────────
# Volumetric Efficiency Bubble Chart
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🫧 Volumetric Efficiency Analysis")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> This bubble chart maps actual weight against volumetric weight, with bubble size representing revenue. Large bubbles in the upper-left quadrant indicate high-revenue shipments where volumetric pricing dominates — potential candidates for packaging optimization.</div>', unsafe_allow_html=True)

vol_eff = qr("""
    SELECT
        "Weight Type" AS weight_type,
        AVG("Actual Weight (kg)") AS avg_actual,
        AVG("Volumetric Weight (kg)") AS avg_volumetric,
        SUM("Revenue") AS total_revenue,
        COUNT(*) AS shipments,
        AVG("Revenue") AS avg_revenue
    FROM filtered
    GROUP BY weight_type
""")

fig_bubble = px.scatter(
    vol_eff, x="avg_actual", y="avg_volumetric",
    size="total_revenue", color="weight_type",
    size_max=60, text="weight_type",
    color_discrete_sequence=["#00D4AA", "#00B4D8", "#FFB703", "#E63946", "#8338EC", "#FF6D00"],
    hover_data={"shipments": ":,.0f", "avg_revenue": ":,.0f", "total_revenue": ":,.0f"},
    labels={
        "avg_actual": "Avg Actual Weight (kg)",
        "avg_volumetric": "Avg Volumetric Weight (kg)",
        "weight_type": "Weight Type",
    },
)
fig_bubble.update_traces(textposition="top center", textfont_size=11)
fig_bubble.update_layout(
    template=PLOTLY_TEMPLATE, height=450,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig_bubble.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
fig_bubble.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_bubble, use_container_width=True)

# ──────────────────────────────────────────────
# AI Mode
# ──────────────────────────────────────────────
if ai_mode:
    st.divider()
    st.markdown("### 🤖 AI Weight Optimization Insights")

    try:
        from openai import OpenAI

        api_key = st.secrets.get("OPENROUTER_API_KEY", None)
        if not api_key:
            st.warning("🔑 Add `OPENROUTER_API_KEY` to `.streamlit/secrets.toml` to enable AI insights.")
        else:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )

            # Limit data to last 3 months for AI context
            max_date = filtered["Order Date"].max()
            min_date = max_date - pd.DateOffset(months=3)
            ai_filtered = filtered[filtered["Order Date"] >= min_date]
            
            ai_weight_kpi = duckdb.query('SELECT AVG("Actual Weight (kg)") AS avg_actual, AVG("Volumetric Weight (kg)") AS avg_volumetric, SUM(CASE WHEN "Chargeable Weight (kg)" > "Actual Weight (kg)" THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS volumetric_charged_pct FROM ai_filtered').to_df()
            ai_wt = duckdb.query('SELECT "Weight Type" AS weight_type, COUNT(*) AS shipments, SUM("Revenue") AS revenue, AVG("Actual Weight (kg)") AS avg_weight FROM ai_filtered GROUP BY weight_type ORDER BY revenue DESC').to_df()
            
            context = {
                "period": f"Last 3 months ({min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')})",
                "volumetric_charged_pct": float(ai_weight_kpi['volumetric_charged_pct'].iloc[0]) if not ai_weight_kpi.empty and pd.notna(ai_weight_kpi['volumetric_charged_pct'].iloc[0]) else 0.0,
                "avg_actual": float(ai_weight_kpi['avg_actual'].iloc[0]) if not ai_weight_kpi.empty and pd.notna(ai_weight_kpi['avg_actual'].iloc[0]) else 0.0,
                "avg_volumetric": float(ai_weight_kpi['avg_volumetric'].iloc[0]) if not ai_weight_kpi.empty and pd.notna(ai_weight_kpi['avg_volumetric'].iloc[0]) else 0.0,
                "weight_type_breakdown": ai_wt[["weight_type", "shipments", "revenue", "avg_weight"]].to_csv(index=False),
            }

            prompt = f"""Freight analyst. Give 2 packaging optimization insights and 2 recommendations to reduce volumetric charges.
Data: {context}"""

            with st.spinner("🧠 Analyzing weight optimization…"):
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b:free",
                    messages=[{"role": "user", "content": prompt}],
                )
                st.markdown(response.choices[0].message.content)

    except ImportError:
        st.info("Install `openai` to enable AI features.")
    except Exception as e:
        st.error(f"AI generation failed: {e}")
