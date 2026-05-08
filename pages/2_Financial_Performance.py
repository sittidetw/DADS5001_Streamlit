import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from theme import PAGE_CSS, PLOTLY_TEMPLATE, COLOR_SEQ, CHART_LAYOUT, GRID_COLOR, apply_chart_style

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Financial Performance – ShipInsight", page_icon="💰", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Data
# ──────────────────────────────────────────────
if "filtered_df" not in st.session_state:
    st.warning("⚠️ Please navigate to the **Home** page first to load data.")
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]
ai_mode = st.session_state.get("ai_mode", False)


def qr(query: str) -> pd.DataFrame:
    return duckdb.query(query).to_df()


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown("## 💰 Financial Performance")
st.caption("Deep dive into revenue streams, pricing mechanics, promotion impact, and margin health.")
st.divider()

# ──────────────────────────────────────────────
# Financial KPIs
# ──────────────────────────────────────────────
fin_kpi = qr("""
    SELECT
        SUM("RRP (Gross Price)") AS total_rrp,
        SUM("Billing Price (ASP)") AS total_asp,
        SUM("Back Margin (Promotion Expense)") AS total_discount,
        SUM("Fuel Surcharge (FSC)") AS total_fsc,
        SUM("Revenue") AS total_revenue,
        AVG("RRP (Gross Price)") AS avg_rrp,
        AVG("Billing Price (ASP)") AS avg_asp
    FROM filtered
""")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Gross Revenue (RRP)", f"฿{fin_kpi['total_rrp'].iloc[0]:,.0f}")
with c2:
    st.metric("Net Billing (ASP)", f"฿{fin_kpi['total_asp'].iloc[0]:,.0f}")
with c3:
    discount_rate = fin_kpi['total_discount'].iloc[0] / fin_kpi['total_rrp'].iloc[0] * 100
    st.metric("Total Discounts", f"฿{fin_kpi['total_discount'].iloc[0]:,.0f}", delta=f"-{discount_rate:.1f}%")
with c4:
    st.metric("Fuel Surcharges", f"฿{fin_kpi['total_fsc'].iloc[0]:,.0f}")
with c5:
    net_margin = (fin_kpi['total_asp'].iloc[0] / fin_kpi['total_rrp'].iloc[0]) * 100
    st.metric("Net-to-Gross Ratio", f"{net_margin:.1f}%")

st.divider()

# ──────────────────────────────────────────────
# RRP vs ASP by Month (Discounting Impact)
# ──────────────────────────────────────────────
st.markdown("### 📉 Gross Price (RRP) vs. Billing Price (ASP) Over Time")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> The gap between RRP and ASP reveals discounting intensity. A widening gap indicates increasing price erosion, which may boost volume but threatens profitability.</div>', unsafe_allow_html=True)

pricing_trend = qr("""
    SELECT
        DATE_TRUNC('month', "Order Date") AS month,
        AVG("RRP (Gross Price)") AS avg_rrp,
        AVG("Billing Price (ASP)") AS avg_asp,
        AVG("Back Margin (Promotion Expense)") AS avg_discount,
        (AVG("Billing Price (ASP)") / NULLIF(AVG("RRP (Gross Price)"), 0)) * 100 AS realization_pct
    FROM filtered
    GROUP BY 1 ORDER BY 1
""")
pricing_trend["month"] = pd.to_datetime(pricing_trend["month"])

fig_pricing = make_subplots(specs=[[{"secondary_y": True}]])

fig_pricing.add_trace(
    go.Scatter(
        x=pricing_trend["month"], y=pricing_trend["avg_rrp"],
        name="Avg RRP (Gross)", mode="lines+markers",
        line=dict(color="#FFB703", width=2.5), marker=dict(size=5),
        hovertemplate="RRP: ฿%{y:,.0f}<extra></extra>"
    ), secondary_y=False
)
fig_pricing.add_trace(
    go.Scatter(
        x=pricing_trend["month"], y=pricing_trend["avg_asp"],
        name="Avg ASP (Billing)", mode="lines+markers",
        line=dict(color="#00D4AA", width=2.5), marker=dict(size=5),
        hovertemplate="ASP: ฿%{y:,.0f}<extra></extra>"
    ), secondary_y=False
)
fig_pricing.add_trace(
    go.Bar(
        x=pricing_trend["month"], y=pricing_trend["avg_discount"],
        name="Avg Discount", marker_color="rgba(230,57,70,0.4)",
        hovertemplate="Discount: ฿%{y:,.0f}<extra></extra>"
    ), secondary_y=True
)

fig_pricing.update_layout(
    template=PLOTLY_TEMPLATE, height=420,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
fig_pricing.update_yaxes(title_text="Average Price (฿)", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
fig_pricing.update_yaxes(title_text="Average Discount (฿)", secondary_y=True, gridcolor="rgba(255,255,255,0.05)")
fig_pricing.update_xaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_pricing, use_container_width=True)

# ──────────────────────────────────────────────
# Promotion Effectiveness
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🎯 Promotion Effectiveness Analysis")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Compare how each promotion type affects revenue, discount depth, and overall margin. Efficient promotions maximize revenue lift per discount dollar spent.</div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    promo = qr("""
        SELECT
            "Promotion Type" AS promo_type,
            COUNT(*) AS shipments,
            SUM("Revenue") AS revenue,
            AVG("Back Margin (Promotion Expense)") AS avg_discount,
            AVG("Revenue") AS avg_revenue,
            SUM("RRP (Gross Price)") AS gross,
            SUM("Billing Price (ASP)") AS net
        FROM filtered
        GROUP BY promo_type ORDER BY revenue DESC
    """)

    fig_promo = px.bar(
        promo, x="promo_type", y="revenue",
        color="promo_type",
        color_discrete_sequence=["#00D4AA", "#00B4D8", "#FFB703", "#E63946", "#8338EC"],
        hover_data={"shipments": ":,.0f", "avg_discount": ":,.0f", "avg_revenue": ":,.0f"},
        labels={"promo_type": "Promotion Type", "revenue": "Total Revenue (฿)"},
        title="Revenue by Promotion Type",
    )
    fig_promo.update_layout(
        template=PLOTLY_TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig_promo.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_promo.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_promo, use_container_width=True)

with col_right:
    # Promotion discount efficiency: Revenue per discount dollar
    promo_eff = promo.copy()
    promo_eff["efficiency"] = promo_eff["revenue"] / promo_eff["avg_discount"].replace(0, float('nan'))
    promo_eff = promo_eff.dropna(subset=["efficiency"])
    promo_eff = promo_eff[promo_eff["promo_type"] != "None"]

    if len(promo_eff) > 0:
        fig_eff = px.bar(
            promo_eff, x="promo_type", y="avg_discount",
            color="promo_type",
            color_discrete_sequence=["#E63946", "#FFB703", "#00B4D8", "#8338EC"],
            hover_data={"efficiency": ":,.0f", "revenue": ":,.0f"},
            labels={"promo_type": "Promotion Type", "avg_discount": "Avg Discount Cost (฿)"},
            title="Average Discount Cost per Promotion Type",
        )
        fig_eff.update_layout(
            template=PLOTLY_TEMPLATE, height=380,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        fig_eff.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_eff.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_eff, use_container_width=True)
    else:
        st.info("No active promotions found in the selected period.")

# ──────────────────────────────────────────────
# Revenue by Industry + Margin Analysis
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🏭 Industry Revenue & Margin Performance")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Identify which industries deliver the best net margin. High-revenue sectors with low margins may require pricing strategy adjustments.</div>', unsafe_allow_html=True)

industry = qr("""
    SELECT
        "Industry" AS industry,
        SUM("Revenue") AS revenue,
        SUM("RRP (Gross Price)") AS gross,
        SUM("Billing Price (ASP)") AS net,
        (SUM("Billing Price (ASP)") / NULLIF(SUM("RRP (Gross Price)"), 0)) * 100 AS margin_pct,
        COUNT(*) AS shipments
    FROM filtered
    GROUP BY industry ORDER BY revenue DESC
""")

fig_ind = make_subplots(specs=[[{"secondary_y": True}]])

fig_ind.add_trace(
    go.Bar(
        x=industry["industry"], y=industry["revenue"],
        name="Total Revenue", marker_color="#00B4D8",
        hovertemplate="%{x}<br>Revenue: ฿%{y:,.0f}<extra></extra>"
    ), secondary_y=False
)
fig_ind.add_trace(
    go.Scatter(
        x=industry["industry"], y=industry["margin_pct"],
        name="Net Margin %", mode="lines+markers",
        line=dict(color="#FFB703", width=2.5), marker=dict(size=8, symbol="diamond"),
        hovertemplate="%{x}<br>Margin: %{y:.1f}%<extra></extra>"
    ), secondary_y=True
)

fig_ind.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
fig_ind.update_yaxes(title_text="Revenue (฿)", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
fig_ind.update_yaxes(title_text="Net Margin %", secondary_y=True, gridcolor="rgba(255,255,255,0.05)")
fig_ind.update_xaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_ind, use_container_width=True)

# ──────────────────────────────────────────────
# Monthly Margin Trend (Area Chart)
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Monthly Net-to-Gross Margin Trend")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Track margin health over time. A downward trend in the net-to-gross ratio indicates growing discount pressure or cost inflation that needs to be addressed.</div>', unsafe_allow_html=True)

margin_trend = qr("""
    SELECT
        DATE_TRUNC('month', "Order Date") AS month,
        SUM("RRP (Gross Price)") AS gross,
        SUM("Billing Price (ASP)") AS net,
        SUM("Revenue") AS revenue,
        SUM("Back Margin (Promotion Expense)") AS discounts,
        (SUM("Billing Price (ASP)") / NULLIF(SUM("RRP (Gross Price)"), 0)) * 100 AS margin_pct
    FROM filtered
    GROUP BY 1 ORDER BY 1
""")
margin_trend["month"] = pd.to_datetime(margin_trend["month"])

fig_margin = go.Figure()

fig_margin.add_trace(go.Scatter(
    x=margin_trend["month"], y=margin_trend["gross"],
    name="Gross (RRP)", fill="tozeroy",
    fillcolor="rgba(255,183,3,0.15)", line=dict(color="#FFB703", width=2),
    hovertemplate="Gross: ฿%{y:,.0f}<extra></extra>"
))
fig_margin.add_trace(go.Scatter(
    x=margin_trend["month"], y=margin_trend["net"],
    name="Net (ASP)", fill="tozeroy",
    fillcolor="rgba(0,212,170,0.15)", line=dict(color="#00D4AA", width=2),
    hovertemplate="Net: ฿%{y:,.0f}<extra></extra>"
))
fig_margin.add_trace(go.Scatter(
    x=margin_trend["month"], y=margin_trend["discounts"],
    name="Discounts", fill="tozeroy",
    fillcolor="rgba(230,57,70,0.15)", line=dict(color="#E63946", width=2),
    hovertemplate="Discounts: ฿%{y:,.0f}<extra></extra>"
))

fig_margin.update_layout(
    template=PLOTLY_TEMPLATE, height=400,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis_title="Amount (฿)",
)
fig_margin.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
fig_margin.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_margin, use_container_width=True)

# ──────────────────────────────────────────────
# AI Mode – Financial Analysis
# ──────────────────────────────────────────────
if ai_mode:
    st.divider()
    st.markdown("### 🤖 AI Financial Analysis")

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
            
            ai_fin_kpi = duckdb.query('SELECT SUM("RRP (Gross Price)") AS total_rrp, SUM("Billing Price (ASP)") AS total_asp FROM ai_filtered').to_df()
            ai_promo = duckdb.query('SELECT "Promotion Type" AS promo_type, SUM("Revenue") AS revenue, AVG("Back Margin (Promotion Expense)") AS avg_discount FROM ai_filtered GROUP BY promo_type ORDER BY revenue DESC').to_df()
            ai_industry = duckdb.query('SELECT "Industry" AS industry, SUM("Revenue") AS revenue, (SUM("Billing Price (ASP)") / NULLIF(SUM("RRP (Gross Price)"), 0)) * 100 AS margin_pct FROM ai_filtered GROUP BY industry ORDER BY revenue DESC').to_df()
            
            total_rrp = float(ai_fin_kpi['total_rrp'].iloc[0]) if not ai_fin_kpi.empty and pd.notna(ai_fin_kpi['total_rrp'].iloc[0]) else 0.0
            total_asp = float(ai_fin_kpi['total_asp'].iloc[0]) if not ai_fin_kpi.empty and pd.notna(ai_fin_kpi['total_asp'].iloc[0]) else 0.0

            context = {
                "period": f"Last 3 months ({min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')})",
                "total_rrp": total_rrp,
                "total_asp": total_asp,
                "discount_rate": ((total_rrp - total_asp) / total_rrp * 100) if total_rrp > 0 else 0.0,
                "net_margin": (total_asp / total_rrp * 100) if total_rrp > 0 else 0.0,
                "promotion_breakdown": ai_promo[["promo_type", "revenue", "avg_discount"]].to_csv(index=False),
                "industry_margins": ai_industry[["industry", "revenue", "margin_pct"]].head(5).to_csv(index=False),
            }

            prompt = f"""Financial analyst. Briefly assess: pricing strategy, top/bottom promotion ROI, and give 2 recommendations.
Data: {context}"""

            with st.spinner("🧠 Generating financial analysis…"):
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b:free",
                    messages=[{"role": "user", "content": prompt}],
                )
                st.markdown(response.choices[0].message.content)

    except ImportError:
        st.info("Install `openai` to enable AI features.")
    except Exception as e:
        st.error(f"AI generation failed: {e}")
