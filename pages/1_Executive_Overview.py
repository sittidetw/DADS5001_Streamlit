import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Executive Overview – ShipInsight", page_icon="📊", layout="wide")

# ── Shared CSS (injected per page for consistency) ──
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
    background: var(--bg-card); border-left: 3px solid var(--accent-teal);
    border-radius: 0 10px 10px 0; padding: 14px 18px; margin: 12px 0;
    color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Data & Helpers
# ──────────────────────────────────────────────
if "filtered_df" not in st.session_state or "df" not in st.session_state:
    st.warning("⚠️ Please navigate to the **Home** page first to load data.")
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]
ai_mode = st.session_state.get("ai_mode", False)

PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = ["#00D4AA", "#00B4D8", "#FFB703", "#E63946", "#8338EC", "#FF6D00", "#06D6A0", "#118AB2"]


def qr(query: str) -> pd.DataFrame:
    """Run DuckDB query against the filtered dataframe."""
    return duckdb.query(query).to_df()


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown("## 📊 Executive Overview")
st.caption("High-level business pulse — KPIs, trends, and shipment status breakdown.")
st.divider()

# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
kpi = qr("""
    SELECT
        COUNT(*) AS total_shipments,
        SUM("Revenue") AS total_revenue,
        AVG("Revenue") AS avg_revenue,
        COUNT(DISTINCT "Customer ID") AS unique_customers,
        SUM(CASE WHEN "FTB (First time buyer)" = 'Yes' THEN 1 ELSE 0 END) AS ftb_count
    FROM filtered
""")

# Calculate period-over-period deltas
date_start = st.session_state.get("date_start", filtered["Order Date"].min())
date_end = st.session_state.get("date_end", filtered["Order Date"].max())
period_length = (date_end - date_start).days
prev_start = date_start - pd.Timedelta(days=period_length)
prev_end = date_start - pd.Timedelta(days=1)

prev = df[(df["Order Date"] >= prev_start) & (df["Order Date"] <= prev_end)]

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    delta_ship = None
    if len(prev) > 0:
        delta_ship = f"{((len(filtered) - len(prev)) / len(prev) * 100):+.1f}%"
    st.metric("Total Shipments", f"{kpi['total_shipments'].iloc[0]:,.0f}", delta=delta_ship)
with c2:
    prev_rev = prev["Revenue"].sum() if len(prev) > 0 else 0
    cur_rev = kpi["total_revenue"].iloc[0]
    delta_rev = f"{((cur_rev - prev_rev) / prev_rev * 100):+.1f}%" if prev_rev > 0 else None
    st.metric("Total Revenue", f"฿{cur_rev:,.0f}", delta=delta_rev)
with c3:
    st.metric("Avg Revenue / Shipment", f"฿{kpi['avg_revenue'].iloc[0]:,.0f}")
with c4:
    st.metric("Active Customers", f"{kpi['unique_customers'].iloc[0]:,.0f}")
with c5:
    ftb_pct = kpi["ftb_count"].iloc[0] / kpi["total_shipments"].iloc[0] * 100
    st.metric("First-Time Buyers", f"{ftb_pct:.1f}%")

st.divider()

# ──────────────────────────────────────────────
# Revenue & Volume Trend
# ──────────────────────────────────────────────
st.markdown("### 📈 Revenue & Shipment Volume Trend")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Track monthly revenue trajectory alongside shipment volume to identify whether growth is driven by higher volume or higher value per shipment.</div>', unsafe_allow_html=True)

trend = qr("""
    SELECT
        DATE_TRUNC('month', "Order Date") AS month,
        SUM("Revenue") AS revenue,
        COUNT(*) AS shipments,
        AVG("Revenue") AS avg_revenue
    FROM filtered
    GROUP BY 1
    ORDER BY month
""")
trend["month"] = pd.to_datetime(trend["month"])

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

fig_trend.add_trace(
    go.Bar(
        x=trend["month"], y=trend["shipments"],
        name="Shipments", marker_color="rgba(0,180,216,0.35)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Shipments: %{y:,.0f}<extra></extra>"
    ),
    secondary_y=False,
)

fig_trend.add_trace(
    go.Scatter(
        x=trend["month"], y=trend["revenue"],
        name="Revenue", mode="lines+markers",
        line=dict(color="#00D4AA", width=3), marker=dict(size=6),
        hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: ฿%{y:,.0f}<extra></extra>"
    ),
    secondary_y=True,
)

fig_trend.update_layout(
    template=PLOTLY_TEMPLATE, height=420,
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
fig_trend.update_yaxes(title_text="Shipment Count", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
fig_trend.update_yaxes(title_text="Revenue (฿)", secondary_y=True, gridcolor="rgba(255,255,255,0.05)")
fig_trend.update_xaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_trend, use_container_width=True)

# ──────────────────────────────────────────────
# Shipment Status & Direction
# ──────────────────────────────────────────────
col_left, col_right = st.columns(2)

# -- Shipment Status Donut --
with col_left:
    st.markdown("### 🎯 Shipment Status Breakdown")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Monitor the proportion of completed vs. exception/in-transit shipments. A rising exception rate signals operational bottlenecks that require immediate attention.</div>', unsafe_allow_html=True)

    status = qr("""
        SELECT "Shipment Status" AS status, COUNT(*) AS cnt,
               SUM("Revenue") AS revenue
        FROM filtered
        GROUP BY status ORDER BY cnt DESC
    """)

    status_colors = {"Completed": "#00D4AA", "Exception": "#E63946", "In Transit": "#FFB703"}
    colors = [status_colors.get(s, "#8B95A5") for s in status["status"]]

    fig_status = go.Figure(go.Pie(
        labels=status["status"], values=status["cnt"],
        hole=0.55, marker=dict(colors=colors),
        textinfo="label+percent", textposition="outside",
        hovertemplate="<b>%{label}</b><br>Count: %{value:,.0f}<br>Share: %{percent}<extra></extra>"
    ))
    fig_status.update_layout(
        template=PLOTLY_TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[dict(text=f"{len(filtered):,}<br><span style='font-size:0.7em;color:#8B95A5'>shipments</span>",
                          x=0.5, y=0.5, font_size=20, font_color="#F0F2F6",
                          showarrow=False)]
    )
    st.plotly_chart(fig_status, use_container_width=True)

# -- Inbound vs Outbound --
with col_right:
    st.markdown("### 🔄 Inbound vs. Outbound Revenue")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Assess the directional balance of trade. A heavy outbound bias may indicate export-driven growth, while inbound dominance suggests import dependency.</div>', unsafe_allow_html=True)

    direction = qr("""
        SELECT "Inbound/Outbound" AS direction,
               COUNT(*) AS shipments,
               SUM("Revenue") AS revenue,
               AVG("Revenue") AS avg_revenue
        FROM filtered
        GROUP BY direction
    """)

    dir_colors = {"Outbound": "#00B4D8", "Inbound": "#FFB703"}
    d_colors = [dir_colors.get(d, "#8B95A5") for d in direction["direction"]]

    fig_dir = go.Figure(go.Pie(
        labels=direction["direction"], values=direction["revenue"],
        hole=0.55, marker=dict(colors=d_colors),
        textinfo="label+percent", textposition="outside",
        hovertemplate="<b>%{label}</b><br>Revenue: ฿%{value:,.0f}<br>Share: %{percent}<extra></extra>"
    ))
    fig_dir.update_layout(
        template=PLOTLY_TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[dict(
            text=f"฿{direction['revenue'].sum():,.0f}<br><span style='font-size:0.7em;color:#8B95A5'>total revenue</span>",
            x=0.5, y=0.5, font_size=16, font_color="#F0F2F6", showarrow=False
        )]
    )
    st.plotly_chart(fig_dir, use_container_width=True)

# ──────────────────────────────────────────────
# Top Industries & Sales Channels
# ──────────────────────────────────────────────
st.divider()
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 🏭 Revenue by Industry")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Identify which industries drive the most revenue and whether diversification is needed to reduce sector-concentration risk.</div>', unsafe_allow_html=True)

    industry = qr("""
        SELECT "Industry" AS industry,
               SUM("Revenue") AS revenue,
               COUNT(*) AS shipments
        FROM filtered
        GROUP BY industry ORDER BY revenue DESC
    """)

    fig_ind = px.bar(
        industry, x="revenue", y="industry", orientation="h",
        color="revenue", color_continuous_scale=["#0E4D64", "#00B4D8", "#00D4AA"],
        hover_data={"shipments": ":,.0f", "revenue": ":,.0f"},
        labels={"revenue": "Revenue (฿)", "industry": "Industry"},
    )
    fig_ind.update_layout(
        template=PLOTLY_TEMPLATE, height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
    )
    fig_ind.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_ind.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_ind, use_container_width=True)

with col_b:
    st.markdown("### 👤 Revenue by Sales Person")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Evaluate individual sales performance. Disproportionate reliance on a single salesperson poses risk if that channel is disrupted.</div>', unsafe_allow_html=True)

    sales = qr("""
        SELECT "Sales Person" AS salesperson,
               SUM("Revenue") AS revenue,
               COUNT(*) AS shipments
        FROM filtered
        GROUP BY salesperson ORDER BY revenue DESC
    """)

    fig_sales = px.bar(
        sales, x="revenue", y="salesperson", orientation="h",
        color="revenue", color_continuous_scale=["#3D1C56", "#8338EC", "#C77DFF"],
        hover_data={"shipments": ":,.0f", "revenue": ":,.0f"},
        labels={"revenue": "Revenue (฿)", "salesperson": "Sales Person"},
    )
    fig_sales.update_layout(
        template=PLOTLY_TEMPLATE, height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
    )
    fig_sales.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_sales.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_sales, use_container_width=True)

# ──────────────────────────────────────────────
# AI Mode – Executive Summary
# ──────────────────────────────────────────────
if ai_mode:
    st.divider()
    st.markdown("### 🤖 AI-Generated Executive Summary")

    try:
        import google.generativeai as genai

        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            st.warning("🔑 Add `GOOGLE_API_KEY` to `.streamlit/secrets.toml` to enable AI insights.")
        else:
            genai.configure(api_key=api_key)

            # Prepare context data
            summary_data = {
                "total_shipments": int(kpi['total_shipments'].iloc[0]),
                "total_revenue": float(kpi['total_revenue'].iloc[0]),
                "avg_revenue": float(kpi['avg_revenue'].iloc[0]),
                "unique_customers": int(kpi['unique_customers'].iloc[0]),
                "status_breakdown": status[["status", "cnt"]].to_dict("records"),
                "direction_split": direction[["direction", "revenue"]].to_dict("records"),
                "top_industries": industry[["industry", "revenue"]].head(3).to_dict("records"),
                "monthly_trend_first": {"month": str(trend["month"].iloc[0]), "revenue": float(trend["revenue"].iloc[0])},
                "monthly_trend_last": {"month": str(trend["month"].iloc[-1]), "revenue": float(trend["revenue"].iloc[-1])},
            }

            prompt = f"""You are a senior logistics business analyst. Based on the following shipment analytics data, 
write a concise executive summary (3-4 paragraphs) highlighting key findings, trends, and actionable recommendations.
Be specific with numbers and percentages. Use professional business language.

Data Summary:
{summary_data}

Focus on: overall performance, growth trends, operational status health, directional trade balance, and industry concentration."""

            with st.spinner("🧠 Generating executive summary…"):
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except ImportError:
        st.info("Install `google-generativeai` to enable AI features.")
    except Exception as e:
        st.error(f"AI generation failed: {e}")
