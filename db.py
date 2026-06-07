"""
db.py – ShipInsight Data Layer
================================
Centralises all database connectivity for the Snowflake + MongoDB hybrid
architecture described in change_data_source.md.

Usage
-----
    from db import init_connections, run_snowflake_query, get_filter_metadata
    init_connections()  # idempotent – cached by @st.cache_resource
    df = run_snowflake_query("SELECT ...")
"""

import streamlit as st
import pandas as pd
import snowflake.connector
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

# Thailand Standard Time – ICT (GMT+7)
TZ_ICT = timezone(timedelta(hours=7))


# ──────────────────────────────────────────────────────────────
# 1. Connection Initialisation  (cached at resource level)
# ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="🔗 Connecting to databases…")
def init_connections():
    """
    Establish and cache connections to Snowflake and MongoDB.

    MongoDB failures are non-fatal — the app continues without write-back
    features if MongoDB is unreachable.

    Returns
    -------
    dict with keys:
        "snowflake"    : SnowflakeConnection  (raises on failure)
        "mongo"        : MongoClient | None
        "mongo_error"  : str | None
    """
    result = {"snowflake": None, "mongo": None, "mongo_error": None}

    # ── Snowflake (required) ───────────────────────────────────
    sf_cfg = st.secrets["snowflake"]
    snow_conn = snowflake.connector.connect(
        user=sf_cfg["user"],
        password=sf_cfg["password"],
        account=sf_cfg["account"],
        warehouse=sf_cfg["warehouse"],
        database=sf_cfg["database"],
        schema=sf_cfg["schema"],
        role=sf_cfg.get("role", ""),
        login_timeout=15,
        session_parameters={"QUERY_TAG": "ShipInsight-Streamlit"},
    )
    result["snowflake"] = snow_conn

    # ── MongoDB (optional — write-back features) ───────────────
    try:
        mongo_uri = st.secrets["mongo"]["uri"]
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")   # verify connectivity
        result["mongo"] = mongo_client
    except Exception as e:
        result["mongo_error"] = str(e)

    return result


# ──────────────────────────────────────────────────────────────
# 2. Snowflake Query Helper
# ──────────────────────────────────────────────────────────────

def run_snowflake_query(sql: str) -> pd.DataFrame:
    """
    Execute a SQL statement on Snowflake and return a Pandas DataFrame.
    """
    conns = init_connections()
    snow_conn = conns["snowflake"]
    try:
        cursor = snow_conn.cursor()
        cursor.execute(sql)
        df = cursor.fetch_pandas_all()
        cursor.close()
        return df
    except Exception as e:
        raise RuntimeError(f"Snowflake query failed: {e}") from e


# ──────────────────────────────────────────────────────────────
# 3. MongoDB Helpers  (all non-fatal)
# ──────────────────────────────────────────────────────────────

def _get_mongo_client():
    """Return MongoClient or None if MongoDB is unavailable."""
    return init_connections()["mongo"]


def get_mongo_collection(collection_name: str):
    """Return a PyMongo collection or None if MongoDB is unavailable."""
    client = _get_mongo_client()
    if client is None:
        return None
    return client["shipinsight"][collection_name]


def get_filter_metadata() -> dict:
    """
    Fetch dropdown option lists (countries, industries, etc.) from MongoDB.
    Returns empty dict if MongoDB is unavailable or collection is empty.
    """
    try:
        col = get_mongo_collection("filter_metadata")
        if col is None:
            return {}
        doc = col.find_one({}, {"_id": 0})
        return doc if doc else {}
    except Exception:
        return {}


def save_user_preferences(session_id: str, prefs: dict) -> None:
    """Persist user filter preferences to MongoDB (non-fatal).

    Two documents are written:
    1. A per-session document keyed by ``session_id`` (existing behaviour).
    2. A single ``"shared"`` document that always holds the *latest* prefs,
       so they can be loaded on the next browser session without knowing the
       previous session_id.
    """
    try:
        col = get_mongo_collection("user_preferences")
        if col is None:
            return
        # Use Thailand Standard Time (ICT, GMT+7) for all timestamps
        now = datetime.now(TZ_ICT)
        payload = {**prefs, "updated_at": now}
        # Per-session record (upsert)
        col.update_one(
            {"session_id": session_id},
            {"$set": payload},
            upsert=True,
        )
        # Shared "latest" record so cross-session pre-fill works
        col.update_one(
            {"session_id": "shared"},
            {"$set": payload},
            upsert=True,
        )
    except Exception:
        pass


def load_user_preferences(session_id: str) -> dict:
    """Load saved filter preferences from MongoDB."""
    try:
        col = get_mongo_collection("user_preferences")
        if col is None:
            return {}
        doc = col.find_one({"session_id": session_id}, {"_id": 0, "session_id": 0})
        return doc if doc else {}
    except Exception:
        return {}


def get_latest_today_preferences() -> dict:
    """Return the most recently saved filter preferences.

    Always returns the ``"shared"`` document written by ``save_user_preferences``
    if it exists, giving cross-session persistence.  Falls back to the most
    recently updated per-session document if no shared doc is found.

    Returns an empty dict when nothing is saved or MongoDB is offline.
    """
    try:
        col = get_mongo_collection("user_preferences")
        if col is None:
            return {}

        # 1. Prefer the shared "latest" document (updated from any session)
        shared = col.find_one(
            {"session_id": "shared"},
            {"_id": 0, "session_id": 0},
        )
        if shared:
            return shared

        # 2. Fallback: most recently updated per-session document
        docs = list(
            col.find(
                {"session_id": {"$ne": "shared"}},
                {"_id": 0, "session_id": 0},
            ).sort("updated_at", -1).limit(1)
        )
        return docs[0] if docs else {}
    except Exception:
        return {}


def submit_insight(payload: dict) -> bool:
    """Write-back a user-generated insight to MongoDB. Returns True on success."""
    try:
        col = get_mongo_collection("insights")
        if col is None:
            return False
        payload["submitted_at"] = datetime.now(TZ_ICT)
        col.insert_one(payload)
        return True
    except Exception:
        return False


def get_recent_insights(limit: int = 10) -> list:
    """Retrieve the most recently submitted insights from MongoDB."""
    try:
        col = get_mongo_collection("insights")
        if col is None:
            return []
        docs = list(
            col.find({}, {"_id": 0})
               .sort("submitted_at", -1)
               .limit(limit)
        )
        return docs
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────
# 4. Snowflake Data Load (full dataset)
# ──────────────────────────────────────────────────────────────

def _parse_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply date parsing and numeric coercion to a raw shipment DataFrame."""
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["YearMonth"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Quarter"] = df["Order Date"].dt.to_period("Q").astype(str)

    num_cols = [
        "Actual Weight (kg)", "Width (cm)", "Length (cm)", "Height (cm)",
        "Volumetric Weight (kg)", "Chargeable Weight (kg)",
        "RRP (Gross Price)", "Back Margin (Promotion Expense)",
        "Billing Price (ASP)", "Fuel Surcharge (FSC)", "Revenue",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=600, show_spinner="📡 Loading shipment data from Snowflake…")
def load_data_from_snowflake() -> pd.DataFrame:
    """
    Pull the complete shipment dataset from Snowflake and return a
    parsed Pandas DataFrame.
    """
    sql = """
        SELECT
            ORDER_ID AS "Order ID",
            ORDER_DATE AS "Order Date",
            CUSTOMER_ID AS "Customer ID",
            SALES_PERSON AS "Sales Person",
            INDUSTRY AS "Industry",
            SHIPMENT_STATUS AS "Shipment Status",
            "Inbound/Outbound",
            COUNTRY_OF_ORIGIN AS "Country of Origin",
            COUNTRY_OF_DESTINATION AS "Country of Destination",
            REGION_OF_ORIGIN AS "Region of Origin",
            REGION_OF_DESTINATION AS "Region of Destination",
            WEIGHT_TYPE AS "Weight Type",
            "Actual Weight (kg)",
            "Width (cm)",
            "Length (cm)",
            "Height (cm)",
            "Volumetric Weight (kg)",
            "Chargeable Weight (kg)",
            "RRP (Gross Price)",
            "Back Margin (Promotion Expense)",
            "Billing Price (ASP)",
            "Fuel Surcharge (FSC)",
            REVENUE AS "Revenue",
            PROMOTION_TYPE AS "Promotion Type",
            "FTB (First time buyer)"
        FROM DADS5001_SHIPINSIGHT.PUBLIC.SHIPMENT
        ORDER BY ORDER_DATE
    """
    df = run_snowflake_query(sql)
    return _parse_df(df)


# ──────────────────────────────────────────────────────────────
# 5. Sidebar Status Badge
# ──────────────────────────────────────────────────────────────

def render_data_source_badge() -> None:
    """
    Render connection-status badges for Snowflake and MongoDB.
    Call this inside the `with st.sidebar:` block in Home.py.
    """
    conns = init_connections()

    # Snowflake badge
    if conns["snowflake"] is not None:
        st.markdown(
            '<span style="font-size:0.72rem;font-weight:600;'
            'background:rgba(0,212,170,0.15);color:#00D4AA;'
            'border:1px solid rgba(0,212,170,0.3);border-radius:9999px;'
            'padding:3px 10px;">⬡ Live · Snowflake</span>',
            unsafe_allow_html=True,
        )

    # MongoDB badge
    if conns["mongo"] is not None:
        st.markdown(
            '<span style="font-size:0.72rem;font-weight:600;'
            'background:rgba(0,180,216,0.12);color:#00B4D8;'
            'border:1px solid rgba(0,180,216,0.3);border-radius:9999px;'
            'padding:3px 10px;">🍃 MongoDB · Connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="font-size:0.72rem;font-weight:600;'
            'background:rgba(139,149,165,0.12);color:#8B95A5;'
            'border:1px solid rgba(139,149,165,0.2);border-radius:9999px;'
            'padding:3px 10px;">🍃 MongoDB · Offline</span>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────
# 6. MongoDB Metadata Seed Utility
# ──────────────────────────────────────────────────────────────

def seed_filter_metadata_from_df(df: pd.DataFrame) -> None:
    """
    One-time utility: populate MongoDB filter_metadata collection from the
    loaded DataFrame. Safe to call when MongoDB is offline — silently skips.
    """
    try:
        col = get_mongo_collection("filter_metadata")
        if col is None:
            return
        if col.count_documents({}) > 0:
            return  # Already seeded

        metadata = {
            "countries_origin": sorted(df["Country of Origin"].dropna().unique().tolist()),
            "countries_destination": sorted(df["Country of Destination"].dropna().unique().tolist()),
            "industries": sorted(df["Industry"].dropna().unique().tolist()),
            "regions_origin": sorted(df["Region of Origin"].dropna().unique().tolist()),
            "regions_destination": sorted(df["Region of Destination"].dropna().unique().tolist()),
            "statuses": sorted(df["Shipment Status"].dropna().unique().tolist()),
            "directions": sorted(df["Inbound/Outbound"].dropna().unique().tolist()),
            "weight_types": sorted(df["Weight Type"].dropna().unique().tolist()),
            "seeded_at": datetime.now(TZ_ICT),
        }
        col.insert_one(metadata)
    except Exception:
        pass  # Non-critical
