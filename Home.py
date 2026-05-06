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
# Custom CSS – Deep Horizon Design System v2.0
# ──────────────────────────────────────────────
DEEP_HORIZON_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root Design Tokens ── */
:root {
    /* Backgrounds */
    --bg-abyss: #060B14;
    --bg-navy: #080F1A;
    --bg-midnight: #0D1B2A;
    --bg-steel: #1B2838;
    --bg-slate: #243447;
    --bg-surface: #2A3F55;
    --bg-card: rgba(13, 27, 42, 0.7);
    --bg-glass: rgba(255, 255, 255, 0.04);

    /* Accents */
    --accent-seafoam: #00D4AA;
    --accent-cyan: #00B4D8;
    --accent-amber: #FFB703;
    --accent-coral: #E63946;
    --accent-violet: #8338EC;
    --accent-tangerine: #FF6D00;
    --accent-emerald: #06D6A0;
    --accent-azure: #118AB2;

    /* Text */
    --text-primary: #F0F2F6;
    --text-secondary: #8B95A5;
    --text-tertiary: #5A6577;
    --text-muted: #3D4A5C;

    /* Borders */
    --border-subtle: rgba(255, 255, 255, 0.06);
    --border-hover: rgba(255, 255, 255, 0.12);
    --border-accent: rgba(0, 212, 170, 0.25);
}

/* ── Base Typography ── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Streamlit App Background ── */
.stApp {
    background: linear-gradient(180deg, var(--bg-abyss) 0%, var(--bg-midnight) 100%) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-navy) 0%, var(--bg-midnight) 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: var(--text-secondary);
}

/* ── Metric Cards ── */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 20px 24px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-seafoam), var(--accent-cyan));
    opacity: 0.8;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0, 212, 170, 0.12);
    border-color: var(--border-accent);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.02em;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] > div {
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}

/* ── Column metric accent variants ── */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"]::before { background: var(--accent-seafoam); }
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"]::before { background: var(--accent-cyan); }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"]::before { background: var(--accent-amber); }
div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"]::before { background: var(--accent-violet); }
div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stMetric"]::before { background: var(--accent-coral); }

/* ── Tab Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: var(--bg-glass);
    border-radius: 12px;
    padding: 4px 6px;
    border: 1px solid var(--border-subtle);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255, 255, 255, 0.04);
}
.stTabs [aria-selected="true"] {
    background: rgba(0, 212, 170, 0.1) !important;
    color: var(--accent-seafoam) !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border-subtle) !important;
    margin: 1.5rem 0 !important;
}

/* ── Plotly chart containers ── */
div[data-testid="stPlotlyChart"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
    padding: 8px;
    transition: border-color 0.3s ease;
}
div[data-testid="stPlotlyChart"]:hover {
    border-color: var(--border-hover);
}

/* ── Dataframe containers ── */
div[data-testid="stDataFrame"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
}

/* ── Hero Banner ── */
.hero-banner {
    background: linear-gradient(135deg, #060B14 0%, #0D1B2A 30%, #1B2838 60%, #0D1B2A 100%);
    background-size: 200% 200%;
    animation: gradientShift 8s ease infinite;
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 52px 44px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(0, 212, 170, 0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30%; left: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0, 180, 216, 0.04) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
}
.hero-badge .logo-mark {
    width: 36px; height: 36px;
    background: rgba(0, 212, 170, 0.15);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.hero-badge .label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: rgba(0, 212, 170, 0.7);
}
.hero-banner h1 {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00D4AA, #00B4D8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
    line-height: 1.1;
    letter-spacing: -0.025em;
}
.hero-banner p {
    color: var(--text-secondary);
    font-size: 1.05rem;
    line-height: 1.7;
    max-width: 700px;
}
.hero-banner strong {
    color: var(--text-primary);
    -webkit-text-fill-color: var(--text-primary);
}

/* ── Feature Cards ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 28px;
}
.feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 28px 24px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
}
.feature-card:hover {
    transform: translateY(-4px);
    border-color: var(--border-accent);
    box-shadow: 0 8px 24px rgba(0, 212, 170, 0.10);
}
.feature-card .icon-box {
    width: 48px; height: 48px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    margin-bottom: 16px;
}
.feature-card .icon-box.teal { background: rgba(0, 212, 170, 0.10); }
.feature-card .icon-box.amber { background: rgba(255, 183, 3, 0.10); }
.feature-card .icon-box.cyan { background: rgba(0, 180, 216, 0.10); }
.feature-card .icon-box.violet { background: rgba(131, 56, 236, 0.10); }
.feature-card .icon-box.coral { background: rgba(230, 57, 70, 0.10); }
.feature-card h3 {
    color: var(--text-primary);
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.feature-card p {
    color: var(--text-tertiary);
    font-size: 0.82rem;
    line-height: 1.55;
}

/* ── Status Badge ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.76rem;
    font-weight: 600;
}
.status-ai-on {
    background: rgba(0, 212, 170, 0.15);
    color: #00D4AA;
    border: 1px solid rgba(0, 212, 170, 0.3);
}
.status-ai-off {
    background: rgba(139, 149, 165, 0.15);
    color: #8B95A5;
    border: 1px solid rgba(139, 149, 165, 0.2);
}

/* ── Insight Box ── */
.insight-box {
    background: var(--bg-card);
    border-left: 3px solid var(--accent-seafoam);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    color: var(--text-secondary);
    font-size: 0.88rem;
    line-height: 1.6;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 212, 170, 0.2) !important;
}

/* ── Selectbox & Inputs ── */
div[data-baseweb="select"] {
    border-radius: 10px !important;
}

/* ── Expander ── */
details[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
}

/* ── Animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseDot {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
}
</style>
"""
st.markdown(DEEP_HORIZON_CSS, unsafe_allow_html=True)

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
    <div class="hero-badge">
        <div class="logo-mark">⬡</div>
        <span class="label">ShipInsight Analytics</span>
    </div>
    <h1>Navigate Your<br/>Logistics Data</h1>
    <p>
        A comprehensive analytics platform for international shipment operations.
        Explore executive KPIs, financial performance, logistics efficiency,
        regional trade flows, and AI-powered forecasting — all from <strong>100,000+</strong>
        shipment records.
    </p>
</div>
""", unsafe_allow_html=True)

# Feature cards
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="icon-box teal">📊</div>
        <h3>Executive Overview</h3>
        <p>High-level KPIs, revenue trends, and shipment status at a glance.</p>
    </div>
    <div class="feature-card">
        <div class="icon-box amber">💰</div>
        <h3>Financial Performance</h3>
        <p>Pricing analysis, promotion effectiveness, and margin tracking.</p>
    </div>
    <div class="feature-card">
        <div class="icon-box cyan">📦</div>
        <h3>Logistics & Weight</h3>
        <p>Weight optimization, package dimensions, and cargo efficiency.</p>
    </div>
    <div class="feature-card">
        <div class="icon-box violet">🌍</div>
        <h3>Regional Routes</h3>
        <p>Trade flow mapping, route analysis, and geographic insights.</p>
    </div>
    <div class="feature-card">
        <div class="icon-box coral">🤖</div>
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

