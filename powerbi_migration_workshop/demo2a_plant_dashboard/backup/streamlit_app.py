"""
Demo 2a: Governed Plant Dashboard (WITHOUT Semantic View)
=========================================================
Multi-page deployed Streamlit app with direct SQL queries.
Shows the dashboard works without a semantic view — but highlights why you'd want one.

Runtime: Container (Deployed)
Persona: Plant Manager
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Configuration ---
DATABASE = "MFG_SCHEDULING_REPORTING"
SCHEMA_RAW = f"{DATABASE}.RAW"
PLANT_ID = "DET01"

st.set_page_config(page_title="Plant Performance Dashboard", layout="wide")

conn = st.connection("snowflake")

# --- Page Selection ---
page = st.sidebar.radio("Navigation", ["Plant Overview", "Drill Down"])

# ===========================
# PAGE 1: Plant Overview
# ===========================
if page == "Plant Overview":
    st.title("Detroit Manufacturing Center — Performance Dashboard")

    # Direct SQL — OEE formula is hardcoded here.
    # NOTE: What if Austin defines OEE differently? That's why Semantic Views exist.
    oee_df = conn.query(
        f"""
        SELECT PRODUCTION_DATE AS date, LINE_NAME AS production_line,
               AVAILABILITY_PCT, PERFORMANCE_PCT, QUALITY_PCT,
               AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT AS oee,
               GOOD_UNITS_PRODUCED AS good_units, SCRAPPED_UNITS AS scrap_units,
               DOWNTIME_MINUTES
        FROM {SCHEMA_RAW}.DAILY_PRODUCTION_METRICS
        WHERE PLANT_ID = :1
          AND PRODUCTION_DATE >= DATEADD(week, -8, CURRENT_DATE())
        ORDER BY PRODUCTION_DATE
        """,
        params=[PLANT_ID],
    )

    otd_df = conn.query(
        f"""
        SELECT DATE_TRUNC('week', PROMISE_DATE) AS week_start,
               COUNT_IF(ON_TIME) / NULLIF(COUNT(*), 0) * 100 AS on_time_delivery_pct
        FROM {SCHEMA_RAW}.DELIVERIES
        WHERE PLANT_ID = :1
        GROUP BY 1 ORDER BY 1
        """,
        params=[PLANT_ID],
    )

    delivery_df = conn.query(
        f"""
        SELECT WO_ID, PRODUCT_NAME AS product, PROMISE_DATE,
               DATEDIFF(day, CURRENT_DATE(), PROMISE_DATE) AS days_until_due,
               RISK_REASON, ON_TIME
        FROM {SCHEMA_RAW}.DELIVERIES
        WHERE PLANT_ID = :1
        """,
        params=[PLANT_ID],
    )

    issues_df = conn.query(
        f"""
        SELECT ISSUE_ID, PRODUCTION_LINE, ISSUE_TYPE AS type, DESCRIPTION,
               SEVERITY, STATUS, CREATED_AT, RESOLVED_AT
        FROM {SCHEMA_RAW}.ISSUES
        WHERE PLANT_ID = :1
        """,
        params=[PLANT_ID],
    )

    util_df = conn.query(
        f"""
        SELECT LINE_NAME AS production_line,
               AVG(AVAILABILITY_PCT) * 100 AS utilization_pct
        FROM {SCHEMA_RAW}.DAILY_PRODUCTION_METRICS
        WHERE PLANT_ID = :1
          AND PRODUCTION_DATE >= DATEADD(day, -7, CURRENT_DATE())
        GROUP BY LINE_NAME
        """,
        params=[PLANT_ID],
    )

    # --- KPI Row ---
    latest_week = oee_df[oee_df["DATE"] >= oee_df["DATE"].max() - np.timedelta64(6, "D")]
    prev_week = oee_df[
        (oee_df["DATE"] >= oee_df["DATE"].max() - np.timedelta64(13, "D"))
        & (oee_df["DATE"] < oee_df["DATE"].max() - np.timedelta64(6, "D"))
    ]

    current_oee = latest_week["OEE"].mean() * 100
    prev_oee = prev_week["OEE"].mean() * 100
    current_otd = otd_df.iloc[-1]["ON_TIME_DELIVERY_PCT"] if len(otd_df) > 0 else 0
    prev_otd = otd_df.iloc[-2]["ON_TIME_DELIVERY_PCT"] if len(otd_df) > 1 else current_otd
    current_throughput = int(latest_week["GOOD_UNITS"].sum() / max(latest_week["DATE"].nunique(), 1))
    prev_throughput = int(prev_week["GOOD_UNITS"].sum() / max(prev_week["DATE"].nunique(), 1))
    active_issues = len(issues_df[issues_df["STATUS"] == "Open"])

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

    # --- OTD Trend + At-Risk ---
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

    # --- Line Utilization ---
    st.subheader("Production Line Utilization")
    fig = go.Figure(go.Bar(
        y=util_df["PRODUCTION_LINE"],
        x=util_df["UTILIZATION_PCT"],
        orientation="h",
        marker_color=[
            "#4CAF50" if v >= 80 else "#FF9800" if v >= 60 else "#F44336"
            for v in util_df["UTILIZATION_PCT"]
        ],
        text=[f"{v:.0f}%" for v in util_df["UTILIZATION_PCT"]],
        textposition="auto",
    ))
    fig.update_layout(xaxis_title="Utilization %", xaxis_range=[0, 100], height=280, margin=dict(t=10, l=200))
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Note: SQL queries use hardcoded OEE formula (Availability x Performance x Quality). "
        "Different plants may define this differently — Semantic Views solve this."
    )

# ===========================
# PAGE 2: Drill Down
# ===========================
else:
    st.title("Production Line Drill Down")

    lines = conn.query(
        f"""
        SELECT DISTINCT LINE_NAME FROM {SCHEMA_RAW}.DAILY_PRODUCTION_METRICS
        WHERE PLANT_ID = :1 ORDER BY 1
        """,
        params=[PLANT_ID],
    )
    selected_line = st.selectbox("Select Production Line", lines["LINE_NAME"].tolist())

    # Daily production
    st.subheader(f"Daily Production — {selected_line}")
    line_data = conn.query(
        f"""
        SELECT PRODUCTION_DATE AS date, GOOD_UNITS_PRODUCED AS good_units, 150 AS target_units
        FROM {SCHEMA_RAW}.DAILY_PRODUCTION_METRICS
        WHERE PLANT_ID = :1 AND LINE_NAME = :2
          AND PRODUCTION_DATE >= DATEADD(day, -14, CURRENT_DATE())
        ORDER BY PRODUCTION_DATE
        """,
        params=[PLANT_ID, selected_line],
    )
    fig = px.bar(line_data, x="DATE", y="GOOD_UNITS", labels={"GOOD_UNITS": "Good Units"})
    fig.add_scatter(x=line_data["DATE"], y=line_data["TARGET_UNITS"],
                    mode="lines", name="Target", line=dict(color="red", dash="dash"))
    fig.update_layout(height=300, margin=dict(t=20), xaxis_title="", yaxis_title="Units")
    st.plotly_chart(fig, use_container_width=True)

    # Issue log
    st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
    line_issues = conn.query(
        f"""
        SELECT ISSUE_ID, ISSUE_TYPE AS type, DESCRIPTION, SEVERITY, STATUS, CREATED_AT
        FROM {SCHEMA_RAW}.ISSUES
        WHERE PLANT_ID = :1 AND PRODUCTION_LINE = :2
          AND CREATED_AT >= DATEADD(day, -7, CURRENT_DATE())
        ORDER BY CREATED_AT DESC
        """,
        params=[PLANT_ID, selected_line],
    )
    if line_issues.empty:
        st.info("No issues recorded for this line in the last 7 days.")
    else:
        st.dataframe(line_issues, use_container_width=True, hide_index=True)
