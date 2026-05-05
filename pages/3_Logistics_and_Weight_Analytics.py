import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Logistics & Weight – ShipInsight", page_icon="📦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root {
    --accent-teal: #00D4AA; --accent-cyan: #00B4D8;
    --accent-amber: #FFB703; --accent-rose: #E63946;
    --bg-card: rgba(30,33,48,0.85); --bg-glass: rgba(255,255,255,0.04);
    --text-primary: #F0F2F6; --text-secondary: #8B95A5;
    --border-subtle: rgba(255,255,255,0.06);
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
div[data-testid="stMetric"] {
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: 12px; padding: 16px 20px; backdrop-filter: blur(12px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,212,170,0.12);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important; font-weight: 500 !important;
    font-size: 0.82rem !important; text-transform: uppercase; letter-spacing: 0.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important; font-weight: 700 !important; font-size: 1.6rem !important;
}
.insight-box {
    background: var(--bg-card); border-left: 3px solid #00B4D8;
    border-radius: 0 10px 10px 0; padding: 14px 18px; margin: 12px 0;
    color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Data
# ──────────────────────────────────────────────
if "filtered_df" not in st.session_state:
    st.warning("⚠️ Please navigate to the **Home** page first to load data.")
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]
ai_mode = st.session_state.get("ai_mode", False)

PLOTLY_TEMPLATE = "plotly_dark"


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
# Chargeable vs Actual Weight Scatter
# ──────────────────────────────────────────────
st.markdown("### ⚖️ Chargeable Weight vs. Actual Weight")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Points above the diagonal (y=x) indicate shipments charged by volumetric weight — bulky but light packages. Clusters below the line represent dense cargo charged at actual weight. Understanding this split helps optimize packaging and pricing.</div>', unsafe_allow_html=True)

# Sample for scatter performance (100k points is too many)
scatter_data = qr("""
    SELECT
        "Actual Weight (kg)" AS actual_weight,
        "Chargeable Weight (kg)" AS chargeable_weight,
        "Weight Type" AS weight_type,
        "Revenue" AS revenue,
        "Shipment Status" AS status
    FROM filtered
    USING SAMPLE 5000
""")

fig_scatter = px.scatter(
    scatter_data, x="actual_weight", y="chargeable_weight",
    color="weight_type", size="revenue",
    size_max=12, opacity=0.6,
    color_discrete_sequence=["#00D4AA", "#00B4D8", "#FFB703", "#E63946", "#8338EC", "#FF6D00"],
    hover_data={"revenue": ":,.0f", "status": True},
    labels={
        "actual_weight": "Actual Weight (kg)",
        "chargeable_weight": "Chargeable Weight (kg)",
        "weight_type": "Weight Type",
    },
)

# Add y=x reference line
max_val = max(scatter_data["actual_weight"].max(), scatter_data["chargeable_weight"].max())
fig_scatter.add_trace(go.Scatter(
    x=[0, max_val], y=[0, max_val],
    mode="lines", name="y = x (breakeven)",
    line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dash"),
    showlegend=True,
))

fig_scatter.update_layout(
    template=PLOTLY_TEMPLATE, height=480,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
fig_scatter.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
fig_scatter.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_scatter, use_container_width=True)

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
        import google.generativeai as genai

        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            st.warning("🔑 Add `GOOGLE_API_KEY` to `.streamlit/secrets.toml` to enable AI insights.")
        else:
            genai.configure(api_key=api_key)

            context = {
                "volumetric_charged_pct": float(weight_kpi['volumetric_charged_pct'].iloc[0]),
                "avg_actual": float(weight_kpi['avg_actual'].iloc[0]),
                "avg_volumetric": float(weight_kpi['avg_volumetric'].iloc[0]),
                "weight_type_breakdown": wt[["weight_type", "shipments", "revenue", "avg_weight"]].to_dict("records"),
            }

            prompt = f"""You are a logistics operations analyst specializing in freight weight optimization.
Analyze the following weight and dimension data and provide:
1. Packaging optimization opportunities (volumetric vs actual weight analysis)
2. Weight type efficiency assessment
3. Specific recommendations to reduce volumetric charges
4. Cargo space utilization improvements

Data:
{context}

Write professionally and include specific numbers. Suggest 3 actionable improvements."""

            with st.spinner("🧠 Analyzing weight optimization…"):
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except ImportError:
        st.info("Install `google-generativeai` to enable AI features.")
    except Exception as e:
        st.error(f"AI generation failed: {e}")
