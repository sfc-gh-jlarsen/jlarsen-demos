"""
Plant Overview page — KPIs, OEE trends, delivery metrics, line utilization.
Queries Snowflake via semantic view (or direct SQL with governed metric definitions).
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

conn = st.connection("snowflake")

st.title("Detroit Manufacturing Center — Performance Dashboard")

# --- Load data via SQL (backed by semantic view in production) ---
oee_df = conn.query("""
    SELECT PRODUCTION_DATE AS date, LINE_NAME AS production_line,
           AVAILABILITY_PCT, PERFORMANCE_PCT, QUALITY_PCT,
           OEE, GOOD_UNITS_PRODUCED AS good_units
    FROM MFG_SCHEDULING_REPORTING.ANALYTICS.DAILY_PRODUCTION_METRICS
    WHERE PLANT_ID = 'DET01'
      AND PRODUCTION_DATE >= DATEADD(week, -8, CURRENT_DATE())
    ORDER BY PRODUCTION_DATE
""")

otd_df = conn.query("""
    SELECT DATE_TRUNC('week', PROMISE_DATE) AS week_start,
           COUNT_IF(ON_TIME) / NULLIF(COUNT(*), 0) * 100 AS on_time_delivery_pct
    FROM MFG_SCHEDULING_REPORTING.RAW.DELIVERIES
    WHERE PLANT_ID = 'DET01'
    GROUP BY 1 ORDER BY 1
""")

delivery_df = conn.query("""
    SELECT WO_ID, PRODUCT_NAME AS product, PROMISE_DATE,
           DATEDIFF(day, CURRENT_DATE(), PROMISE_DATE) AS days_until_due,
           RISK_REASON, ON_TIME
    FROM MFG_SCHEDULING_REPORTING.RAW.DELIVERIES
    WHERE PLANT_ID = 'DET01'
""")

issues_df = conn.query("""
    SELECT ISSUE_ID, PRODUCTION_LINE, ISSUE_TYPE AS type,
           SEVERITY, STATUS, CREATED_AT
    FROM MFG_SCHEDULING_REPORTING.RAW.ISSUES
    WHERE PLANT_ID = 'DET01'
""")

util_df = conn.query("""
    SELECT LINE_NAME AS production_line,
           AVG(AVAILABILITY_PCT) * 100 AS utilization_pct
    FROM MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS
    WHERE PLANT_ID = 'DET01'
      AND PRODUCTION_DATE >= DATEADD(day, -7, CURRENT_DATE())
    GROUP BY LINE_NAME
""")

# --- KPI Row ---
latest_week = oee_df[oee_df["DATE"] >= oee_df["DATE"].max() - np.timedelta64(6, "D")]
prev_week = oee_df[
    (oee_df["DATE"] >= oee_df["DATE"].max() - np.timedelta64(13, "D"))
    & (oee_df["DATE"] < oee_df["DATE"].max() - np.timedelta64(6, "D"))
]

current_oee = latest_week["OEE"].mean() * 100
prev_oee = prev_week["OEE"].mean() * 100
oee_delta = current_oee - prev_oee

current_otd = otd_df.iloc[-1]["ON_TIME_DELIVERY_PCT"] if len(otd_df) > 0 else 0
prev_otd = otd_df.iloc[-2]["ON_TIME_DELIVERY_PCT"] if len(otd_df) > 1 else current_otd
otd_delta = current_otd - prev_otd

current_throughput = int(latest_week["GOOD_UNITS"].sum() / max(latest_week["DATE"].nunique(), 1))
prev_throughput = int(prev_week["GOOD_UNITS"].sum() / max(prev_week["DATE"].nunique(), 1))
throughput_delta = current_throughput - prev_throughput

active_issues = len(issues_df[issues_df["STATUS"] == "Open"])

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
    weekly_oee = oee_df.groupby(
        oee_df["DATE"].apply(lambda d: d - np.timedelta64(d.weekday(), "D"))
    )["OEE"].mean().reset_index()
    weekly_oee.columns = ["week", "oee"]
    weekly_oee["oee_pct"] = weekly_oee["oee"] * 100

    fig = px.line(weekly_oee, x="week", y="oee_pct", markers=True)
    fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Target: 85%")
    fig.update_layout(yaxis_title="OEE %", xaxis_title="", height=300, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("OEE Breakdown (Current)")
    avg_a = latest_week["AVAILABILITY_PCT"].mean() * 100
    avg_p = latest_week["PERFORMANCE_PCT"].mean() * 100
    avg_q = latest_week["QUALITY_PCT"].mean() * 100

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
    if not otd_df.empty:
        fig = px.line(otd_df, x="WEEK_START", y="ON_TIME_DELIVERY_PCT", markers=True)
        fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Target: 95%")
        fig.update_layout(yaxis_title="OTD %", xaxis_title="", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

with chart4:
    st.subheader("At-Risk Orders")
    at_risk = delivery_df[delivery_df["ON_TIME"] == False][
        ["WO_ID", "PRODUCT", "PROMISE_DATE", "DAYS_UNTIL_DUE", "RISK_REASON"]
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
    y=util_df["PRODUCTION_LINE"],
    x=util_df["UTILIZATION_PCT"],
    orientation="h",
    marker_color=[_color(v) for v in util_df["UTILIZATION_PCT"]],
    text=[f"{v:.0f}%" for v in util_df["UTILIZATION_PCT"]],
    textposition="auto",
))
fig.update_layout(xaxis_title="Utilization %", xaxis_range=[0, 100], height=280, margin=dict(t=10, l=200))
st.plotly_chart(fig, use_container_width=True)
