"""
ShipInsight Design System v2.0 — Deep Horizon Theme
Shared CSS and Plotly configuration for all pages.
"""

# ──────────────────────────────────────────────
# Page CSS — inject via st.markdown(PAGE_CSS, unsafe_allow_html=True)
# ──────────────────────────────────────────────
PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-abyss: #060B14;
    --bg-navy: #080F1A;
    --bg-midnight: #0D1B2A;
    --bg-steel: #1B2838;
    --bg-slate: #243447;
    --bg-surface: #2A3F55;
    --bg-card: rgba(13, 27, 42, 0.7);
    --bg-glass: rgba(255, 255, 255, 0.04);
    --accent-seafoam: #00D4AA;
    --accent-cyan: #00B4D8;
    --accent-amber: #FFB703;
    --accent-coral: #E63946;
    --accent-violet: #8338EC;
    --accent-tangerine: #FF6D00;
    --accent-emerald: #06D6A0;
    --accent-azure: #118AB2;
    --text-primary: #F0F2F6;
    --text-secondary: #8B95A5;
    --text-tertiary: #5A6577;
    --text-muted: #3D4A5C;
    --border-subtle: rgba(255, 255, 255, 0.06);
    --border-hover: rgba(255, 255, 255, 0.12);
    --border-accent: rgba(0, 212, 170, 0.25);
}

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

.stApp { background: linear-gradient(180deg, var(--bg-abyss) 0%, var(--bg-midnight) 100%) !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-navy) 0%, var(--bg-midnight) 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

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

div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"]::before { background: var(--accent-seafoam); }
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"]::before { background: var(--accent-cyan); }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"]::before { background: var(--accent-amber); }
div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"]::before { background: var(--accent-violet); }
div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stMetric"]::before { background: var(--accent-coral); }

.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background: var(--bg-glass);
    border-radius: 12px; padding: 4px 6px;
    border: 1px solid var(--border-subtle);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; padding: 10px 18px;
    font-weight: 500; font-size: 0.9rem;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.04); }
.stTabs [aria-selected="true"] {
    background: rgba(0, 212, 170, 0.1) !important;
    color: var(--accent-seafoam) !important;
}

hr { border-color: var(--border-subtle) !important; margin: 1.5rem 0 !important; }

div[data-testid="stPlotlyChart"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
    padding: 8px;
    transition: border-color 0.3s ease;
}
div[data-testid="stPlotlyChart"]:hover { border-color: var(--border-hover); }

div[data-testid="stDataFrame"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
}

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
.insight-box.amber { border-left-color: var(--accent-amber); }
.insight-box.cyan { border-left-color: var(--accent-cyan); }
.insight-box.violet { border-left-color: var(--accent-violet); }
.insight-box.coral { border-left-color: var(--accent-coral); }

.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 212, 170, 0.2) !important;
}

details[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
}
</style>
"""

# ──────────────────────────────────────────────
# Plotly Chart Configuration
# ──────────────────────────────────────────────
PLOTLY_TEMPLATE = "plotly_dark"

COLOR_SEQ = [
    "#00D4AA", "#00B4D8", "#FFB703", "#E63946",
    "#8338EC", "#FF6D00", "#06D6A0", "#118AB2",
]

CHART_LAYOUT = dict(
    template=PLOTLY_TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color="#8B95A5", size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        xanchor="right", x=1,
        font=dict(size=11, color="#8B95A5"),
        bgcolor="rgba(0,0,0,0)",
    ),
    hoverlabel=dict(
        bgcolor="#1B2838",
        bordercolor="rgba(255,255,255,0.1)",
        font=dict(family="Inter", size=13, color="#F0F2F6"),
    ),
)

GRID_COLOR = "rgba(255,255,255,0.04)"
AXIS_LINE_COLOR = "rgba(255,255,255,0.06)"


def render_sidebar_filters() -> "pd.DataFrame | None":
    """
    Render the global filter sidebar on any page.

    Requires ``st.session_state["df"]`` to be populated (i.e. Home.py ran first).
    If the raw dataframe is missing the function shows a warning and returns None.

    Returns the currently filtered DataFrame and also writes it back to
    ``st.session_state["filtered_df"]`` so existing page code continues to work.
    """
    import streamlit as st
    import pandas as pd

    # ── Guard: need raw df ────────────────────────────────────────
    if "df" not in st.session_state:
        with st.sidebar:
            st.warning("⚠️ Please visit the **Home** page first to load data.")
        return None

    df = st.session_state["df"]

    # ── Pre-fill from MongoDB on first call in this browser session ─────
    if "_prefs_loaded" not in st.session_state:
        try:
            from db import get_latest_today_preferences
            _saved = get_latest_today_preferences()
            if _saved:
                try:
                    st.session_state["date_start"] = pd.Timestamp(_saved["date_start"])
                    st.session_state["date_end"]   = pd.Timestamp(_saved["date_end"])
                except Exception:
                    pass
                st.session_state["selected_industries"] = _saved.get("industries", [])
                st.session_state["selected_countries"]  = _saved.get("countries",  [])
        except Exception:
            pass
        st.session_state["_prefs_loaded"] = True

    with st.sidebar:
        st.markdown("### 🚢 ShipInsight")
        st.caption("International Shipment Analytics")

        # Try to show data-source badge (optional — db may not be imported)
        try:
            from db import render_data_source_badge
            render_data_source_badge()
        except Exception:
            pass

        st.divider()

        # ── AI Mode Toggle ─────────────────────────────────────────
        ai_mode = st.toggle(
            "🤖 AI Mode",
            value=st.session_state.get("ai_mode", False),
            key="ai_toggle_page",
        )
        st.session_state["ai_mode"] = ai_mode

        if ai_mode:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:6px;'
                'padding:4px 12px;border-radius:9999px;font-size:0.76rem;font-weight:600;'
                'background:rgba(0,212,170,0.15);color:#00D4AA;'
                'border:1px solid rgba(0,212,170,0.3);">● AI Active</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:6px;'
                'padding:4px 12px;border-radius:9999px;font-size:0.76rem;font-weight:600;'
                'background:rgba(139,149,165,0.15);color:#8B95A5;'
                'border:1px solid rgba(139,149,165,0.2);">● Traditional BI</span>',
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Resolve full date bounds once ─────────────────────────
        min_date = df["Order Date"].min().date()
        max_date = df["Order Date"].max().date()

        if "filter_reset_counter" not in st.session_state:
            st.session_state["filter_reset_counter"] = 0

        # ── Flag pattern: increment counter to force fresh widgets ─────
        if st.session_state.pop("_clear_filters_page", False):
            st.session_state["filter_reset_counter"] += 1
            st.session_state.pop("date_start", None)
            st.session_state.pop("date_end", None)
            st.session_state.pop("selected_industries", None)
            st.session_state.pop("selected_countries", None)

        # ── Date Range ─────────────────────────────────────────────
        st.markdown("**📅 Date Range Filter**")

        # Restore previous selection if available
        prev_start = st.session_state.get("date_start", pd.Timestamp(min_date)).date()
        prev_end   = st.session_state.get("date_end",   pd.Timestamp(max_date)).date()
        prev_start = max(min_date, min(prev_start, max_date))
        prev_end   = max(min_date, min(prev_end,   max_date))

        date_range = st.date_input(
            "Select period",
            value=(prev_start, prev_end),
            min_value=min_date,
            max_value=max_date,
            key=f"sidebar_date_range_{st.session_state['filter_reset_counter']}",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            st.session_state["date_start"] = pd.Timestamp(date_range[0])
            st.session_state["date_end"]   = pd.Timestamp(date_range[1])
        else:
            st.session_state["date_start"] = pd.Timestamp(min_date)
            st.session_state["date_end"]   = pd.Timestamp(max_date)

        st.divider()

        # ── Industry Filter ────────────────────────────────────────
        st.markdown("**🏭 Industry Filter**")
        industry_options = sorted(df["Industry"].dropna().unique().tolist())
        prev_industries  = st.session_state.get("selected_industries", [])

        selected_industries = st.multiselect(
            "Select industries",
            options=industry_options,
            default=[i for i in prev_industries if i in industry_options],
            placeholder="All industries",
            key=f"sidebar_industries_{st.session_state['filter_reset_counter']}",
        )

        # ── Country Filter ─────────────────────────────────────────
        st.markdown("**🌍 Country of Destination**")
        country_options  = sorted(df["Country of Destination"].dropna().unique().tolist())
        prev_countries   = st.session_state.get("selected_countries", [])

        selected_countries = st.multiselect(
            "Select countries",
            options=country_options,
            default=[c for c in prev_countries if c in country_options],
            placeholder="All countries",
            key=f"sidebar_countries_{st.session_state['filter_reset_counter']}",
        )

        st.divider()

        # ── Clear All Filters button (always visible) ──────────────
        # Only sets a flag + reruns — does NOT touch widget keys here
        # (that would throw StreamlitAPIException after instantiation).
        if st.button("🗑️ Clear All Filters", use_container_width=True, key="clear_filters_btn"):
            st.session_state["_clear_filters_page"] = True
            st.rerun()

        # ── Apply filters ──────────────────────────────────────────
        filtered = df[
            (df["Order Date"] >= st.session_state["date_start"])
            & (df["Order Date"] <= st.session_state["date_end"])
        ]
        if selected_industries:
            filtered = filtered[filtered["Industry"].isin(selected_industries)]
        if selected_countries:
            filtered = filtered[filtered["Country of Destination"].isin(selected_countries)]

        # Persist back to session state
        st.session_state["filtered_df"]        = filtered
        st.session_state["selected_industries"] = selected_industries
        st.session_state["selected_countries"]  = selected_countries

        st.caption(f"📊 **{len(filtered):,}** shipments in selected range")
        st.caption(
            f"📅 {st.session_state['date_start'].strftime('%b %Y')} – "
            f"{st.session_state['date_end'].strftime('%b %Y')}"
        )

        # ── Save latest preferences to MongoDB ─────────────────────
        try:
            from db import save_user_preferences
            import streamlit.runtime.scriptrunner as _sr
            _sid = _sr.get_script_run_ctx().session_id
        except Exception:
            _sid = "default"
        try:
            save_user_preferences(_sid, {
                "date_start": str(st.session_state["date_start"].date()),
                "date_end":   str(st.session_state["date_end"].date()),
                "industries": selected_industries,
                "countries":  selected_countries,
            })
        except Exception:
            pass

    return filtered



def apply_chart_style(fig, height=400, hovermode="x unified"):
    """Apply the Deep Horizon chart styling to any Plotly figure."""
    fig.update_layout(
        **CHART_LAYOUT,
        height=height,
        hovermode=hovermode,
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, linecolor=AXIS_LINE_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, linecolor=AXIS_LINE_COLOR)
    return fig
