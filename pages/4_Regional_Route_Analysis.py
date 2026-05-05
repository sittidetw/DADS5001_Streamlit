import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Regional Routes – ShipInsight", page_icon="🌍", layout="wide")

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
    background: var(--bg-card); border-left: 3px solid #8338EC;
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
st.markdown("## 🌍 Regional & Route Analysis")
st.caption("Map global trade flows, identify high-value routes, and compare regional performance.")
st.divider()

# ──────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────
route_kpi = qr("""
    SELECT
        COUNT(DISTINCT "Country of Origin") AS origin_countries,
        COUNT(DISTINCT "Country of Destination") AS dest_countries,
        COUNT(DISTINCT "Region of Origin") AS origin_regions,
        COUNT(DISTINCT "Region of Destination") AS dest_regions,
        COUNT(DISTINCT "Country of Origin" || '->' || "Country of Destination") AS unique_routes
    FROM filtered
""")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Origin Countries", f"{route_kpi['origin_countries'].iloc[0]:,}")
with c2:
    st.metric("Destination Countries", f"{route_kpi['dest_countries'].iloc[0]:,}")
with c3:
    st.metric("Origin Regions", f"{route_kpi['origin_regions'].iloc[0]:,}")
with c4:
    st.metric("Destination Regions", f"{route_kpi['dest_regions'].iloc[0]:,}")
with c5:
    st.metric("Unique Trade Routes", f"{route_kpi['unique_routes'].iloc[0]:,}")

st.divider()

# ──────────────────────────────────────────────
# Sankey Diagram — Region Flows
# ──────────────────────────────────────────────
st.markdown("### 🔀 Trade Flow: Region of Origin → Region of Destination")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> The Sankey diagram reveals the volume and direction of trade between regions. Thick flows indicate dominant trade corridors, while thin flows may represent emerging or underserved markets.</div>', unsafe_allow_html=True)

sankey_data = qr("""
    SELECT
        "Region of Origin" AS source,
        "Region of Destination" AS target,
        COUNT(*) AS shipments,
        SUM("Revenue") AS revenue
    FROM filtered
    GROUP BY source, target
    ORDER BY shipments DESC
""")

# Build Sankey node list
all_nodes = list(pd.concat([sankey_data["source"], sankey_data["target"]]).unique())
# Prefix to separate source/target labels
source_nodes = [f"{n} (Origin)" for n in sankey_data["source"]]
target_nodes = [f"{n} (Dest)" for n in sankey_data["target"]]
node_labels = list(dict.fromkeys(source_nodes + target_nodes))  # ordered unique

source_idx = [node_labels.index(f"{s} (Origin)") for s in sankey_data["source"]]
target_idx = [node_labels.index(f"{t} (Dest)") for t in sankey_data["target"]]

node_colors = []
color_map = {
    "Asia": "#00D4AA", "Europe": "#00B4D8", "Americas": "#FFB703",
    "Middle East": "#E63946", "Oceania": "#8338EC", "Africa": "#FF6D00",
}
for label in node_labels:
    region = label.replace(" (Origin)", "").replace(" (Dest)", "")
    node_colors.append(color_map.get(region, "#8B95A5"))

link_colors = []
hex_to_rgba = {
    "#00D4AA": "rgba(0,212,170,0.25)", "#00B4D8": "rgba(0,180,216,0.25)",
    "#FFB703": "rgba(255,183,3,0.25)", "#E63946": "rgba(230,57,70,0.25)",
    "#8338EC": "rgba(131,56,236,0.25)", "#FF6D00": "rgba(255,109,0,0.25)",
    "#8B95A5": "rgba(139,149,165,0.25)",
}
for i in source_idx:
    link_colors.append(hex_to_rgba.get(node_colors[i], "rgba(139,149,165,0.25)"))

fig_sankey = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=20, thickness=20, line=dict(color="rgba(255,255,255,0.1)", width=0.5),
        label=node_labels, color=node_colors,
    ),
    link=dict(
        source=source_idx, target=target_idx,
        value=sankey_data["shipments"].tolist(),
        color=link_colors,
        hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>Shipments: %{value:,.0f}<extra></extra>",
    ),
))

fig_sankey.update_layout(
    template=PLOTLY_TEMPLATE, height=480,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F0F2F6", size=11),
)

st.plotly_chart(fig_sankey, use_container_width=True)

# ──────────────────────────────────────────────
# Top Trade Routes (Country Level)
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🏆 Top 15 Trade Routes by Revenue")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Focus on the highest-revenue trade corridors. Routes at the top are strategic priorities; any disruption to these corridors would significantly impact overall business performance.</div>', unsafe_allow_html=True)

top_routes = qr("""
    SELECT
        "Country of Origin" || ' → ' || "Country of Destination" AS route,
        "Inbound/Outbound" AS direction,
        COUNT(*) AS shipments,
        SUM("Revenue") AS revenue,
        AVG("Revenue") AS avg_revenue
    FROM filtered
    GROUP BY route, direction
    ORDER BY revenue DESC
    LIMIT 15
""")

dir_colors = {"Outbound": "#00D4AA", "Inbound": "#00B4D8"}

fig_routes = px.bar(
    top_routes, x="revenue", y="route", orientation="h",
    color="direction", color_discrete_map=dir_colors,
    hover_data={"shipments": ":,.0f", "avg_revenue": ":,.0f"},
    labels={"revenue": "Revenue (฿)", "route": "Trade Route", "direction": "Direction"},
)
fig_routes.update_layout(
    template=PLOTLY_TEMPLATE, height=500,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(autorange="reversed"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig_routes.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
fig_routes.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig_routes, use_container_width=True)

# ──────────────────────────────────────────────
# Inbound vs Outbound by Country
# ──────────────────────────────────────────────
st.divider()
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 Inbound vs. Outbound Volume by Country")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Compare export vs import volumes for each country. Large imbalances may indicate trade dependency or expansion opportunities in the underrepresented direction.</div>', unsafe_allow_html=True)

    country_dir = qr("""
        SELECT
            CASE
                WHEN "Inbound/Outbound" = 'Outbound' THEN "Country of Destination"
                ELSE "Country of Origin"
            END AS country,
            "Inbound/Outbound" AS direction,
            COUNT(*) AS shipments,
            SUM("Revenue") AS revenue
        FROM filtered
        GROUP BY country, direction
        ORDER BY revenue DESC
    """)

    # Get top 10 countries by total
    top_countries = country_dir.groupby("country")["revenue"].sum().nlargest(10).index.tolist()
    country_dir_top = country_dir[country_dir["country"].isin(top_countries)]

    fig_cd = px.bar(
        country_dir_top, x="country", y="shipments",
        color="direction", barmode="group",
        color_discrete_map={"Outbound": "#00D4AA", "Inbound": "#FFB703"},
        labels={"country": "Country", "shipments": "Shipments", "direction": "Direction"},
    )
    fig_cd.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_cd.update_xaxes(gridcolor="rgba(255,255,255,0.05)", tickangle=45)
    fig_cd.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_cd, use_container_width=True)

with col_right:
    st.markdown("### 🌐 Revenue by Destination Region")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Understand regional revenue concentration. Over-reliance on a single region creates vulnerability; diversifying trade partners strengthens resilience.</div>', unsafe_allow_html=True)

    region_rev = qr("""
        SELECT
            "Region of Destination" AS region,
            SUM("Revenue") AS revenue,
            COUNT(*) AS shipments,
            AVG("Revenue") AS avg_revenue
        FROM filtered
        GROUP BY region ORDER BY revenue DESC
    """)

    fig_region = px.bar(
        region_rev, x="region", y="revenue",
        color="region",
        color_discrete_sequence=["#00D4AA", "#00B4D8", "#FFB703", "#E63946", "#8338EC", "#FF6D00"],
        hover_data={"shipments": ":,.0f", "avg_revenue": ":,.0f"},
        labels={"region": "Region", "revenue": "Revenue (฿)"},
    )
    fig_region.update_layout(
        template=PLOTLY_TEMPLATE, height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig_region.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig_region.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    st.plotly_chart(fig_region, use_container_width=True)

# ──────────────────────────────────────────────
# Geographic Heatmap
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🗺️ Geographic Heatmap — Revenue by Destination Country")
st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> The choropleth map provides a geographic view of revenue distribution. Darker shades indicate higher revenue concentration, helping identify key markets and white-space opportunities.</div>', unsafe_allow_html=True)

# Country name to ISO-3 mapping for choropleth
country_iso = {
    "Thailand": "THA", "Singapore": "SGP", "China": "CHN", "Japan": "JPN",
    "USA": "USA", "UK": "GBR", "Germany": "DEU", "Australia": "AUS",
    "UAE": "ARE", "India": "IND", "Vietnam": "VNM", "South Korea": "KOR",
    "Malaysia": "MYS", "Indonesia": "IDN", "France": "FRA", "Canada": "CAN",
    "Italy": "ITA", "Spain": "ESP", "Netherlands": "NLD", "Brazil": "BRA",
    "Mexico": "MEX", "Saudi Arabia": "SAU", "Philippines": "PHL",
    "Taiwan": "TWN", "Hong Kong": "HKG", "New Zealand": "NZL",
    "Switzerland": "CHE", "Sweden": "SWE", "Norway": "NOR", "Denmark": "DNK",
    "Belgium": "BEL", "Austria": "AUT", "Poland": "POL", "Turkey": "TUR",
    "Russia": "RUS", "South Africa": "ZAF", "Egypt": "EGY", "Nigeria": "NGA",
    "Kenya": "KEN", "Argentina": "ARG", "Chile": "CHL", "Colombia": "COL",
    "Peru": "PER", "Pakistan": "PAK", "Bangladesh": "BGD", "Myanmar": "MMR",
    "Cambodia": "KHM", "Laos": "LAO",
}

geo_data = qr("""
    SELECT
        "Country of Destination" AS country,
        COUNT(*) AS shipments,
        SUM("Revenue") AS revenue
    FROM filtered
    GROUP BY country
""")
geo_data["iso_alpha"] = geo_data["country"].map(country_iso)
geo_data = geo_data.dropna(subset=["iso_alpha"])

if len(geo_data) > 0:
    fig_map = px.choropleth(
        geo_data, locations="iso_alpha", color="revenue",
        hover_name="country",
        color_continuous_scale=["#0A192F", "#0E4D64", "#00B4D8", "#00D4AA", "#FFB703"],
        hover_data={"shipments": ":,.0f", "revenue": ":,.0f", "iso_alpha": False},
        labels={"revenue": "Revenue (฿)"},
    )
    fig_map.update_layout(
        template=PLOTLY_TEMPLATE, height=480,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            lakecolor="rgba(0,0,0,0)",
            landcolor="#1B2838",
            showframe=False,
            coastlinecolor="rgba(255,255,255,0.1)",
            countrycolor="rgba(255,255,255,0.08)",
        ),
        coloraxis_colorbar=dict(title="Revenue (฿)", thickness=15),
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No geographic data available for the selected period.")

# ──────────────────────────────────────────────
# AI Mode
# ──────────────────────────────────────────────
if ai_mode:
    st.divider()
    st.markdown("### 🤖 AI Route Optimization Analysis")

    try:
        import google.generativeai as genai

        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            st.warning("🔑 Add `GOOGLE_API_KEY` to `.streamlit/secrets.toml` to enable AI insights.")
        else:
            genai.configure(api_key=api_key)

            context = {
                "top_routes": top_routes[["route", "direction", "shipments", "revenue"]].head(10).to_dict("records"),
                "region_flow": sankey_data[["source", "target", "shipments", "revenue"]].head(10).to_dict("records"),
                "region_revenue": region_rev[["region", "revenue", "shipments"]].to_dict("records"),
            }

            prompt = f"""You are a supply chain strategist for an international logistics company.
Analyze the following regional trade route data and provide:
1. Assessment of trade route concentration risks
2. Identification of underperforming or underserved routes
3. Regional diversification recommendations
4. 3 specific route optimization strategies with expected impact

Data:
{context}

Be specific with numbers and route names. Write in professional business language."""

            with st.spinner("🧠 Analyzing trade routes…"):
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except ImportError:
        st.info("Install `google-generativeai` to enable AI features.")
    except Exception as e:
        st.error(f"AI generation failed: {e}")
