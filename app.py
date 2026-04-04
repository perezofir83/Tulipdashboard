import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from lib.theme import inject_rtl_css, load_client_config, format_currency, format_number
from lib.data_loader import (
    load_google_ads,
    load_meta_ads,
    load_ga4,
    load_social_facebook,
    load_social_instagram,
    filter_by_date,
)
from lib.kpis import (
    google_ads_kpis,
    meta_ads_kpis,
    ga4_kpis,
    social_facebook_kpis,
    social_instagram_kpis,
    unified_kpis,
)
from lib.charts import pie_chart, horizontal_bar, comparison_bar

st.set_page_config(
    page_title="דשבורד שיווק - יקב טוליפ",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_rtl_css()

cfg = load_client_config()
client = cfg["client"]
colors = cfg["colors"]

# --- Always last 7 days ---
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
date_range_str = f"{start_date.strftime('%d/%m/%Y')} – {end_date.strftime('%d/%m/%Y')}"

# --- Sidebar ---
st.sidebar.markdown(f"## 🍷 {client['name_he']}")
st.sidebar.markdown("---")
st.sidebar.markdown("**דשבורד ניהול שיווק**")
st.sidebar.markdown("סקירה כללית")
st.sidebar.markdown(f"📅 7 ימים אחרונים")

# --- Load all data & filter to 7 days ---
google_df = filter_by_date(load_google_ads(), start_date, end_date)
meta_df = filter_by_date(load_meta_ads(), start_date, end_date)
ga4_df = filter_by_date(load_ga4(), start_date, end_date)
fb_df = filter_by_date(load_social_facebook(), start_date, end_date)
ig_df = filter_by_date(load_social_instagram(), start_date, end_date)

# --- Compute KPIs ---
g_kpis = google_ads_kpis(google_df)
m_kpis = meta_ads_kpis(meta_df)
a_kpis = ga4_kpis(ga4_df)
fb_kpis = social_facebook_kpis(fb_df)
ig_kpis = social_instagram_kpis(ig_df)
u_kpis = unified_kpis(g_kpis, m_kpis, a_kpis, fb_kpis, ig_kpis)

# Active campaigns count
active_campaigns = 0
if not google_df.empty and "campaign_name" in google_df.columns:
    active_campaigns += google_df["campaign_name"].nunique()
if not meta_df.empty and "campaign_name" in meta_df.columns:
    active_campaigns += meta_df["campaign_name"].nunique()

# --- Header ---
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1a3c5e, #2e6da4); color: white; border-radius: 14px;
    padding: 28px 32px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h1 style="color: white; margin: 0; font-size: 1.7rem;">דשבורד שיווק - {client['name_he']}</h1>
        <p style="opacity: 0.85; margin-top: 6px;">סקירה מנהלית של כל ערוצי השיווק</p>
        <p style="opacity: 0.7; margin-top: 4px; font-size: 0.85rem;">📅 7 ימים אחרונים: {date_range_str}</p>
    </div>
    <div style="background: #ff8c00; color: white; padding: 6px 18px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
        סקירה כללית
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TOP ROW – Executive KPI Cards
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("קמפיינים פעילים", format_number(active_campaigns), help="Google Ads + Meta Ads")
with col2:
    st.metric("הוצאה כוללת", format_currency(u_kpis["total_spend"]), help="Google Ads + Meta Ads")
with col3:
    st.metric("מעורבות כוללת", format_number(u_kpis["total_engagement"]), help="לייקים + תגובות + שיתופים (FB + IG)")
with col4:
    st.metric("סשנים באתר", format_number(u_kpis["total_sessions"]), help="GA4")

st.markdown("---")

# ============================================================
# SECOND ROW – Spend pie + Social engagement bar
# ============================================================
left, right = st.columns(2)

with left:
    google_spend = u_kpis["google_spend"]
    meta_spend = u_kpis["meta_spend"]
    if google_spend > 0 or meta_spend > 0:
        fig = pie_chart(
            labels=["Google Ads", "Meta Ads"],
            values=[google_spend, meta_spend],
            colors_list=[colors["google"], colors["meta"]],
            title="חלוקת הוצאה לפי פלטפורמה",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתוני הוצאה ב-7 ימים אחרונים")

with right:
    fb_eng = fb_kpis.get("total_engagement", 0)
    ig_eng = ig_kpis.get("total_engagement", 0)
    if fb_eng > 0 or ig_eng > 0:
        fig = horizontal_bar(
            labels=["פייסבוק", "אינסטגרם"],
            values=[fb_eng, ig_eng],
            colors_list=[colors["meta"], colors["instagram"]],
            title="השוואת מעורבות סושיאל",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתוני מעורבות ב-7 ימים אחרונים")

st.markdown("---")

# ============================================================
# THIRD ROW – Traffic sources from GA4
# ============================================================
st.markdown("### מקורות תנועה מובילים (GA4)")
if not ga4_df.empty and "session_source_medium" in ga4_df.columns:
    source_sessions = (
        ga4_df.groupby("session_source_medium")["sessions"]
        .sum()
        .sort_values(ascending=True)
    )
    top_sources = source_sessions.tail(10)
    source_colors = [colors["secondary"]] * len(top_sources)

    fig = horizontal_bar(
        labels=top_sources.index.tolist(),
        values=top_sources.values.tolist(),
        colors_list=source_colors,
        title="סשנים לפי מקור תנועה – טופ 10",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("אין נתוני GA4 ב-7 ימים אחרונים")

st.markdown("---")

# ============================================================
# FOURTH ROW – Top posts tables
# ============================================================
left_t, right_t = st.columns(2)

with left_t:
    st.markdown("### טופ 5 פוסטים בפייסבוק")
    if not fb_df.empty:
        top_fb = (
            fb_df.nlargest(5, "engagement")[["date", "post", "likes", "comments", "shares", "engagement"]]
            .copy()
        )
        top_fb["date"] = top_fb["date"].dt.strftime("%Y-%m-%d")
        top_fb.columns = ["תאריך", "פוסט", "לייקים", "תגובות", "שיתופים", "מעורבות"]
        top_fb["פוסט"] = top_fb["פוסט"].astype(str).str[:60] + "..."
        st.dataframe(top_fb, use_container_width=True, hide_index=True)
    else:
        st.info("אין פוסטים ב-7 ימים אחרונים")

with right_t:
    st.markdown("### טופ 5 פוסטים באינסטגרם")
    if not ig_df.empty:
        top_ig = (
            ig_df.nlargest(5, "engagement")[["date", "type", "post", "likes", "comments", "saved", "engagement"]]
            .copy()
        )
        top_ig["date"] = top_ig["date"].dt.strftime("%Y-%m-%d")
        top_ig.columns = ["תאריך", "סוג", "פוסט", "לייקים", "תגובות", "שמירות", "מעורבות"]
        top_ig["פוסט"] = top_ig["פוסט"].astype(str).str[:60] + "..."
        st.dataframe(top_ig, use_container_width=True, hide_index=True)
    else:
        st.info("אין פוסטים ב-7 ימים אחרונים")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #aaa; font-size: 0.8rem;'>"
    f"דשבורד שיווק | {client['name_he']} | 7 ימים אחרונים</div>",
    unsafe_allow_html=True,
)
