import pandas as pd
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data(ttl=3600)
def load_csv(filename):
    live_path = DATA_DIR / "live" / filename
    demo_path = DATA_DIR / "demo" / filename
    filepath = live_path if live_path.exists() else demo_path
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)
    return df


def load_google_ads():
    df = load_csv("google_ads.csv")
    if df.empty:
        return df
    # Normalize column names from Google Ads Script export
    col_map = {
        "Date": "date",
        "Campaign": "campaign_name",
        "Campaign status": "campaign_status",
        "Campaign type": "campaign_type",
        "Ad group": "ad_group",
        "Impressions": "impressions",
        "Clicks": "clicks",
        "Cost": "cost",
        "Conversions": "conversions",
        "Conv. value": "conv_value",
        "CTR": "ctr",
        "Avg. CPC": "avg_cpc",
        "Interactions": "interactions",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date", ascending=False)
    for col in ["impressions", "clicks", "cost", "conversions", "conv_value", "avg_cpc", "interactions"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # Parse CTR from "7.50%" format
    if "ctr" in df.columns:
        df["ctr"] = df["ctr"].astype(str).str.rstrip("%").apply(pd.to_numeric, errors="coerce").fillna(0)
    return df


def load_meta_ads():
    df = load_csv("meta_ads.csv")
    if df.empty:
        return df
    # Normalize Meta's real export column names
    col_map = {
        "Campaign name": "campaign_name",
        "Ad set name": "ad_set_name",
        "Ad name": "ad_name",
        "Day": "date",
        "Age": "age",
        "Reach": "reach",
        "Impressions": "impressions",
        "Frequency": "frequency",
        "Result type": "result_type",
        "Results": "results",
        "Amount spent (ILS)": "spend",
        "Cost per result": "cost_per_result",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date", ascending=False)
    # Drop summary rows (no campaign name)
    if "campaign_name" in df.columns:
        df = df.dropna(subset=["campaign_name"])
    # Convert numeric columns
    for col in ["reach", "impressions", "results", "spend", "cost_per_result", "frequency"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_ga4():
    df = load_csv("ga4.csv")
    if df.empty:
        return df
    # Normalize column names from GA4 Apps Script export
    col_map = {
        "Date": "date",
        "Session source / medium": "session_source_medium",
        "Sessions": "sessions",
        "Engaged sessions": "engaged_sessions",
        "Engagement rate": "engagement_rate",
        "Average engagement time per session": "avg_engagement_time_seconds",
        "Key events": "key_events",
        "Key event rate": "key_event_rate",
        "Events per session": "events_per_session",
        "Total revenue": "total_revenue",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date", ascending=False)
    for col in ["sessions", "engaged_sessions", "engagement_rate", "avg_engagement_time_seconds",
                 "key_events", "key_event_rate", "events_per_session", "total_revenue"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_social():
    return load_csv("social_organic.csv")


@st.cache_data(ttl=3600)
def load_social_facebook():
    df = load_csv("social_facebook.csv")
    if df.empty:
        return df
    # Normalize column names – CSV uses Title Case
    col_map = {
        "Date": "date",
        "Platform": "platform",
        "Post": "post",
        "Impressions": "impressions",
        "Reach": "reach",
        "Likes": "likes",
        "Comments": "comments",
        "Shares": "shares",
        "Clicks": "clicks",
        "Engagement": "engagement",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date", ascending=False)
    for col in ["impressions", "reach", "likes", "comments", "shares", "clicks", "engagement"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=3600)
def load_social_instagram():
    df = load_csv("social_instagram.csv")
    if df.empty:
        return df
    col_map = {
        "Date": "date",
        "Platform": "platform",
        "Type": "type",
        "Post": "post",
        "Impressions": "impressions",
        "Reach": "reach",
        "Likes": "likes",
        "Comments": "comments",
        "Shares": "shares",
        "Saved": "saved",
        "Engagement": "engagement",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date", ascending=False)
    for col in ["impressions", "reach", "likes", "comments", "shares", "saved", "engagement"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def get_date_range(df):
    if df.empty or "date" not in df.columns:
        return None, None
    return df["date"].min(), df["date"].max()


def filter_by_date(df, start_date, end_date):
    if df.empty or "date" not in df.columns:
        return df
    mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
    return df[mask]
