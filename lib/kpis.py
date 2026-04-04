import pandas as pd


def google_ads_kpis(df):
    if df.empty:
        return {}
    return {
        "clicks": int(df["clicks"].sum()),
        "impressions": int(df["impressions"].sum()),
        "cost": float(df["cost"].sum()),
        "conversions": int(df["conversions"].sum()),
        "ctr": float(df["clicks"].sum() / df["impressions"].sum() * 100) if df["impressions"].sum() > 0 else 0,
        "cost_per_conversion": float(df["cost"].sum() / df["conversions"].sum()) if df["conversions"].sum() > 0 else 0,
        "avg_cpc": float(df["cost"].sum() / df["clicks"].sum()) if df["clicks"].sum() > 0 else 0,
    }


def meta_ads_kpis(df):
    if df.empty:
        return {}
    results = float(df["results"].sum()) if "results" in df.columns else 0
    spend = float(df["spend"].sum()) if "spend" in df.columns else 0
    impressions = int(df["impressions"].sum()) if "impressions" in df.columns else 0
    reach = int(df["reach"].sum()) if "reach" in df.columns else 0
    return {
        "results": int(results),
        "spend": spend,
        "impressions": impressions,
        "reach": reach,
        "cost_per_result": spend / results if results > 0 else 0,
        "frequency": impressions / reach if reach > 0 else 0,
    }


def ga4_kpis(df):
    if df.empty:
        return {}
    return {
        "sessions": int(df["sessions"].sum()),
        "engaged_sessions": int(df["engaged_sessions"].sum()),
        "engagement_rate": float(df["engaged_sessions"].sum() / df["sessions"].sum() * 100) if df["sessions"].sum() > 0 else 0,
        "key_events": int(df["key_events"].sum()) if "key_events" in df.columns else 0,
        "total_revenue": float(df["total_revenue"].sum()) if "total_revenue" in df.columns else 0,
    }


def social_facebook_kpis(df):
    if df.empty:
        return {}
    total_posts = len(df)
    total_likes = int(df["likes"].sum()) if "likes" in df.columns else 0
    total_comments = int(df["comments"].sum()) if "comments" in df.columns else 0
    total_shares = int(df["shares"].sum()) if "shares" in df.columns else 0
    total_engagement = int(df["engagement"].sum()) if "engagement" in df.columns else 0
    avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
    return {
        "total_posts": total_posts,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "total_engagement": total_engagement,
        "avg_engagement_per_post": round(avg_engagement, 1),
    }


def social_instagram_kpis(df):
    if df.empty:
        return {}
    total_posts = len(df)
    total_likes = int(df["likes"].sum()) if "likes" in df.columns else 0
    total_comments = int(df["comments"].sum()) if "comments" in df.columns else 0
    total_shares = int(df["shares"].sum()) if "shares" in df.columns else 0
    total_saved = int(df["saved"].sum()) if "saved" in df.columns else 0
    total_engagement = int(df["engagement"].sum()) if "engagement" in df.columns else 0
    avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
    return {
        "total_posts": total_posts,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "total_saved": total_saved,
        "total_engagement": total_engagement,
        "avg_engagement_per_post": round(avg_engagement, 1),
    }


def unified_kpis(google_kpis, meta_kpis, ga4_kpis_dict, fb_kpis, ig_kpis):
    """Combined executive dashboard KPIs across all platforms."""
    # Active campaigns: count of unique campaigns from raw data is not available
    # in KPI dicts, so we count non-empty platform KPIs as active sources
    google_spend = google_kpis.get("cost", 0)
    meta_spend = meta_kpis.get("spend", 0)
    total_spend = google_spend + meta_spend

    fb_engagement = fb_kpis.get("total_engagement", 0)
    ig_engagement = ig_kpis.get("total_engagement", 0)
    meta_results = meta_kpis.get("results", 0)
    total_engagement = fb_engagement + ig_engagement

    total_sessions = ga4_kpis_dict.get("sessions", 0)

    return {
        "total_spend": total_spend,
        "google_spend": google_spend,
        "meta_spend": meta_spend,
        "total_engagement": total_engagement,
        "fb_engagement": fb_engagement,
        "ig_engagement": ig_engagement,
        "total_sessions": total_sessions,
        "total_clicks": google_kpis.get("clicks", 0) + meta_kpis.get("results", 0),
        "total_conversions": google_kpis.get("conversions", 0),
        "total_key_events": ga4_kpis_dict.get("key_events", 0),
        "total_revenue": ga4_kpis_dict.get("total_revenue", 0),
    }


def overview_kpis(google_df, meta_df, ga4_df):
    g = google_ads_kpis(google_df)
    m = meta_ads_kpis(meta_df)
    a = ga4_kpis(ga4_df)
    total_spend = g.get("cost", 0) + m.get("spend", 0)
    total_clicks = g.get("clicks", 0) + m.get("results", 0)
    total_conversions = g.get("conversions", 0)
    return {
        "total_spend": total_spend,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_sessions": a.get("sessions", 0),
        "total_key_events": a.get("key_events", 0),
        "total_revenue": a.get("total_revenue", 0),
        "avg_cpc": total_spend / total_clicks if total_clicks > 0 else 0,
        "cost_per_conversion": total_spend / total_conversions if total_conversions > 0 else 0,
    }
