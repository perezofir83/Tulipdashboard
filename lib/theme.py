import toml
import streamlit as st
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_client_config():
    return toml.load(CONFIG_DIR / "client.toml")


def load_columns_config():
    return toml.load(CONFIG_DIR / "columns.toml")


def inject_rtl_css():
    cfg = load_client_config()
    colors = cfg["colors"]
    st.markdown(f"""
    <style>
        /* RTL + Hebrew */
        .stApp, .stMarkdown, .stDataFrame, [data-testid="stMetric"] {{
            direction: rtl;
            text-align: right;
        }}
        /* Header styling */
        h1, h2, h3 {{
            color: {colors["primary"]};
        }}
        /* Metric cards */
        [data-testid="stMetricValue"] {{
            direction: ltr;
            text-align: center;
        }}
        [data-testid="stMetricDelta"] {{
            direction: ltr;
        }}
        /* Tabs RTL fix */
        .stTabs [data-baseweb="tab-list"] {{
            direction: rtl;
        }}
        /* Sidebar RTL */
        [data-testid="stSidebar"] {{
            direction: rtl;
            text-align: right;
        }}
        /* Table RTL */
        .stDataFrame table {{
            direction: rtl;
        }}
        /* Custom colors */
        .kpi-google {{ border-right: 4px solid {colors["google"]}; }}
        .kpi-meta {{ border-right: 4px solid {colors["meta"]}; }}
        .kpi-organic {{ border-right: 4px solid {colors["organic"]}; }}
        /* Card style */
        .dashboard-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            margin-bottom: 16px;
        }}
    </style>
    """, unsafe_allow_html=True)


def format_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def format_currency(n, symbol="₪"):
    if abs(n) >= 1_000:
        return f"{symbol}{n:,.0f}"
    return f"{symbol}{n:,.2f}"
