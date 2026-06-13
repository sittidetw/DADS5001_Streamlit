import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

# Thailand Standard Time – ICT (GMT+7)
TZ_ICT = timezone(timedelta(hours=7))
from theme import PAGE_CSS, PLOTLY_TEMPLATE, COLOR_SEQ, CHART_LAYOUT, GRID_COLOR
from db import submit_insight, get_recent_insights, get_mongo_collection

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Actionable Insights – ShipInsight",
    page_icon="💬",
    layout="wide",
)
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Guard: require Home load
# ──────────────────────────────────────────────
if "filtered_df" not in st.session_state or "df" not in st.session_state:
    st.warning("⚠️ Please navigate to the **Home** page first to load data.")
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]

# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown("## 💬 Actionable Insights")
st.caption("Flag delayed shipments, add business comments, and review team annotations — all stored in MongoDB.")
st.divider()

# ──────────────────────────────────────────────
# Shared constants
# ──────────────────────────────────────────────
PRIORITY_COLORS = {
    "Critical": "#E63946",
    "High":     "#FFB703",
    "Medium":   "#00B4D8",
    "Low":      "#8B95A5",
}
FLAG_ICONS = {
    "Delay Risk":             "⏱️",
    "Exception – Customs":    "🛃",
    "Exception – Carrier":    "🚚",
    "Revenue Anomaly":        "📉",
    "Overweight / Dimensions":"⚖️",
    "Route Concern":          "🗺️",
    "Positive Highlight":     "⭐",
    "Other":                  "💬",
}
FLAG_OPTIONS = list(FLAG_ICONS.keys())


def _render_insight_card(ins: dict) -> None:
    """Render a single insight as a styled HTML card."""
    p = ins.get("priority", "Medium")
    p_color = PRIORITY_COLORS.get(p, "#8B95A5")
    icon = FLAG_ICONS.get(ins.get("flag_type", ""), "💬")
    submitted_at = ins.get("submitted_at")
    if isinstance(submitted_at, datetime):
        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=timezone.utc).astimezone(TZ_ICT)
        else:
            submitted_at = submitted_at.astimezone(TZ_ICT)
        ts = submitted_at.strftime("%d %b %Y  %H:%M Thailand Time")
    else:
        ts = "—"

    st.markdown(
        f"""
<div style="
    background: rgba(13,27,42,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid {p_color};
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-weight:700; color:#F0F2F6; font-size:0.95rem;">
            {icon} {ins.get('flag_type', 'Insight')}
        </span>
        <span style="
            background: rgba(255,255,255,0.06);
            border-radius: 9999px;
            padding: 2px 10px;
            font-size: 0.72rem;
            font-weight: 600;
            color: {p_color};
        ">{p}</span>
    </div>
    <div style="font-size:0.82rem; color:#8B95A5; margin-bottom:6px;">
        🚢 <strong style="color:#F0F2F6;">{ins.get('shipment_id', '—')}</strong>
        &nbsp;·&nbsp; 👤 {ins.get('analyst', '—')}
        &nbsp;·&nbsp; 🕐 {ts}
    </div>
    <div style="font-size:0.88rem; color:#C0C8D4; line-height:1.55;">
        {ins.get('comment', '')}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────
tab_submit, tab_browse = st.tabs([
    "📝 Submit & Overview",
    "🔍 Browse by Flag",
])

# ══════════════════════════════════════════════
# TAB 1 – Summary Stats + Submit Insight
# ══════════════════════════════════════════════
with tab_submit:
    # ── Summary Stats (top) ────────────────────
    st.markdown("### 📊 Insights Overview")
    _all_insights_top = get_recent_insights(limit=500)
    if _all_insights_top:
        _ins_df = pd.DataFrame(_all_insights_top)
        import plotly.express as px

        _c1, _c2, _c3, _c4 = st.columns(4)
        with _c1:
            st.metric("Total Insights", f"{len(_ins_df):,}")
        with _c2:
            _critical = (
                len(_ins_df[_ins_df["priority"] == "Critical"])
                if "priority" in _ins_df.columns else 0
            )
            st.metric("Critical Flags", f"{_critical:,}")
        with _c3:
            _analysts = _ins_df["analyst"].nunique() if "analyst" in _ins_df.columns else 0
            st.metric("Unique Analysts", f"{_analysts:,}")
        with _c4:
            _top_flag = (
                _ins_df["flag_type"].mode()[0]
                if "flag_type" in _ins_df.columns and len(_ins_df) > 0 else "—"
            )
            st.metric("Most Common Flag", _top_flag)

        if "flag_type" in _ins_df.columns and len(_ins_df) > 0:
            _flag_counts = _ins_df["flag_type"].value_counts().reset_index()
            _flag_counts.columns = ["Flag Type", "Count"]
            _fig = px.bar(
                _flag_counts, x="Count", y="Flag Type", orientation="h",
                color="Count",
                color_continuous_scale=["#0E4D64", "#00B4D8", "#00D4AA"],
                labels={"Count": "Submissions", "Flag Type": ""},
            )
            _fig.update_layout(
                template=PLOTLY_TEMPLATE, height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
            )
            _fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            _fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(_fig, use_container_width=True)
    else:
        st.info("No insights data yet. Submit your first insight below!")

    st.divider()

    col_form, col_feed = st.columns([1, 1], gap="large")

    # ── LEFT: Submission Form ──────────────────
    with col_form:
        st.markdown("### 📝 Submit an Insight")
        st.markdown(
            '<div class="insight-box">💡 Use this form to flag a shipment issue, '
            'add a business observation, or record a recommended action. '
            'Data is written directly to MongoDB in real-time.</div>',
            unsafe_allow_html=True,
        )

        recent_shipment_ids = (
            filtered.sort_values("Order Date", ascending=False)["Shipment ID"]
            .dropna()
            .unique()
            .tolist()[:200]
            if "Shipment ID" in filtered.columns
            else []
        )

        with st.form("insight_form", clear_on_submit=True):
            st.markdown("**🔍 Shipment Reference**")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                shipment_id = st.selectbox(
                    "Select Shipment ID",
                    options=["— manual entry —"] + recent_shipment_ids,
                    key="form_shipment_select",
                )
            with col_b:
                manual_id = st.text_input(
                    "Or enter manually",
                    placeholder="SHP-XXXXX",
                    key="form_shipment_manual",
                )

            analyst = st.text_input(
                "👤 Analyst Name",
                placeholder="e.g., Alice Chen",
                key="form_analyst",
            )

            flag_type = st.selectbox(
                "🚩 Flag Type",
                options=FLAG_OPTIONS,
                key="form_flag_type",
            )

            priority = st.radio(
                "⚡ Priority",
                options=["Low", "Medium", "High", "Critical"],
                horizontal=True,
                index=1,
                key="form_priority",
            )

            comment = st.text_area(
                "📋 Business Comment / Recommended Action",
                placeholder="Describe the issue or recommended action in detail…",
                height=130,
                key="form_comment",
            )

            submitted = st.form_submit_button("🚀 Submit Insight", type="primary", use_container_width=True)

        if submitted:
            resolved_id = manual_id.strip() if manual_id.strip() else (
                shipment_id if shipment_id != "— manual entry —" else ""
            )
            if not resolved_id:
                st.error("❌ Please select or enter a Shipment ID.")
            elif not analyst.strip():
                st.error("❌ Please enter your name as the analyst.")
            elif not comment.strip():
                st.error("❌ Please add a business comment.")
            else:
                payload = {
                    "shipment_id": resolved_id,
                    "analyst":     analyst.strip(),
                    "flag_type":   flag_type,
                    "priority":    priority,
                    "comment":     comment.strip(),
                    "submitted_at": datetime.now(TZ_ICT),
                }
                success = submit_insight(payload)
                if success:
                    st.success(f"✅ Insight submitted for **{resolved_id}** and saved to MongoDB!")
                    st.balloons()
                else:
                    st.error("❌ Failed to write to MongoDB. Check your connection in `secrets.toml`.")

    # ── RIGHT: Latest Insights Feed ────────────
    with col_feed:
        st.markdown("### 📡 Latest Insights Feed")
        st.markdown(
            '<div class="insight-box">💡 Showing the 10 most recent insights submitted by your team, '
            'read live from MongoDB.</div>',
            unsafe_allow_html=True,
        )

        if st.button("🔄 Refresh Feed", use_container_width=True, key="refresh_feed_submit"):
            st.cache_data.clear()

        insights = get_recent_insights(limit=10)

        if not insights:
            st.info("No insights submitted yet. Be the first to flag a shipment!")
        else:
            for ins in insights:
                _render_insight_card(ins)


# ══════════════════════════════════════════════
# TAB 2 – Browse by Flag
# ══════════════════════════════════════════════
with tab_browse:
    st.markdown("### 🔍 Browse & Filter Submitted Insights")
    st.markdown(
        '<div class="insight-box">💡 Use the filters below to narrow down submitted insights '
        'by flag type, priority, analyst name, or shipment ID.</div>',
        unsafe_allow_html=True,
    )

    # ── Load all insights ──────────────────────
    if st.button("🔄 Refresh", use_container_width=False, key="refresh_feed_browse"):
        st.cache_data.clear()

    all_raw = get_recent_insights(limit=500)

    if not all_raw:
        st.info("No insights submitted yet. Head to the **Submit Insight** tab to add the first one!")
    else:
        browse_df = pd.DataFrame(all_raw)

        # ── Filter controls ────────────────────
        fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 2], gap="medium")

        with fcol1:
            flag_filter = st.multiselect(
                "🚩 Flag Type",
                options=FLAG_OPTIONS,
                default=[],
                placeholder="All flag types",
                key="browse_flag_filter",
            )
        with fcol2:
            priority_filter = st.multiselect(
                "⚡ Priority",
                options=["Critical", "High", "Medium", "Low"],
                default=[],
                placeholder="All priorities",
                key="browse_priority_filter",
            )
        with fcol3:
            analyst_options = (
                sorted(browse_df["analyst"].dropna().unique().tolist())
                if "analyst" in browse_df.columns
                else []
            )
            analyst_filter = st.multiselect(
                "👤 Analyst",
                options=analyst_options,
                default=[],
                placeholder="All analysts",
                key="browse_analyst_filter",
            )
        with fcol4:
            shipment_filter = st.text_input(
                "🚢 Shipment ID contains",
                placeholder="e.g. SHP-001",
                key="browse_shipment_filter",
            )

        # ── Apply filters ──────────────────────
        view_df = browse_df.copy()

        if flag_filter:
            view_df = view_df[view_df["flag_type"].isin(flag_filter)]
        if priority_filter:
            view_df = view_df[view_df["priority"].isin(priority_filter)]
        if analyst_filter:
            view_df = view_df[view_df["analyst"].isin(analyst_filter)]
        if shipment_filter.strip():
            view_df = view_df[
                view_df["shipment_id"]
                .astype(str)
                .str.contains(shipment_filter.strip(), case=False, na=False)
            ]

        # Sort newest first
        if "submitted_at" in view_df.columns:
            view_df = view_df.sort_values("submitted_at", ascending=False)

        # ── Result count ───────────────────────
        total = len(view_df)
        st.markdown(
            f"<p style='color:#8B95A5; font-size:0.85rem; margin:8px 0 14px;'>"
            f"Showing <strong style='color:#F0F2F6;'>{total}</strong> insight{'s' if total != 1 else ''}"
            f"</p>",
            unsafe_allow_html=True,
        )

        if total == 0:
            st.warning("No insights match the selected filters.")
        else:
            for _, row in view_df.iterrows():
                _render_insight_card(row.to_dict())


