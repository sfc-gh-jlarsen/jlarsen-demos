# Drill Down page using SEMANTIC_VIEW() queries for governed metrics
# Co-authored with CoCo
"""
Drill Down page — Line-level detail with daily production, issue log.
Queries governed metrics via the SEMANTIC_VIEW() clause.
"""

import plotly.express as px
import streamlit as st

# --- Configuration ---
SV = "MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS"
PLANT_ID = "DET01"

conn = st.connection("snowflake")

st.title("Production Line Drill Down")

# Get available lines from semantic view
lines = conn.query(f"""
    SELECT DISTINCT production_line
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS daily_production_metrics.plant_id,
                   daily_production_metrics.production_line
        METRICS daily_production_metrics.throughput
    )
    WHERE plant_id = '{PLANT_ID}'
    ORDER BY production_line
""")

selected_line = st.selectbox("Select Production Line", lines["PRODUCTION_LINE"].tolist())

# --- Daily Production vs Target ---
st.subheader(f"Daily Production — {selected_line}")
line_data = conn.query(f"""
    SELECT *
    FROM SEMANTIC_VIEW(
        {SV}
        DIMENSIONS daily_production_metrics.plant_id,
                   daily_production_metrics.production_line,
                   daily_production_metrics.production_date
        METRICS daily_production_metrics.throughput,
                daily_production_metrics.oee
    )
    WHERE plant_id = '{PLANT_ID}'
      AND production_line = '{selected_line}'
      AND production_date >= DATEADD(day, -14, CURRENT_DATE())
    ORDER BY production_date
""")

if not line_data.empty:
    fig = px.bar(line_data, x="PRODUCTION_DATE", y="THROUGHPUT", labels={"THROUGHPUT": "Good Units"})
    fig.add_scatter(
        x=line_data["PRODUCTION_DATE"],
        y=[150] * len(line_data),
        mode="lines", name="Target", line=dict(color="red", dash="dash"),
    )
    fig.update_layout(height=300, margin=dict(t=20), xaxis_title="", yaxis_title="Units")
    st.plotly_chart(fig, use_container_width=True)

    # OEE sparkline for selected line
    st.subheader(f"OEE Trend — {selected_line}")
    line_data["OEE_PCT"] = line_data["OEE"] * 100
    fig2 = px.line(line_data, x="PRODUCTION_DATE", y="OEE_PCT", markers=True)
    fig2.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Target: 85%")
    fig2.update_layout(height=250, margin=dict(t=20), xaxis_title="", yaxis_title="OEE %")
    st.plotly_chart(fig2, use_container_width=True)

# --- Issue Log ---
st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
line_issues = conn.query(f"""
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
    WHERE production_line = '{selected_line}'
      AND created_at >= DATEADD(day, -7, CURRENT_DATE())
    ORDER BY created_at DESC
""")

if line_issues.empty:
    st.info("No issues recorded for this line in the last 7 days.")
else:
    st.dataframe(line_issues, use_container_width=True, hide_index=True)
