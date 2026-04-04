import streamlit as st
import pandas as pd
from lib.theme import inject_rtl_css, format_currency, format_number, load_client_config
from lib.data_loader import load_meta_ads, get_date_range, filter_by_date
from lib.kpis import meta_ads_kpis
from lib.charts import daily_bar_chart, pie_chart

st.set_page_config(page_title="Meta Ads - יקב טוליפ", page_icon="📱", layout="wide")
inject_rtl_css()
colors = load_client_config()["colors"]

df = load_meta_ads()

if df.empty:
    st.warning("אין נתוני Meta Ads זמינים")
    st.stop()

# Header
campaigns = df["campaign_name"].dropna().unique() if "campaign_name" in df.columns else []
campaign_list = ", ".join(campaigns[:3])
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1877f2, #0d5bbf); color: white; border-radius: 14px;
    padding: 20px 28px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <h2 style="color: white; margin: 0;">📱 קמפיינים Meta Ads</h2>
        <p style="opacity: 0.85; margin-top: 5px;">{campaign_list}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Date filter
min_date, max_date = get_date_range(df)
if min_date is not None:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start = st.date_input("מתאריך", value=min_date, key="meta_start")
    with col_d2:
        end = st.date_input("עד תאריך", value=max_date, key="meta_end")
    filtered = filter_by_date(df, start, end)
else:
    filtered = df

kpis = meta_ads_kpis(filtered)

# KPI Cards
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("תוצאות (Results)", format_number(kpis["results"]))
with c2:
    st.metric("סה״כ הוצאה", format_currency(kpis["spend"]))
with c3:
    st.metric("עלות לתוצאה", format_currency(kpis["cost_per_result"]))
with c4:
    st.metric("חשיפות", format_number(kpis["impressions"]))
with c5:
    st.metric("Reach", format_number(kpis["reach"]))

st.markdown("---")

# Daily chart
if "date" in filtered.columns:
    daily = filtered.groupby("date").agg(
        results=("results", "sum"),
        spend=("spend", "sum"),
    ).reset_index()

    fig = daily_bar_chart(
        daily, "date",
        values=["results", "spend"],
        labels=["תוצאות", "הוצאה (₪)"],
        colors_list=[colors["meta"], "#42b72a"],
        title="גרף יומי – תוצאות והוצאה",
    )
    st.plotly_chart(fig, use_container_width=True)

# Campaign breakdown + Age breakdown
left, right = st.columns(2)

with left:
    st.markdown("### ביצועים לפי קמפיין")
    if "campaign_name" in filtered.columns:
        campaign_data = filtered.groupby("campaign_name").agg(
            spend=("spend", "sum"),
            results=("results", "sum"),
            impressions=("impressions", "sum"),
            reach=("reach", "sum"),
        ).reset_index()
        campaign_data["cost_per_result"] = (campaign_data["spend"] / campaign_data["results"]).round(2).replace([float("inf")], 0)
        campaign_data = campaign_data.sort_values("spend", ascending=False)
        campaign_data.columns = ["קמפיין", "הוצאה", "תוצאות", "חשיפות", "ריצ'", "עלות/תוצאה"]
        st.dataframe(campaign_data, use_container_width=True, hide_index=True)

with right:
    st.markdown("### ביצועים לפי גיל")
    if "age" in filtered.columns:
        age_data = filtered.groupby("age").agg(
            results=("results", "sum"),
            spend=("spend", "sum"),
        ).reset_index()
        age_data = age_data[age_data["age"] != "Unknown"]
        age_data = age_data.sort_values("results", ascending=False)
        if not age_data.empty:
            fig = pie_chart(
                labels=age_data["age"].tolist(),
                values=age_data["results"].tolist(),
                colors_list=[colors["meta"], "#42b72a", colors["warning"], colors["danger"], "#9c27b0", "#ff9800"],
                title="תוצאות לפי קבוצת גיל",
            )
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Ad Set breakdown
st.markdown("### ביצועים לפי אד סט")
if "ad_set_name" in filtered.columns:
    adset_data = filtered.groupby(["campaign_name", "ad_set_name"]).agg(
        spend=("spend", "sum"),
        results=("results", "sum"),
        impressions=("impressions", "sum"),
        reach=("reach", "sum"),
    ).reset_index()
    adset_data["cost_per_result"] = (adset_data["spend"] / adset_data["results"]).round(2).replace([float("inf")], 0)
    adset_data = adset_data.sort_values("spend", ascending=False)
    adset_data.columns = ["קמפיין", "אד סט", "הוצאה", "תוצאות", "חשיפות", "ריצ'", "עלות/תוצאה"]
    st.dataframe(adset_data, use_container_width=True, hide_index=True)

# Stats
st.markdown("---")
left2, right2 = st.columns(2)
with left2:
    days = filtered["date"].nunique() if "date" in filtered.columns else 1
    avg_spend = kpis["spend"] / days if days > 0 else 0
    avg_results = kpis["results"] / days if days > 0 else 0
    st.metric("ימי קמפיין", str(days))
    st.metric("ממוצע הוצאה/יום", format_currency(avg_spend))
with right2:
    st.metric("ממוצע תוצאות/יום", format_number(avg_results))
    st.metric("Frequency", f'{kpis["frequency"]:.2f}x')

# Failure points
with st.expander("⚠️ נקודות כשל"):
    st.markdown("""
    - **פער קליקים vs סשנים**: Meta מדווחת יותר תוצאות מ-GA4 (פער אופייני של 40-60%).
    - **Attribution**: ברירת מחדל 7-day click / 1-day view - משפיע על ספירת המרות.
    - **Result Type משתנה**: סוג התוצאה (Landing page views, Link clicks וכו') יכול להשתנות בין קמפיינים.
    - **פורמט CSV**: אם Meta ישנו את שמות העמודות, צריך לעדכן את המיפוי ב-data_loader.py.
    """)
