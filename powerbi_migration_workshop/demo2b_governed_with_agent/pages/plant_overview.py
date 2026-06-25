"""
Plant Overview page — KPIs, OEE trends, delivery metrics, line utilization.
Queries are expressed as semantic view references (comments show raw SQL equivalent).
"""

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from data.synthetic_data import (
    get_delivery_data,
    get_issues,
    get_line_utilization,
    get_oee_data,
    get_on_time_delivery_trend,
)

st.title("Detroit Manufacturing Center — Performance Dashboard")

# --- Load data ---
# In production, these would be:
#   session.sql("SELECT * FROM TABLE(SEMANTIC_VIEW('manufacturing_operations', ...))")
# Using synthetic data for standalone demo.
oee_df = get_oee_data(weeks=8)
otd_df = get_on_time_delivery_trend(weeks=8)
delivery_df = get_delivery_data()
issues_df = get_issues()
util_df = get_line_utilization()

# --- KPI Row ---
latest_week = oee_df[oee_df["date"] >= oee_df["date"].max() - np.timedelta64(6, "D")]
prev_week = oee_df[
    (oee_df["date"] >= oee_df["date"].max() - np.timedelta64(13, "D"))
    & (oee_df["date"] < oee_df["date"].max() - np.timedelta64(6, "D"))
]

current_oee = latest_week["oee"].mean() * 100
prev_oee = prev_week["oee"].mean() * 100
oee_delta = current_oee - prev_oee

current_otd = otd_df.iloc[-1]["on_time_delivery_pct"]
prev_otd = otd_df.iloc[-2]["on_time_delivery_pct"]
otd_delta = current_otd - prev_otd

current_throughput = int(latest_week["good_units"].sum() / 7)
prev_throughput = int(prev_week["good_units"].sum() / 7)
throughput_delta = current_throughput - prev_throughput

active_issues = len(issues_df[issues_df["status"] == "Open"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("OEE", f"{current_oee:.1f}%", f"{oee_delta:+.1f} pts")
col2.metric("On-Time Delivery", f"{current_otd:.1f}%", f"{otd_delta:+.1f} pts")
col3.metric("Throughput (units/day)", f"{current_throughput:,}", f"{throughput_delta:+d}")
col4.metric("Active Issues", active_issues)

st.divider()

# --- Charts Row 1: OEE Trend + Waterfall ---
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("OEE Trend (8 weeks)")
    weekly_oee = oee_df.groupby(oee_df["date"].apply(lambda d: d - np.timedelta64(d.weekday(), "D")))[
        "oee"
    ].mean().reset_index()
    weekly_oee.columns = ["week", "oee"]
    weekly_oee["oee_pct"] = weekly_oee["oee"] * 100

    fig = px.line(weekly_oee, x="week", y="oee_pct", markers=True)
    fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Target: 85%")
    fig.update_layout(yaxis_title="OEE %", xaxis_title="", height=300, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("OEE Breakdown (Current)")
    avg_a = latest_week["availability_pct"].mean() * 100
    avg_p = latest_week["performance_pct"].mean() * 100
    avg_q = latest_week["quality_pct"].mean() * 100

    fig = go.Figure(go.Bar(
        x=["Availability", "Performance", "Quality"],
        y=[avg_a, avg_p, avg_q],
        marker_color=["#2196F3", "#4CAF50", "#FF9800"],
        text=[f"{v:.1f}%" for v in [avg_a, avg_p, avg_q]],
        textposition="auto",
    ))
    fig.update_layout(yaxis_title="%", yaxis_range=[0, 100], height=300, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

# --- Charts Row 2: OTD Trend + At-Risk Orders ---
chart3, chart4 = st.columns(2)

with chart3:
    st.subheader("On-Time Delivery Trend")
    fig = px.line(otd_df, x="week_start", y="on_time_delivery_pct", markers=True)
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Target: 95%")
    fig.update_layout(yaxis_title="OTD %", xaxis_title="", height=300, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

with chart4:
    st.subheader("At-Risk Orders")
    at_risk = delivery_df[delivery_df["on_time"] == False][
        ["wo_id", "product", "promise_date", "days_until_due", "risk_reason"]
    ]
    st.dataframe(at_risk, use_container_width=True, hide_index=True)

# --- Row 3: Line Utilization ---
st.subheader("Production Line Utilization")


def _color(pct):
    if pct >= 80:
        return "#4CAF50"
    elif pct >= 60:
        return "#FF9800"
    return "#F44336"


fig = go.Figure(go.Bar(
    y=util_df["production_line"],
    x=util_df["utilization_pct"],
    orientation="h",
    marker_color=[_color(v) for v in util_df["utilization_pct"]],
    text=[f"{v:.0f}%" for v in util_df["utilization_pct"]],
    textposition="auto",
))
fig.update_layout(xaxis_title="Utilization %", xaxis_range=[0, 100], height=280, margin=dict(t=10, l=200))
st.plotly_chart(fig, use_container_width=True)
