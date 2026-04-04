import plotly.graph_objects as go
import plotly.express as px
from lib.theme import load_client_config


def _get_colors():
    cfg = load_client_config()
    return cfg["colors"]


def _rtl_layout(fig, title=""):
    colors = _get_colors()
    fig.update_layout(
        title=dict(text=title, x=1, xanchor="right", font=dict(size=16, color=colors["primary"])),
        font=dict(family="Arial", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=40),
        xaxis=dict(autorange="reversed"),
        legend=dict(x=1, xanchor="right"),
    )
    return fig


def daily_bar_chart(df, date_col, values, labels, colors_list, title=""):
    daily = df.groupby(date_col)[values[0]].sum().reset_index() if len(values) == 1 else None
    fig = go.Figure()
    for val, label, color in zip(values, labels, colors_list):
        daily_data = df.groupby(date_col)[val].sum().reset_index().sort_values(date_col)
        fig.add_trace(go.Bar(
            x=daily_data[date_col],
            y=daily_data[val],
            name=label,
            marker_color=color,
            opacity=0.85,
        ))
    fig.update_layout(
        barmode="group",
        font=dict(family="Arial", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=40),
        title=dict(text=title, x=1, xanchor="right", font=dict(size=14, color=_get_colors()["primary"])),
        legend=dict(x=0, xanchor="left"),
        xaxis=dict(type="date"),
    )
    return fig


def pie_chart(labels, values, colors_list, title=""):
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors_list),
        textinfo="label+percent",
        textposition="inside",
        hole=0.4,
    )])
    fig.update_layout(
        title=dict(text=title, x=1, xanchor="right", font=dict(size=14, color=_get_colors()["primary"])),
        font=dict(family="Arial", size=12),
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
    )
    return fig


def horizontal_bar(labels, values, colors_list, title=""):
    fig = go.Figure(data=[go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker_color=colors_list,
    )])
    fig.update_layout(
        title=dict(text=title, x=1, xanchor="right", font=dict(size=14, color=_get_colors()["primary"])),
        font=dict(family="Arial", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def comparison_bar(labels, values_a, values_b, name_a, name_b, color_a, color_b, title=""):
    fig = go.Figure()
    fig.add_trace(go.Bar(name=name_a, x=labels, y=values_a, marker_color=color_a))
    fig.add_trace(go.Bar(name=name_b, x=labels, y=values_b, marker_color=color_b))
    fig.update_layout(
        barmode="group",
        title=dict(text=title, x=1, xanchor="right", font=dict(size=14, color=_get_colors()["primary"])),
        font=dict(family="Arial", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=40),
        legend=dict(x=0, xanchor="left"),
    )
    return fig
