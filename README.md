# ShipInsight – International Shipment Analytics

> A multi-page **Streamlit** dashboard built for the **DADS5001** course (NIDA, Semester 2/2568).  
> Analyses 100,000+ international shipment records with interactive BI views, statistical forecasting, and optional AI-powered insights via OpenRouter.

---

## Links

| | |
|---|---|
| 🚀 **Live App** | <a href="https://shipinsight.streamlit.app" target="_blank">shipinsight.streamlit.app</a> |
| 🎬 **Presentation Video** | <a href="https://nida365-my.sharepoint.com/:v:/g/personal/6810422030_stu_nida_ac_th/IQC-t7nCncp7RqpFGddLE7j6AVO2NFbnUBdEAcdG4YxoweY" target="_blank">Watch on SharePoint</a> |

> 🔒 The presentation video is hosted on NIDA SharePoint and is accessible to **NIDA members only** (requires a `@stu.nida.ac.th` or `@nida.ac.th` account).

---

## Members
- 6810422001 Jedsadaporn Jinasena
- 6810422002 Pichaya Jandokmai
- 6810422030 Sittidet Wichaidit

---

## Overview

**ShipInsight** is a data analytics platform for international logistics operations. It pulls shipment data from **Snowflake**, uses **DuckDB** for in-browser SQL analytics, persists user preferences and team annotations in **MongoDB**, and optionally calls an LLM through **OpenRouter** when AI Mode is enabled.

The app is designed with a custom *Deep Horizon* dark design system — glassmorphism cards, animated gradients, and Plotly charts themed to match.

---

## Features & Pages

| # | Page | Description |
|---|------|-------------|
| 🏠 | **Home** | Landing page with global sidebar filters (date range, industry, destination country). Loads data from Snowflake and seeds MongoDB metadata. Shows top-level KPI cards. |
| 1 | **Executive Overview** | High-level business pulse: total shipments & revenue with period-over-period deltas, monthly trend chart (dual-axis), shipment status donut, inbound vs. outbound split, revenue by industry, and revenue by salesperson. AI Mode adds a GPT-generated 2-paragraph executive summary. |
| 2 | **Financial Performance** | Deep-dive into pricing: RRP vs. ASP (billing price) gap over time, promotion effectiveness (revenue & discount cost by promotion type), industry revenue vs. net margin, and a monthly gross/net/discount area chart. AI Mode generates a financial analysis with pricing strategy recommendations. |
| 3 | **Logistics & Weight Analytics** | Weight optimisation analysis: actual vs. volumetric vs. chargeable weight distributions, weight-type breakdown, package dimension analysis, cargo efficiency metrics. |
| 4 | **Regional Route Analysis** | Geographic trade-flow mapping, route ranking by volume and revenue, origin/destination region heatmaps, and country-level drill-downs. |
| 5 | **AI Insights & Forecasting** | Three tabs: **(a) SQL Explorer / Chat with Data** — run DuckDB SQL or ask natural-language questions (AI Mode auto-generates and executes the SQL then summarises results); **(b) Forecasting** — Holt-Winters Exponential Smoothing projections for revenue and shipment volume with configurable horizon (1–12 months) and confidence bands; **(c) Anomaly Detection** — rolling-mean ±1.5σ anomaly flags on monthly revenue plus a route-level exception-rate scatter plot. |
| 6 | **Actionable Insights** | Team collaboration layer backed by MongoDB. Analysts can flag shipment issues (delay risk, customs exception, revenue anomaly, etc.), set priority (Low → Critical), and add business comments. A live feed shows the 10 most recent submissions; a browse tab lets you filter by flag type, priority, analyst, or shipment ID. |

---

## Architecture

```
┌─────────────────────────────────────────┐
│              Streamlit App              │
│  Home.py  +  pages/1_…6_*.py           │
│  theme.py (CSS / Plotly design system)  │
└───────────┬─────────────────┬───────────┘
            │                 │
     ┌──────▼──────┐   ┌──────▼──────┐
     │  Snowflake  │   │   MongoDB   │
     │  (primary   │   │  (optional  │
     │   dataset)  │   │  write-back)│
     └─────────────┘   └─────────────┘
            │
     ┌──────▼──────┐
     │   DuckDB    │  ← in-process SQL on pandas DataFrames
     └─────────────┘
            │
     ┌──────▼──────┐
     │  OpenRouter │  ← LLM API (AI Mode only)
     │  (GPT-4o)   │
     └─────────────┘
```

**Data layer (`db.py`):**
- `init_connections()` — cached `@st.cache_resource` connecting to Snowflake (required) and MongoDB (optional, non-fatal).
- `load_data_from_snowflake()` — cached 10-min TTL, fetches the full `SHIPMENT` table, parses dates and numeric columns.
- MongoDB helpers — `save_user_preferences`, `get_latest_today_preferences`, `seed_filter_metadata_from_df`, `submit_insight`, `get_recent_insights`.
- `render_data_source_badge()` — shows live/offline status badges in the sidebar.

**Streamlit caching & state strategy:**

| Mechanism | Where used | Purpose |
|-----------|-----------|--------|
| `@st.cache_resource` | `init_connections()` | Keeps Snowflake and MongoDB connections alive across reruns and users — initialised once per server process. |
| `@st.cache_data(ttl=600)` | `load_data_from_snowflake()` | Caches the full 100 K-row DataFrame in memory for 10 minutes, avoiding repeated round-trips to Snowflake on every page navigation or filter change. |
| `st.session_state` | All pages | Shares the filtered DataFrame (`filtered_df`), active filter selections (`date_start`, `date_end`, `selected_industries`, `selected_countries`), and the AI Mode toggle across the entire multi-page app within a single browser session. |

**Design system (`theme.py`):**  
Centralises all CSS variables (*Deep Horizon* palette), Plotly template, colour sequences, and a `render_sidebar_filters()` helper used by every analytics page.

---

## Dataset

The dataset (`International_Shipment_100k_V3.csv`, ~21 MB) has been ingested into Snowflake as the table `DADS5001_SHIPINSIGHT.PUBLIC.SHIPMENT` — this is the **live data source** the app queries at runtime. The CSV file is kept in the repository as a reference copy only. The table contains ~100,000 rows with fields including:

> **Note:** The dataset is **synthetically generated** for educational purposes. It does not represent real shipment transactions.

| Field | Description |
|-------|-------------|
| Order ID / Order Date | Shipment identifier and date |
| Customer ID / Sales Person | Customer and sales channel |
| Industry | Shipper industry sector |
| Shipment Status | `Completed`, `In Transit`, `Exception` |
| Inbound/Outbound | Trade direction |
| Country of Origin / Destination | Geographic endpoints |
| Region of Origin / Destination | Regional grouping |
| Weight Type | Actual or volumetric billing basis |
| Actual / Volumetric / Chargeable Weight (kg) | Package weight dimensions |
| Width / Length / Height (cm) | Package dimensions |
| RRP (Gross Price) | List price before discount |
| Back Margin (Promotion Expense) | Discount applied |
| Billing Price (ASP) | Net price charged |
| Fuel Surcharge (FSC) | Carrier fuel levy |
| Revenue | Final recognised revenue |
| Promotion Type | Promotion category |
| FTB (First time buyer) | Boolean first-purchase flag |

---

## Key Libraries

| Library | Purpose |
|---------|---------|
| `streamlit` | Web app framework |
| `pandas` | DataFrame manipulation |
| `duckdb` | In-process SQL analytics on DataFrames |
| `plotly` | Interactive charts |
| `snowflake-connector-python` | Snowflake data source |
| `pymongo` | MongoDB write-back / annotations |
| `openai` | OpenRouter LLM API client (AI Mode) |
| `statsmodels` | Holt-Winters forecasting |
| `scipy` / `numpy` | Statistical computations |

---

## Project Structure

```
DADS5001_Streamlit/
├── Home.py                          # Entry point – global filters & landing page
├── db.py                            # Data layer: Snowflake + MongoDB helpers
├── theme.py                         # CSS design system + Plotly theme
├── pages/
│   ├── 1_Executive_Overview.py
│   ├── 2_Financial_Performance.py
│   ├── 3_Logistics_and_Weight_Analytics.py
│   ├── 4_Regional_Route_Analysis.py
│   ├── 5_AI_Insights_and_Forecasting.py
│   └── 6_Actionable_Insights.py
├── International_Shipment_100k_V3.csv   # Local dataset (fallback reference)
├── requirements.txt
└── .streamlit/
    └── secrets.toml                 # Credentials (not committed to git)
```

---

## Course Context

This project was developed as part of **DADS5001 – Data Analytics and Data Science Tools** at the **National Institute of Development Administration (NIDA)**, Thailand, Academic Year 2568, Semester 2.
