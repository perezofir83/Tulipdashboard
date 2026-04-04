import streamlit as st
import pandas as pd
from lib.theme import inject_rtl_css, format_number, load_client_config
from lib.data_loader import load_social_facebook, load_social_instagram, get_date_range, filter_by_date
from lib.kpis import social_facebook_kpis, social_instagram_kpis
from lib.charts import daily_bar_chart, comparison_bar

st.set_page_config(page_title="סושיאל - יקב טוליפ", page_icon="💬", layout="wide")
inject_rtl_css()
colors = load_client_config()["colors"]

fb_df_raw = load_social_facebook()
ig_df_raw = load_social_instagram()

if fb_df_raw.empty and ig_df_raw.empty:
    st.warning("אין נתוני סושיאל זמינים")
    st.stop()

# Header
st.markdown("""
<div style="background: linear-gradient(135deg, #c13584, #e1306c); color: white; border-radius: 14px;
    padding: 20px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0;">💬 סושיאל</h2>
    <p style="opacity: 0.9; margin-top: 5px;">פייסבוק + אינסטגרם | נתוני פוסטים</p>
</div>
""", unsafe_allow_html=True)

# Date filter
all_dates = []
if not fb_df_raw.empty and "date" in fb_df_raw.columns:
    fb_min, fb_max = get_date_range(fb_df_raw)
    if fb_min is not None:
        all_dates.extend([fb_min, fb_max])
if not ig_df_raw.empty and "date" in ig_df_raw.columns:
    ig_min, ig_max = get_date_range(ig_df_raw)
    if ig_min is not None:
        all_dates.extend([ig_min, ig_max])

if all_dates:
    min_date = min(all_dates)
    max_date = max(all_dates)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start = st.date_input("מתאריך", value=min_date, key="social_start")
    with col_d2:
        end = st.date_input("עד תאריך", value=max_date, key="social_end")
    fb_df = filter_by_date(fb_df_raw, start, end)
    ig_df = filter_by_date(ig_df_raw, start, end)
else:
    fb_df = fb_df_raw
    ig_df = ig_df_raw

has_fb = not fb_df.empty
has_ig = not ig_df.empty

# ============================================================
# KPI Cards per platform
# ============================================================
fb_kpis = social_facebook_kpis(fb_df) if has_fb else {}
ig_kpis = social_instagram_kpis(ig_df) if has_ig else {}

col_fb, col_ig = st.columns(2)

with col_fb:
    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 20px; border-top: 4px solid {colors['meta']};
        box-shadow: 0 2px 10px rgba(0,0,0,0.07); text-align: center;">
        <h3 style="color: {colors['meta']}; margin-bottom: 4px;">פייסבוק</h3>
    </div>
    """, unsafe_allow_html=True)
    if has_fb:
        m1, m2, m3 = st.columns(3)
        m1.metric("פוסטים", format_number(fb_kpis.get("total_posts", 0)))
        m2.metric("לייקים", format_number(fb_kpis.get("total_likes", 0)))
        m3.metric("מעורבות כוללת", format_number(fb_kpis.get("total_engagement", 0)))
        m4, m5, m6 = st.columns(3)
        m4.metric("תגובות", format_number(fb_kpis.get("total_comments", 0)))
        m5.metric("שיתופים", format_number(fb_kpis.get("total_shares", 0)))
        m6.metric("מעורבות ממוצעת / פוסט", str(fb_kpis.get("avg_engagement_per_post", 0)))
    else:
        st.info("אין נתוני פייסבוק")

with col_ig:
    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 20px; border-top: 4px solid {colors['instagram']};
        box-shadow: 0 2px 10px rgba(0,0,0,0.07); text-align: center;">
        <h3 style="color: {colors['instagram']}; margin-bottom: 4px;">אינסטגרם</h3>
    </div>
    """, unsafe_allow_html=True)
    if has_ig:
        m1, m2, m3 = st.columns(3)
        m1.metric("פוסטים", format_number(ig_kpis.get("total_posts", 0)))
        m2.metric("לייקים", format_number(ig_kpis.get("total_likes", 0)))
        m3.metric("מעורבות כוללת", format_number(ig_kpis.get("total_engagement", 0)))
        m4, m5, m6 = st.columns(3)
        m4.metric("תגובות", format_number(ig_kpis.get("total_comments", 0)))
        m5.metric("שמירות", format_number(ig_kpis.get("total_saved", 0)))
        m6.metric("מעורבות ממוצעת / פוסט", str(ig_kpis.get("avg_engagement_per_post", 0)))
    else:
        st.info("אין נתוני אינסטגרם")

st.markdown("---")

# ============================================================
# Combined engagement timeline
# ============================================================
st.markdown("### מגמת מעורבות לפי תאריך")

# Build combined daily engagement
frames = []
if has_fb:
    fb_daily = fb_df.groupby("date")["engagement"].sum().reset_index()
    fb_daily["platform"] = "פייסבוק"
    frames.append(fb_daily)
if has_ig:
    ig_daily = ig_df.groupby("date")["engagement"].sum().reset_index()
    ig_daily["platform"] = "אינסטגרם"
    frames.append(ig_daily)

if frames:
    combined = pd.concat(frames, ignore_index=True).sort_values("date")
    # Use comparison bar if both platforms present
    if has_fb and has_ig:
        # Merge on date for side-by-side
        fb_pivot = fb_daily.rename(columns={"engagement": "fb_eng"}).drop(columns=["platform"])
        ig_pivot = ig_daily.rename(columns={"engagement": "ig_eng"}).drop(columns=["platform"])
        merged = pd.merge(fb_pivot, ig_pivot, on="date", how="outer").fillna(0).sort_values("date")
        fig = comparison_bar(
            labels=merged["date"].dt.strftime("%d/%m"),
            values_a=merged["fb_eng"].tolist(),
            values_b=merged["ig_eng"].tolist(),
            name_a="פייסבוק",
            name_b="אינסטגרם",
            color_a=colors["meta"],
            color_b=colors["instagram"],
            title="מעורבות יומית – פייסבוק מול אינסטגרם",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Single platform bar
        platform_df = frames[0]
        color = colors["meta"] if has_fb else colors["instagram"]
        fig = daily_bar_chart(
            platform_df, "date",
            values=["engagement"],
            labels=["מעורבות"],
            colors_list=[color],
            title="מעורבות יומית",
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# Post-level breakdown tables
# ============================================================
tab_fb, tab_ig = st.tabs(["📘 פייסבוק – פירוט פוסטים", "📸 אינסטגרם – פירוט פוסטים"])

with tab_fb:
    if has_fb:
        display_fb = fb_df.copy()
        display_fb["date"] = display_fb["date"].dt.strftime("%Y-%m-%d")
        display_fb = display_fb.sort_values("engagement", ascending=False)
        display_fb = display_fb[["date", "post", "impressions", "reach", "likes", "comments", "shares", "clicks", "engagement"]]
        display_fb["post"] = display_fb["post"].astype(str).str[:80]
        display_fb.columns = ["תאריך", "פוסט", "חשיפות", "ריצ'", "לייקים", "תגובות", "שיתופים", "קליקים", "מעורבות"]
        st.dataframe(display_fb, use_container_width=True, hide_index=True)
    else:
        st.info("אין נתוני פייסבוק")

with tab_ig:
    if has_ig:
        display_ig = ig_df.copy()
        display_ig["date"] = display_ig["date"].dt.strftime("%Y-%m-%d")
        display_ig = display_ig.sort_values("engagement", ascending=False)
        display_ig = display_ig[["date", "type", "post", "impressions", "reach", "likes", "comments", "shares", "saved", "engagement"]]
        display_ig["post"] = display_ig["post"].astype(str).str[:80]
        display_ig.columns = ["תאריך", "סוג", "פוסט", "חשיפות", "ריצ'", "לייקים", "תגובות", "שיתופים", "שמירות", "מעורבות"]
        st.dataframe(display_ig, use_container_width=True, hide_index=True)
    else:
        st.info("אין נתוני אינסטגרם")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.info("🔮 **בקרוב**: מחקר מתחרים – פידים אוטומטיים של ביצועי מתחרים בסושיאל")

with st.expander("⚠️ נקודות כשל"):
    st.markdown("""
    - **נתונים ידניים**: סושיאל אורגני דורש Google Sheet ידני או Apps Script.
    - **API מוגבל**: API של Meta לנתונים אורגניים מוגבל ודורש הרשאות מיוחדות.
    - **חוסר עקביות**: פלטפורמות שונות מודדות "מעורבות" אחרת.
    """)
