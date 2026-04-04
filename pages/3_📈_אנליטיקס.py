import streamlit as st
import pandas as pd
from lib.theme import inject_rtl_css, format_currency, format_number, load_client_config
from lib.data_loader import load_ga4, get_date_range, filter_by_date
from lib.kpis import ga4_kpis
from lib.charts import horizontal_bar

st.set_page_config(page_title="GA4 Analytics - יקב טוליפ", page_icon="📈", layout="wide")
inject_rtl_css()
colors = load_client_config()["colors"]

df = load_ga4()

if df.empty:
    st.warning("אין נתוני GA4 זמינים")
    st.stop()

# Header
st.markdown("""
<div style="background: linear-gradient(135deg, #e37400, #f9ab00); color: white; border-radius: 14px;
    padding: 20px 28px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h2 style="color: white; margin: 0;">📈 Google Analytics 4 – מקורות תנועה</h2>
        <p style="opacity: 0.9; margin-top: 5px;">Tulip IL | Traffic Acquisition by Source/Medium</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Date filter
min_date, max_date = get_date_range(df)
col_d1, col_d2 = st.columns(2)
with col_d1:
    start = st.date_input("מתאריך", value=min_date, key="ga4_start")
with col_d2:
    end = st.date_input("עד תאריך", value=max_date, key="ga4_end")

filtered = filter_by_date(df, start, end)
kpis = ga4_kpis(filtered)

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("סה״כ סשנים", format_number(kpis["sessions"]))
with c2:
    st.metric("סה״כ Key Events", format_number(kpis["key_events"]))
with c3:
    st.metric("שיעור מעורבות", f'{kpis["engagement_rate"]:.1f}%')
with c4:
    st.metric("הכנסה מדידה", format_currency(kpis["total_revenue"]))

st.markdown("---")

# Chart + Table
left, right = st.columns([1, 2])

with left:
    st.markdown("### סשנים לפי מקור")
    source_data = filtered.groupby("session_source_medium").agg(
        sessions=("sessions", "sum"),
        engaged=("engaged_sessions", "sum"),
    ).sort_values("sessions", ascending=True)

    source_colors_map = {
        "google / cpc": colors["google"],
        "google / organic": colors["organic"],
        "(direct) / (none)": "#9e9e9e",
        "fb / paid": colors["meta"],
        "ig / paid": colors["instagram"],
        "an / paid": "#ff9800",
        "ig / social": "#c13584",
        "m.facebook.com / referral": "#3b5998",
    }
    bar_colors = [source_colors_map.get(s, colors["secondary"]) for s in source_data.index]

    fig = horizontal_bar(
        labels=source_data.index.tolist(),
        values=source_data["sessions"].tolist(),
        colors_list=bar_colors,
        title="סשנים לפי מקור",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### מקורות תנועה עיקריים")
    table_data = filtered.groupby("session_source_medium").agg(
        sessions=("sessions", "sum"),
        engaged_sessions=("engaged_sessions", "sum"),
        key_events=("key_events", "sum"),
        total_revenue=("total_revenue", "sum"),
    ).reset_index()

    table_data["engagement_rate"] = (table_data["engaged_sessions"] / table_data["sessions"] * 100).round(1)
    table_data = table_data.sort_values("sessions", ascending=False)

    display_df = table_data[["session_source_medium", "sessions", "engagement_rate", "key_events", "total_revenue"]].copy()
    display_df.columns = ["מקור / Medium", "סשנים", "Engagement %", "Key Events", "הכנסה ₪"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Push vs Pull insight
st.markdown("---")
st.markdown("""
<div style="background: linear-gradient(135deg, #fff3e0, #fbe9e7); border-radius: 12px; padding: 20px;
    border: 2px solid #ff6d00; margin-bottom: 20px;">
    <h3 style="color: #e65100; font-size: 1rem; font-weight: 700; margin-bottom: 10px;">
        ⚠️ נקודת תשומת לב – Push vs Pull Ads
    </h3>
    <p style="font-size: 0.88rem; color: #333; line-height: 1.8;">
        <strong>Pull Ads (Google Search)</strong> – המשתמש מחפש את המוצר בעצמו → Engagement גבוה, המרות טובות.<br>
        <strong>Push Ads (Facebook/Instagram)</strong> – המודעה מופיעה לפני שהמשתמש חיפש → Bounce מהיר, engagement נמוך.<br><br>
        הפתרון: Push Ads מצוינים ל-Awareness ו-Retargeting – לא לסגירת מכירה ישירה.
    </p>
</div>
""", unsafe_allow_html=True)

# Failure points
with st.expander("⚠️ נקודות כשל"):
    st.markdown("""
    - **GA4 לא שולח CSV במייל**: צריך Google Apps Script שמריץ API query ושולח CSV.
    - **Sampling**: GA4 עלול לדגום נתונים באתרים גדולים - המספרים עלולים להיות אומדנים.
    - **Attribution**: GA4 משתמש ב-data-driven attribution כברירת מחדל, שונה מ-Meta.
    """)
