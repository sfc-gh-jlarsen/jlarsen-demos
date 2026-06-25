"""
Demo 2a: Governed Plant Dashboard (WITHOUT Semantic View)
=========================================================
Multi-page deployed Streamlit app with direct SQL queries.
Shows the dashboard works without a semantic view — but highlights why you'd want one.

Runtime: Container (Deployed)
Persona: Plant Manager
"""

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.synthetic_data import (
    LINES,
    get_changeover_history,
    get_delivery_data,
    get_issues,
    get_line_utilization,
    get_oee_data,
    get_on_time_delivery_trend,
)

st.set_page_config(page_title="Plant Performance Dashboard", layout="wide")

# --- Page Selection ---
page = st.sidebar.radio("Navigation", ["Plant Overview", "Drill Down"])

# ===========================
# PAGE 1: Plant Overview
# ===========================
if page == "Plant Overview":
    st.title("Detroit Manufacturing Center — Performance Dashboard")

    # In production, this would be direct SQL (no semantic view):
    # session.sql("""
    #   SELECT DATE, AVG(AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT) AS OEE
    #   FROM MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS
    #   WHERE PLANT_ID = 'DET01' AND DATE >= DATEADD(week, -8, CURRENT_DATE())
    #   GROUP BY DATE ORDER BY DATE
    # """)
    # NOTE: OEE formula is hardcoded here — what if Austin defines it differently?

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
    current_otd = otd_df.iloc[-1]["on_time_delivery_pct"]
    prev_otd = otd_df.iloc[-2]["on_time_delivery_pct"]
    current_throughput = int(latest_week["good_units"].sum() / 7)
    prev_throughput = int(prev_week["good_units"].sum() / 7)
    active_issues = len(issues_df[issues_df["status"] == "Open"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("OEE", f"{current_oee:.1f}%", f"{current_oee - prev_oee:+.1f} pts")
    col2.metric("On-Time Delivery", f"{current_otd:.1f}%", f"{current_otd - prev_otd:+.1f} pts")
    col3.metric("Throughput (units/day)", f"{current_throughput:,}", f"{current_throughput - prev_throughput:+d}")
    col4.metric("Active Issues", active_issues)

    st.divider()

    # --- OEE Trend + Breakdown ---
    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("OEE Trend (8 weeks)")
        weekly_oee = oee_df.groupby(
            oee_df["date"].apply(lambda d: d - np.timedelta64(d.weekday(), "D"))
        )["oee"].mean().reset_index()
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

    # --- OTD Trend + At-Risk ---
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

    # --- Line Utilization ---
    st.subheader("Production Line Utilization")
    fig = go.Figure(go.Bar(
        y=util_df["production_line"],
        x=util_df["utilization_pct"],
        orientation="h",
        marker_color=[
            "#4CAF50" if v >= 80 else "#FF9800" if v >= 60 else "#F44336"
            for v in util_df["utilization_pct"]
        ],
        text=[f"{v:.0f}%" for v in util_df["utilization_pct"]],
        textposition="auto",
    ))
    fig.update_layout(xaxis_title="Utilization %", xaxis_range=[0, 100], height=280, margin=dict(t=10, l=200))
    st.plotly_chart(fig, use_container_width=True)

    # Demo callout
    st.caption(
        "Note: SQL queries use hardcoded OEE formula (Availability x Performance x Quality). "
        "Different plants may define this differently — Semantic Views solve this."
    )

# ===========================
# PAGE 2: Drill Down
# ===========================
else:
    st.title("Production Line Drill Down")

    selected_line = st.selectbox("Select Production Line", LINES)

    # Daily production
    st.subheader(f"Daily Production — {selected_line}")
    oee_df = get_oee_data(weeks=2)
    line_data = oee_df[oee_df["production_line"] == selected_line].tail(14).copy()
    line_data["target_units"] = 150
    fig = px.bar(line_data, x="date", y="good_units", labels={"good_units": "Good Units"})
    fig.add_scatter(x=line_data["date"], y=line_data["target_units"],
                    mode="lines", name="Target", line=dict(color="red", dash="dash"))
    fig.update_layout(height=300, margin=dict(t=20), xaxis_title="", yaxis_title="Units")
    st.plotly_chart(fig, use_container_width=True)

    # Issue log
    st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
    issues_df = get_issues()
    line_issues = issues_df[issues_df["production_line"] == selected_line][
        ["issue_id", "type", "description", "severity", "status", "created_at"]
    ]
    if line_issues.empty:
        st.info("No issues recorded for this line in the last 7 days.")
    else:
        st.dataframe(line_issues, use_container_width=True, hide_index=True)

    # Changeover history
    st.subheader(f"Changeover History — {selected_line}")
    changeover_df = get_changeover_history()
    line_changeovers = changeover_df[changeover_df["production_line"] == selected_line][
        ["changeover_time", "duration_minutes", "from_product", "to_product"]
    ]
    if line_changeovers.empty:
        st.info("No changeovers recorded.")
    else:
        avg_duration = line_changeovers["duration_minutes"].mean()
        st.metric("Average Changeover Time", f"{avg_duration:.0f} min")
        st.dataframe(line_changeovers, use_container_width=True, hide_index=True)
