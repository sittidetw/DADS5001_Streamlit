import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from theme import PAGE_CSS, PLOTLY_TEMPLATE, COLOR_SEQ, CHART_LAYOUT, GRID_COLOR, apply_chart_style, render_sidebar_filters

st.set_page_config(page_title="AI Insights – ShipInsight", page_icon="🤖", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ── Sidebar Filters (renders on every page) ───────────────────
_filtered = render_sidebar_filters()
if _filtered is None:
    st.stop()

df = st.session_state["df"]
filtered = st.session_state["filtered_df"]
ai_mode = st.session_state.get("ai_mode", False)


def qr(query: str) -> pd.DataFrame:
    return duckdb.query(query).to_df()

st.markdown("## AI Insights & Forecasting")
st.caption("Predictive analytics, anomaly detection, and intelligent data querying.")
st.divider()

# ══════════════════════════════════════════════
# Tab Layout
# ══════════════════════════════════════════════
if ai_mode:
    tab1, tab2, tab3 = st.tabs(["Chat with Data", "Forecasting", "Anomaly Detection"])
else:
    tab1, tab2, tab3 = st.tabs(["SQL Query Explorer", "Forecasting", "Anomaly Detection"])

# ──────────────────────────────────────────────
# TAB 1: SQL / Chat
# ──────────────────────────────────────────────
with tab1:
    if not ai_mode:
        st.markdown("### DuckDB SQL Query Explorer")
        st.markdown('<div class="insight-box">💡 Write SQL queries against the <code>filtered</code> dataframe. Use column names in double quotes. Toggle AI mode in the sidebar for natural language queries.</div>', unsafe_allow_html=True)

        templates = {
            "— Select a template —": "",
            "Top 5 Industries by Revenue": 'SELECT "Industry", SUM("Revenue") AS total_revenue FROM filtered GROUP BY "Industry" ORDER BY total_revenue DESC LIMIT 5',
            "Monthly Shipment Count": 'SELECT DATE_TRUNC(\'month\', "Order Date") AS month, COUNT(*) AS shipments FROM filtered GROUP BY 1 ORDER BY 1',
            "Avg Revenue by Status": 'SELECT "Shipment Status", AVG("Revenue") AS avg_rev, COUNT(*) AS cnt FROM filtered GROUP BY "Shipment Status"',
            "Top Routes by Volume": 'SELECT "Country of Origin" || \' → \' || "Country of Destination" AS route, COUNT(*) AS volume FROM filtered GROUP BY route ORDER BY volume DESC LIMIT 10',
        }
        template = st.selectbox("Query Templates", list(templates.keys()))
        default_q = templates[template] if template != "— Select a template —" else ""

        user_sql = st.text_area("Enter DuckDB SQL:", value=default_q, height=120, placeholder='SELECT "Industry", COUNT(*) FROM filtered GROUP BY "Industry"')

        if st.button("▶️ Run Query", type="primary"):
            if user_sql.strip():
                try:
                    result = qr(user_sql)
                    st.success(f"{len(result)} rows returned")
                    st.dataframe(result, use_container_width=True)
                    # Auto-chart if small result
                    if len(result) <= 50 and len(result.columns) >= 2:
                        num_cols = result.select_dtypes(include="number").columns.tolist()
                        str_cols = result.select_dtypes(include="object").columns.tolist()
                        if num_cols and str_cols:
                            fig = px.bar(result, x=str_cols[0], y=num_cols[0], color_discrete_sequence=["#00D4AA"],
                                         labels={str_cols[0]: str_cols[0], num_cols[0]: num_cols[0]})
                            fig.update_layout(template=PLOTLY_TEMPLATE, height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
                            fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
                            st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Query error: {e}")
            else:
                st.warning("Please enter a SQL query.")

    else:
        # AI Chat Mode
        st.markdown("### 💬 Chat with Your Data")
        st.markdown('<div class="insight-box">💡 Ask questions in natural language. The AI will translate your question to SQL, execute it, and visualize the results.</div>', unsafe_allow_html=True)

        cols_info = ", ".join([f'"{c}"' for c in filtered.columns[:20]])

        try:
            from openai import OpenAI
            api_key = st.secrets.get("OPENROUTER_API_KEY", None)
            if not api_key:
                st.warning("🔑 Add `OPENROUTER_API_KEY` to `.streamlit/secrets.toml` to enable AI chat.")
            else:
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )
                question = st.text_input("🗣️ Ask a question about your shipment data:", placeholder="e.g., Which industry had the highest revenue in Q1 2025?")

                if question:
                    with st.spinner("🧠 Translating to SQL…"):
                        prompt = f"""DuckDB SQL expert. Write a SQL query for: {question}
Table 'filtered', columns: {cols_info}. "Order Date" is timestamp. Double-quote column names. Return SQL only."""
                        resp = client.chat.completions.create(
                            model="google/gemma-4-26b-a4b-it:free",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        sql = resp.choices[0].message.content.strip().replace("```sql", "").replace("```", "").strip()

                        st.code(sql, language="sql")
                        try:
                            result = qr(sql)
                            st.dataframe(result, use_container_width=True)
                            # Auto chart
                            num_cols = result.select_dtypes(include="number").columns.tolist()
                            str_cols = result.select_dtypes(include="object").columns.tolist()
                            if num_cols and str_cols and len(result) <= 50:
                                fig = px.bar(result, x=str_cols[0], y=num_cols[0], color_discrete_sequence=["#00D4AA"])
                                fig.update_layout(template=PLOTLY_TEMPLATE, height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                                st.plotly_chart(fig, use_container_width=True)

                            # AI summary
                            summary_prompt = f"1-sentence summary for executive. Q: {question}\nData: {result.head(5).to_csv(index=False)}"
                            summary = client.chat.completions.create(
                                model="openai/gpt-oss-120b:free",
                                messages=[{"role": "user", "content": summary_prompt}],
                            )
                            st.markdown(f"**📝 Summary:** {summary.choices[0].message.content}")
                        except Exception as e:
                            st.error(f"SQL execution error: {e}")
        except ImportError:
            st.info("Install `openai` for AI chat.")
        except Exception as e:
            st.error(f"Error: {e}")

# ──────────────────────────────────────────────
# TAB 2: Forecasting
# ──────────────────────────────────────────────
with tab2:
    st.markdown("### Revenue & Volume Forecasting")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Uses Holt-Winters Exponential Smoothing to project future shipment volumes and revenue, capturing both trend and seasonality. The shaded region shows the confidence interval.</div>', unsafe_allow_html=True)

    forecast_months = st.slider("Forecast horizon (months):", 1, 12, 6)

    monthly = qr("""
        SELECT DATE_TRUNC('month', "Order Date") AS month, SUM("Revenue") AS revenue, COUNT(*) AS shipments
        FROM filtered GROUP BY 1 ORDER BY 1
    """)
    monthly["month"] = pd.to_datetime(monthly["month"])

    if len(monthly) >= 3:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            seasonal_periods = 12 if len(monthly) >= 24 else None
            trend = "add"
            seasonal = "add" if seasonal_periods else None

            hw_rev = ExponentialSmoothing(monthly["revenue"], trend=trend, seasonal=seasonal, seasonal_periods=seasonal_periods, initialization_method="estimated").fit()
            hw_ship = ExponentialSmoothing(monthly["shipments"], trend=trend, seasonal=seasonal, seasonal_periods=seasonal_periods, initialization_method="estimated").fit()

            pred_rev = hw_rev.forecast(forecast_months).values
            pred_ship = hw_ship.forecast(forecast_months).values
            
            rev_std = monthly["revenue"].std() * 0.2 + (np.arange(forecast_months) * monthly["revenue"].std() * 0.05)
            ship_std = monthly["shipments"].std() * 0.2 + (np.arange(forecast_months) * monthly["shipments"].std() * 0.05)
        except Exception as e:
            from numpy.polynomial import polynomial as P
            monthly["month_num"] = np.arange(len(monthly))
            coeffs_rev = P.polyfit(monthly["month_num"], monthly["revenue"], 1)
            coeffs_ship = P.polyfit(monthly["month_num"], monthly["shipments"], 1)

            future_nums = np.arange(len(monthly), len(monthly) + forecast_months)
            pred_rev = P.polyval(future_nums, coeffs_rev)
            pred_ship = P.polyval(future_nums, coeffs_ship)

            rev_std = monthly["revenue"].std() * 0.3
            ship_std = monthly["shipments"].std() * 0.3

        future_months = pd.date_range(start=monthly["month"].iloc[-1] + pd.DateOffset(months=1), periods=forecast_months, freq="MS")

        # Revenue forecast chart
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=monthly["month"], y=monthly["revenue"], name="Actual Revenue", mode="lines+markers", line=dict(color="#00D4AA", width=2.5), marker=dict(size=5)))
        fig_fc.add_trace(go.Scatter(x=future_months, y=pred_rev, name="Forecast", mode="lines+markers", line=dict(color="#FFB703", width=2.5, dash="dash"), marker=dict(size=5)))
        fig_fc.add_trace(go.Scatter(x=list(future_months) + list(future_months[::-1]), y=list(pred_rev + rev_std) + list((pred_rev - rev_std)[::-1]),
                                     fill="toself", fillcolor="rgba(255,183,3,0.1)", line=dict(width=0), name="Confidence", showlegend=False))

        fig_fc.update_layout(template=PLOTLY_TEMPLATE, height=400, margin=dict(l=20, r=20, t=30, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                              yaxis_title="Revenue (฿)", hovermode="x unified")
        fig_fc.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_fc.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_fc, use_container_width=True)

        # Volume forecast
        fig_vs = go.Figure()
        fig_vs.add_trace(go.Scatter(x=monthly["month"], y=monthly["shipments"], name="Actual Shipments", mode="lines+markers", line=dict(color="#00B4D8", width=2.5)))
        fig_vs.add_trace(go.Scatter(x=future_months, y=pred_ship, name="Forecast", mode="lines+markers", line=dict(color="#E63946", width=2.5, dash="dash")))
        fig_vs.add_trace(go.Scatter(x=list(future_months) + list(future_months[::-1]), y=list(pred_ship + ship_std) + list((pred_ship - ship_std)[::-1]),
                                     fill="toself", fillcolor="rgba(230,57,70,0.1)", line=dict(width=0), name="Confidence", showlegend=False))
        fig_vs.update_layout(template=PLOTLY_TEMPLATE, height=400, margin=dict(l=20, r=20, t=30, b=20),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                              yaxis_title="Shipment Count", hovermode="x unified")
        fig_vs.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_vs.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_vs, use_container_width=True)

        if ai_mode:
            try:
                from openai import OpenAI
                api_key = st.secrets.get("OPENROUTER_API_KEY", None)
                if api_key:
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                    ctx = {"last_3_months": monthly[["month", "revenue", "shipments"]].tail(3).to_csv(index=False),
                           "forecast_revenue": [f"{m},{r:.0f}" for m, r in zip(future_months, pred_rev)],
                           "forecast_shipments": [f"{m},{s:.0f}" for m, s in zip(future_months, pred_ship)]}
                    prompt = f"""Forecasting analyst. Give 2 strategic recommendations based on these logistics forecasts.\nData: {ctx}"""
                    with st.spinner("🧠 AI forecast analysis…"):
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-120b:free",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        st.markdown(response.choices[0].message.content)
            except Exception:
                pass
    else:
        st.info("Not enough data for forecasting. Select a wider date range.")

# ──────────────────────────────────────────────
# TAB 3: Anomaly Detection
# ──────────────────────────────────────────────
with tab3:
    st.markdown("### Revenue Anomaly Detection")
    st.markdown('<div class="insight-box">💡 <strong>Insight:</strong> Anomalies are months where revenue deviates more than 1.5 standard deviations from the rolling mean. These may indicate seasonal spikes, market disruptions, or operational issues.</div>', unsafe_allow_html=True)

    monthly_anom = qr("""
        SELECT DATE_TRUNC('month', "Order Date") AS month, SUM("Revenue") AS revenue, COUNT(*) AS shipments
        FROM filtered GROUP BY 1 ORDER BY 1
    """)
    monthly_anom["month"] = pd.to_datetime(monthly_anom["month"])

    if len(monthly_anom) >= 4:
        window = min(6, len(monthly_anom) // 2)
        monthly_anom["rolling_mean"] = monthly_anom["revenue"].rolling(window=window, min_periods=2, center=True).mean()
        monthly_anom["rolling_std"] = monthly_anom["revenue"].rolling(window=window, min_periods=2, center=True).std()
        monthly_anom["upper"] = monthly_anom["rolling_mean"] + 1.5 * monthly_anom["rolling_std"]
        monthly_anom["lower"] = monthly_anom["rolling_mean"] - 1.5 * monthly_anom["rolling_std"]
        monthly_anom["is_anomaly"] = (monthly_anom["revenue"] > monthly_anom["upper"]) | (monthly_anom["revenue"] < monthly_anom["lower"])

        anomalies = monthly_anom[monthly_anom["is_anomaly"]]

        fig_anom = go.Figure()
        fig_anom.add_trace(go.Scatter(x=monthly_anom["month"], y=monthly_anom["revenue"], name="Revenue", mode="lines+markers", line=dict(color="#00D4AA", width=2), marker=dict(size=5)))
        fig_anom.add_trace(go.Scatter(x=monthly_anom["month"], y=monthly_anom["rolling_mean"], name="Rolling Mean", line=dict(color="#8B95A5", width=1.5, dash="dot")))
        fig_anom.add_trace(go.Scatter(x=list(monthly_anom["month"]) + list(monthly_anom["month"][::-1]),
                                       y=list(monthly_anom["upper"]) + list(monthly_anom["lower"][::-1]),
                                       fill="toself", fillcolor="rgba(139,149,165,0.1)", line=dict(width=0), name="Normal Range"))
        if len(anomalies) > 0:
            fig_anom.add_trace(go.Scatter(x=anomalies["month"], y=anomalies["revenue"], name="Anomaly", mode="markers",
                                           marker=dict(color="#E63946", size=14, symbol="x", line=dict(width=2, color="#E63946"))))

        fig_anom.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(l=20, r=20, t=20, b=20),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                yaxis_title="Revenue (฿)", hovermode="x unified")
        fig_anom.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_anom.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_anom, use_container_width=True)

        if len(anomalies) > 0:
            st.markdown(f"**{len(anomalies)} anomalous month(s) detected:**")
            for _, row in anomalies.iterrows():
                direction = "📈 Above" if row["revenue"] > row["rolling_mean"] else "📉 Below"
                deviation = abs(row["revenue"] - row["rolling_mean"]) / row["rolling_std"] if row["rolling_std"] > 0 else 0
                st.markdown(f"- **{row['month'].strftime('%B %Y')}**: ฿{row['revenue']:,.0f} ({direction} normal by {deviation:.1f}σ)")
        else:
            st.success("No significant anomalies detected in the selected period.")

        # Route anomalies
        st.divider()
        st.markdown("### Route-Level Anomaly Detection")
        route_stats = qr("""
            SELECT "Country of Origin" || ' → ' || "Country of Destination" AS route,
                   COUNT(*) AS shipments, AVG("Revenue") AS avg_rev, STDDEV("Revenue") AS std_rev,
                   SUM(CASE WHEN "Shipment Status" = 'Exception' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS exception_pct
            FROM filtered GROUP BY route HAVING COUNT(*) >= 20 ORDER BY exception_pct DESC LIMIT 10
        """)

        fig_route_anom = px.scatter(route_stats, x="avg_rev", y="exception_pct", size="shipments", color="exception_pct",
                                     text="route", size_max=40, color_continuous_scale=["#00D4AA", "#FFB703", "#E63946"],
                                     labels={"avg_rev": "Avg Revenue (฿)", "exception_pct": "Exception Rate (%)", "shipments": "Volume"})
        fig_route_anom.update_traces(textposition="top center", textfont_size=9)
        fig_route_anom.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(l=20, r=20, t=20, b=20),
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_route_anom.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig_route_anom.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig_route_anom, use_container_width=True)

        if ai_mode:
            try:
                from openai import OpenAI
                api_key = st.secrets.get("OPENROUTER_API_KEY", None)
                if api_key:
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                    ctx = {"anomalous_months": anomalies[["month", "revenue"]].to_csv(index=False) if len(anomalies) > 0 else "None",
                           "high_exception_routes": route_stats[["route", "exception_pct", "avg_rev"]].head(5).to_csv(index=False)}
                    prompt = f"""Risk analyst. Give 2 root cause hypotheses and 2 mitigation strategies for these anomalies.\nData: {ctx}"""
                    with st.spinner("🧠 AI anomaly analysis…"):
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-120b:free",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        st.markdown(response.choices[0].message.content)
            except Exception:
                pass
    else:
        st.info("Not enough data for anomaly detection. Select a wider date range.")
