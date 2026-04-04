import streamlit as st
import pandas as pd
from lib.theme import inject_rtl_css, format_currency, format_number, load_client_config
from lib.data_loader import load_google_ads, get_date_range, filter_by_date
from lib.kpis import google_ads_kpis
from lib.charts import daily_bar_chart, pie_chart, horizontal_bar

st.set_page_config(page_title="Google Ads - יקב טוליפ", page_icon="🔍", layout="wide")
inject_rtl_css()
colors = load_client_config()["colors"]

df = load_google_ads()

if df.empty:
    st.warning("אין נתוני Google Ads זמינים")
    st.stop()

# Header
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1a3c5e, #2e6da4); color: white; border-radius: 14px;
    padding: 20px 28px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h2 style="color: white; margin: 0;">🔍 קמפיין Google Ads</h2>
        <p style="opacity: 0.85; margin-top: 5px;">יקב טוליפ | קמפיין: פסח 2025 | חיפוש</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Date filter
min_date, max_date = get_date_range(df)
col_d1, col_d2 = st.columns(2)
with col_d1:
    start = st.date_input("מתאריך", value=min_date, key="gads_start")
with col_d2:
    end = st.date_input("עד תאריך", value=max_date, key="gads_end")

filtered = filter_by_date(df, start, end)
kpis = google_ads_kpis(filtered)

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("קליקים", format_number(kpis["clicks"]))
with c2:
    st.metric("חשיפות", format_number(kpis["impressions"]))
with c3:
    st.metric("עלות להמרה", format_currency(kpis["cost_per_conversion"]))
with c4:
    st.metric("עלות כוללת", format_currency(kpis["cost"]))

st.markdown("---")

# Daily chart
fig = daily_bar_chart(
    filtered, "date",
    values=["clicks", "cost"],
    labels=["קליקים", "עלות (₪)"],
    colors_list=[colors["google"], colors["success"]],
    title="גרף יומי – קליקים ועלות",
)
st.plotly_chart(fig, use_container_width=True)

# Ad groups table + Device breakdown
left, right = st.columns([2, 1])

with left:
    st.markdown("### קבוצות מודעות (לפי עלות)")
    ad_groups = filtered.groupby("ad_group").agg(
        cost=("cost", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
    ).reset_index()
    ad_groups["ctr"] = (ad_groups["clicks"] / ad_groups["impressions"] * 100).round(2)
    ad_groups = ad_groups.sort_values("cost", ascending=False)
    ad_groups.columns = ["קבוצת מודעה", "עלות", "קליקים", "חשיפות", "CTR %"]
    st.dataframe(ad_groups, use_container_width=True, hide_index=True)

with right:
    st.markdown("### ביצועים לפי מכשיר")
    if "device" in filtered.columns:
        device_data = filtered.groupby("device")["clicks"].sum()
        device_map = {"mobile": "מובייל", "desktop": "מחשב", "tablet": "טאבלט"}
        device_labels = [device_map.get(d, d) for d in device_data.index]
        fig = pie_chart(
            labels=device_labels,
            values=device_data.values.tolist(),
            colors_list=[colors["google"], colors["success"], colors["warning"]],
            title="חלוקה לפי מכשיר",
        )
        st.plotly_chart(fig, use_container_width=True)

# Failure points
with st.expander("⚠️ נקודות כשל"):
    st.markdown("""
    - **שינוי פורמט CSV**: אם גוגל ישנה את שמות העמודות, הטעינה תיכשל. פתרון: בדיקת עמודות ב-data_loader.
    - **מטבע**: הנתונים מניחים שקלים. אם הקמפיין במטבע אחר, צריך התאמה.
    - **תאריכים חסרים**: ימים ללא נתונים ייראו כפערים בגרף.
    """)
