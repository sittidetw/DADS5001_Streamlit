import streamlit as st
import pandas as pd
import duckdb
from streamlit_gsheets import GSheetsConnection

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="ShipInsight – International Shipment Analytics",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS – Corporate Dark Theme
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root Variables ── */
:root {
    --accent-teal: #00D4AA;
    --accent-cyan: #00B4D8;
    --accent-amber: #FFB703;
    --accent-rose: #E63946;
    --bg-card: rgba(30, 33, 48, 0.85);
    --bg-glass: rgba(255,255,255,0.04);
    --text-primary: #F0F2F6;
    --text-secondary: #8B95A5;
    --border-subtle: rgba(255,255,255,0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}



/* ── Metric Cards ── */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 16px 20px;
    backdrop-filter: blur(12px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,212,170,0.12);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* ── Tab Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: var(--bg-glass);
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}

/* ── Divider ── */
hr {
    border-color: var(--border-subtle) !important;
    margin: 1.5rem 0 !important;
}

/* ── Plotly chart containers ── */
div[data-testid="stPlotlyChart"] {
    border-radius: 12px;
    overflow: hidden;
}

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0D1B2A 0%, #1B2838 50%, #0A192F 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 48px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00D4AA, #00B4D8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.hero-banner p {
    color: var(--text-secondary);
    font-size: 1.05rem;
    line-height: 1.6;
    max-width: 700px;
}

/* ── Feature Cards ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-top: 24px;
}
.feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 24px 20px;
    transition: transform 0.2s ease, border-color 0.3s ease;
}
.feature-card:hover {
    transform: translateY(-3px);
    border-color: rgba(0,212,170,0.3);
}
.feature-card .icon {
    font-size: 1.8rem;
    margin-bottom: 10px;
}
.feature-card h3 {
    color: var(--text-primary);
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.feature-card p {
    color: var(--text-secondary);
    font-size: 0.85rem;
    line-height: 1.5;
}

/* ── Status Badge ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.status-ai-on {
    background: rgba(0,212,170,0.15);
    color: #00D4AA;
    border: 1px solid rgba(0,212,170,0.3);
}
.status-ai-off {
    background: rgba(139,149,165,0.15);
    color: #8B95A5;
    border: 1px solid rgba(139,149,165,0.2);
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Data Loading
# ──────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner="📡 Loading shipment data…")
def load_data():
    """Load data from Google Sheets, falling back to local CSV."""
    df = None
    # Try Google Sheets first
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read()
        if df is not None and len(df) > 0:
            pass  # success
        else:
            df = None
    except Exception:
        df = None

    # Fallback to local CSV
    if df is None:
        try:
            df = pd.read_csv("International_Shipment_100k_V3.csv", encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv("International_Shipment_100k_V3.csv", encoding="latin-1")

    # Parse & clean
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["YearMonth"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Quarter"] = df["Order Date"].dt.to_period("Q").astype(str)

    # Ensure numeric columns
    num_cols = [
        "Actual Weight (kg)", "Width (cm)", "Length (cm)", "Height (cm)",
        "Volumetric Weight (kg)", "Chargeable Weight (kg)",
        "RRP (Gross Price)", "Back Margin (Promotion Expense)",
        "Billing Price (ASP)", "Fuel Surcharge (FSC)", "Revenue",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def run_query(query: str, df: pd.DataFrame) -> pd.DataFrame:
    """Execute a DuckDB SQL query against the dataframe."""
    return duckdb.query(query).to_df()


# ──────────────────────────────────────────────
# Load Data & Store in Session
# ──────────────────────────────────────────────
df = load_data()
st.session_state["df"] = df

# ──────────────────────────────────────────────
# Sidebar – Global Controls
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🚢 ShipInsight")
    st.caption("International Shipment Analytics")
    st.divider()

    # AI Mode Toggle
    ai_mode = st.toggle("🤖 AI Mode", value=st.session_state.get("ai_mode", False), key="ai_toggle")
    st.session_state["ai_mode"] = ai_mode

    if ai_mode:
        st.markdown('<span class="status-badge status-ai-on">● AI Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-ai-off">● Traditional BI</span>', unsafe_allow_html=True)

    st.divider()

    # Global Date Range Filter
    st.markdown("**📅 Date Range Filter**")
    min_date = df["Order Date"].min().date()
    max_date = df["Order Date"].max().date()
    date_range = st.date_input(
        "Select period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="global_date_range",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        st.session_state["date_start"] = pd.Timestamp(date_range[0])
        st.session_state["date_end"] = pd.Timestamp(date_range[1])
    else:
        st.session_state["date_start"] = pd.Timestamp(min_date)
        st.session_state["date_end"] = pd.Timestamp(max_date)

    st.divider()

    # Data Summary
    filtered = df[
        (df["Order Date"] >= st.session_state["date_start"])
        & (df["Order Date"] <= st.session_state["date_end"])
    ]
    st.session_state["filtered_df"] = filtered
    st.caption(f"📊 **{len(filtered):,}** shipments in selected range")
    st.caption(f"📅 {st.session_state['date_start'].strftime('%b %Y')} – {st.session_state['date_end'].strftime('%b %Y')}")

# ──────────────────────────────────────────────
# Landing Page
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>ShipInsight Analytics</h1>
    <p>
        A comprehensive analytics platform for international shipment operations.
        Explore executive KPIs, financial performance, logistics efficiency,
        regional trade flows, and AI-powered forecasting — all from 100,000+
        shipment records.
    </p>
</div>
""", unsafe_allow_html=True)

# Feature cards
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="icon">📊</div>
        <h3>Executive Overview</h3>
        <p>High-level KPIs, revenue trends, and shipment status at a glance.</p>
    </div>
    <div class="feature-card">
        <div class="icon">💰</div>
        <h3>Financial Performance</h3>
        <p>Pricing analysis, promotion effectiveness, and margin tracking.</p>
    </div>
    <div class="feature-card">
        <div class="icon">📦</div>
        <h3>Logistics & Weight</h3>
        <p>Weight optimization, package dimensions, and cargo efficiency.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🌍</div>
        <h3>Regional Routes</h3>
        <p>Trade flow mapping, route analysis, and geographic insights.</p>
    </div>
    <div class="feature-card">
        <div class="icon">🤖</div>
        <h3>AI Insights</h3>
        <p>Predictive forecasting, anomaly detection, and smart queries.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.markdown("")

# Quick stats row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Shipments", f"{len(filtered):,}")
with c2:
    total_rev = filtered["Revenue"].sum()
    st.metric("Total Revenue", f"฿{total_rev:,.0f}")
with c3:
    avg_rev = filtered["Revenue"].mean()
    st.metric("Avg Revenue / Shipment", f"฿{avg_rev:,.0f}")
with c4:
    n_customers = filtered["Customer ID"].nunique()
    st.metric("Active Customers", f"{n_customers:,}")

st.divider()
st.caption("👈 Use the sidebar to navigate between pages and toggle AI mode.")
