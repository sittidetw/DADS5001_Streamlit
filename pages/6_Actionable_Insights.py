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
# Layout: Form + Recent Insights
# ──────────────────────────────────────────────
col_form, col_feed = st.columns([1, 1], gap="large")

# ──────────────────────────────────────────────
# LEFT: Submission Form
# ──────────────────────────────────────────────
with col_form:
    st.markdown("### 📝 Submit an Insight")
    st.markdown(
        '<div class="insight-box">💡 Use this form to flag a shipment issue, '
        'add a business observation, or record a recommended action. '
        'Data is written directly to MongoDB in real-time.</div>',
        unsafe_allow_html=True,
    )

    # ── Populate shipment IDs from loaded data ─────────────────────────
    recent_shipment_ids = (
        filtered.sort_values("Order Date", ascending=False)["Shipment ID"]
        .dropna()
        .unique()
        .tolist()[:200]
        if "Shipment ID" in filtered.columns
        else []
    )

    with st.form("insight_form", clear_on_submit=True):
        # Shipment reference
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

        # Analyst name
        analyst = st.text_input(
            "👤 Analyst Name",
            placeholder="e.g., Alice Chen",
            key="form_analyst",
        )

        # Flag type
        flag_type = st.selectbox(
            "🚩 Flag Type",
            options=[
                "Delay Risk",
                "Exception – Customs",
                "Exception – Carrier",
                "Revenue Anomaly",
                "Overweight / Dimensions",
                "Route Concern",
                "Positive Highlight",
                "Other",
            ],
            key="form_flag_type",
        )

        # Priority
        priority = st.radio(
            "⚡ Priority",
            options=["Low", "Medium", "High", "Critical"],
            horizontal=True,
            index=1,
            key="form_priority",
        )

        # Comment
        comment = st.text_area(
            "📋 Business Comment / Recommended Action",
            placeholder="Describe the issue or recommended action in detail…",
            height=130,
            key="form_comment",
        )

        submitted = st.form_submit_button("🚀 Submit Insight", type="primary", use_container_width=True)

    # ── Handle Submission ──────────────────────────────────────────────
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
                "analyst": analyst.strip(),
                "flag_type": flag_type,
                "priority": priority,
                "comment": comment.strip(),
                "submitted_at": datetime.now(TZ_ICT),
            }
            success = submit_insight(payload)
            if success:
                st.success(f"✅ Insight submitted for **{resolved_id}** and saved to MongoDB!")
                st.balloons()
            else:
                st.error("❌ Failed to write to MongoDB. Check your connection in `secrets.toml`.")

# ──────────────────────────────────────────────
# RIGHT: Recent Insights Feed
# ──────────────────────────────────────────────
with col_feed:
    st.markdown("### 📡 Latest Insights Feed")
    st.markdown(
        '<div class="insight-box">💡 Showing the 10 most recent insights submitted by your team, '
        'read live from MongoDB.</div>',
        unsafe_allow_html=True,
    )

    # Refresh button
    if st.button("🔄 Refresh Feed", use_container_width=True):
        st.cache_data.clear()

    insights = get_recent_insights(limit=10)

    if not insights:
        st.info("No insights submitted yet. Be the first to flag a shipment!")
    else:
        priority_colors = {
            "Critical": "#E63946",
            "High": "#FFB703",
            "Medium": "#00B4D8",
            "Low": "#8B95A5",
        }
        flag_icons = {
            "Delay Risk": "⏱️",
            "Exception – Customs": "🛃",
            "Exception – Carrier": "🚚",
            "Revenue Anomaly": "📉",
            "Overweight / Dimensions": "⚖️",
            "Route Concern": "🗺️",
            "Positive Highlight": "⭐",
            "Other": "💬",
        }

        for ins in insights:
            p = ins.get("priority", "Medium")
            p_color = priority_colors.get(p, "#8B95A5")
            icon = flag_icons.get(ins.get("flag_type", ""), "💬")
            submitted_at = ins.get("submitted_at")
            if isinstance(submitted_at, datetime):
                # MongoDB returns naive UTC datetimes; convert to Thailand time for display
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
# Bottom: Summary Stats
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Insights Summary")

all_insights = get_recent_insights(limit=500)
if all_insights:
    ins_df = pd.DataFrame(all_insights)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Insights", f"{len(ins_df):,}")
    with c2:
        critical_count = len(ins_df[ins_df.get("priority", pd.Series(dtype=str)) == "Critical"]) if "priority" in ins_df.columns else 0
        st.metric("Critical Flags", f"{critical_count:,}")
    with c3:
        analysts = ins_df["analyst"].nunique() if "analyst" in ins_df.columns else 0
        st.metric("Unique Analysts", f"{analysts:,}")
    with c4:
        top_flag = ins_df["flag_type"].mode()[0] if "flag_type" in ins_df.columns and len(ins_df) > 0 else "—"
        st.metric("Most Common Flag", top_flag)

    if "flag_type" in ins_df.columns and len(ins_df) > 0:
        import plotly.express as px
        flag_counts = ins_df["flag_type"].value_counts().reset_index()
        flag_counts.columns = ["Flag Type", "Count"]
        fig = px.bar(
            flag_counts, x="Count", y="Flag Type", orientation="h",
            color="Count",
            color_continuous_scale=["#0E4D64", "#00B4D8", "#00D4AA"],
            labels={"Count": "Submissions", "Flag Type": ""},
        )
        fig.update_layout(
            template=PLOTLY_TEMPLATE, height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No insights data yet. Submit your first insight above!")
