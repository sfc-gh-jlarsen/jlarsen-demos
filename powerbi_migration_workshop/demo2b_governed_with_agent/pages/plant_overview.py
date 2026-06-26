# Plant Overview page using SEMANTIC_VIEW() queries for governed metrics
# Co-authored with CoCo
"""
Plant Overview page — KPIs, OEE trends, delivery metrics, line utilization.
Queries governed metrics via the SEMANTIC_VIEW() clause.
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Configuration ---
SV = "MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS"
PLANT_ID = "DET01"

conn = st.connection("snowflake")

st.title("Detroit Manufacturing Center — Performance Dashboard")

# --- Load data via SEMANTIC_VIEW() ---
oee_df = conn.query(f"""
    SELECT *
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS daily_production_metrics.plant_id,
                   daily_production_metrics.production_date,
                   daily_production_metrics.production_line
        METRICS daily_production_metrics.oee,
                daily_production_metrics.availability,
                daily_production_metrics.performance,
                daily_production_metrics.quality,
                daily_production_metrics.throughput
    )
    WHERE plant_id = '{PLANT_ID}'
      AND production_date >= DATEADD(week, -8, CURRENT_DATE())
    ORDER BY production_date
""")

issues_df = conn.query(f"""
    SELECT *
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS issues.issue_id,
                   issues.production_line,
                   issues.issue_type,
                   issues.severity,
                   issues.issue_status,
                   issues.created_at
    )
""")

util_df = conn.query(f"""
    SELECT *
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS daily_production_metrics.plant_id,
                   daily_production_metrics.production_date,
                   daily_production_metrics.production_line
        METRICS daily_production_metrics.availability
    )
    WHERE plant_id = '{PLANT_ID}'
      AND production_date >= DATEADD(day, -7, CURRENT_DATE())
""")

at_risk_df = conn.query(f"""
    SELECT *
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS work_orders.wo_id,
                   work_orders.product,
                   work_orders.due_date,
                   work_orders.status,
                   work_orders.material_status
    )
    WHERE material_status != 'Available'
""")

# --- KPI Row ---
if not oee_df.empty:
    latest_week = oee_df[oee_df["PRODUCTION_DATE"] >= oee_df["PRODUCTION_DATE"].max() - np.timedelta64(6, "D")]
    prev_week = oee_df[
        (oee_df["PRODUCTION_DATE"] >= oee_df["PRODUCTION_DATE"].max() - np.timedelta64(13, "D"))
        & (oee_df["PRODUCTION_DATE"] < oee_df["PRODUCTION_DATE"].max() - np.timedelta64(6, "D"))
    ]

    current_oee = latest_week["OEE"].mean() * 100
    prev_oee = prev_week["OEE"].mean() * 100 if not prev_week.empty else current_oee
    oee_delta = current_oee - prev_oee

    current_throughput = int(latest_week["THROUGHPUT"].sum() / max(latest_week["PRODUCTION_DATE"].nunique(), 1))
    prev_throughput = int(prev_week["THROUGHPUT"].sum() / max(prev_week["PRODUCTION_DATE"].nunique(), 1)) if not prev_week.empty else current_throughput
    throughput_delta = current_throughput - prev_throughput
else:
    current_oee = oee_delta = current_throughput = throughput_delta = 0

active_issues = len(issues_df[issues_df["ISSUE_STATUS"] == "Open"]) if not issues_df.empty else 0
at_risk_count = len(at_risk_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("OEE", f"{current_oee:.1f}%", f"{oee_delta:+.1f} pts")
col2.metric("At-Risk Orders", at_risk_count)
col3.metric("Throughput (units/day)", f"{current_throughput:,}", f"{throughput_delta:+d}")
col4.metric("Active Issues", active_issues)

st.divider()

# --- Charts Row 1: OEE Trend + Breakdown ---
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("OEE Trend (8 weeks)")
    if not oee_df.empty:
        weekly_oee = oee_df.groupby(
            oee_df["PRODUCTION_DATE"].apply(lambda d: d - np.timedelta64(d.weekday(), "D"))
        )["OEE"].mean().reset_index()
        weekly_oee.columns = ["week", "oee"]
        weekly_oee["oee_pct"] = weekly_oee["oee"] * 100

        fig = px.line(weekly_oee, x="week", y="oee_pct", markers=True)
        fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Target: 85%")
        fig.update_layout(yaxis_title="OEE %", xaxis_title="", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("OEE Breakdown (Current)")
    if not oee_df.empty:
        avg_a = latest_week["AVAILABILITY"].mean() * 100
        avg_p = latest_week["PERFORMANCE"].mean() * 100
        avg_q = latest_week["QUALITY"].mean() * 100

        fig = go.Figure(go.Bar(
            x=["Availability", "Performance", "Quality"],
            y=[avg_a, avg_p, avg_q],
            marker_color=["#2196F3", "#4CAF50", "#FF9800"],
            text=[f"{v:.1f}%" for v in [avg_a, avg_p, avg_q]],
            textposition="auto",
        ))
        fig.update_layout(yaxis_title="%", yaxis_range=[0, 100], height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

# --- Charts Row 2: At-Risk Orders + Issues ---
chart3, chart4 = st.columns(2)

with chart3:
    st.subheader("At-Risk Orders")
    if not at_risk_df.empty:
        st.dataframe(
            at_risk_df[["WO_ID", "PRODUCT", "DUE_DATE", "MATERIAL_STATUS"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No at-risk orders.")

with chart4:
    st.subheader("Open Issues by Severity")
    if not issues_df.empty:
        open_issues = issues_df[issues_df["ISSUE_STATUS"] == "Open"]
        if not open_issues.empty:
            sev_counts = open_issues.groupby("SEVERITY").size().reset_index(name="count")
            fig = px.bar(sev_counts, x="SEVERITY", y="count",
                         color="SEVERITY",
                         color_discrete_map={"High": "#F44336", "Medium": "#FF9800", "Low": "#4CAF50"})
            fig.update_layout(height=300, margin=dict(t=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- Row 3: Line Utilization ---
st.subheader("Production Line Utilization")


def _color(pct):
    if pct >= 80:
        return "#4CAF50"
    elif pct >= 60:
        return "#FF9800"
    return "#F44336"


if not util_df.empty:
    util_agg = util_df.groupby("PRODUCTION_LINE")["AVAILABILITY"].mean().reset_index()
    util_agg["UTILIZATION_PCT"] = util_agg["AVAILABILITY"] * 100
    fig = go.Figure(go.Bar(
        y=util_agg["PRODUCTION_LINE"],
        x=util_agg["UTILIZATION_PCT"],
        orientation="h",
        marker_color=[_color(v) for v in util_agg["UTILIZATION_PCT"]],
        text=[f"{v:.0f}%" for v in util_agg["UTILIZATION_PCT"]],
        textposition="auto",
    ))
    fig.update_layout(xaxis_title="Utilization %", xaxis_range=[0, 100], height=280, margin=dict(t=10, l=200))
    st.plotly_chart(fig, use_container_width=True)
