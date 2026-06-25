"""
Drill Down page — Line-level detail with daily production, issue log.
"""

import plotly.express as px
import streamlit as st

# --- Configuration ---
DATABASE = "MFG_SCHEDULING_REPORTING"
SCHEMA_RAW = f"{DATABASE}.RAW"
PLANT_ID = "DET01"

conn = st.connection("snowflake")

st.title("Production Line Drill Down")

lines = conn.query(
    f"""
    SELECT DISTINCT LINE_NAME
    FROM {SCHEMA_RAW}.DAILY_PRODUCTION_METRICS
    WHERE PLANT_ID = :1 ORDER BY 1
    """,
    params=[PLANT_ID],
)
selected_line = st.selectbox("Select Production Line", lines["LINE_NAME"].tolist())

# --- Daily Production vs Target ---
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

# --- Issue Log ---
st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
line_issues = conn.query(
    f"""
    SELECT ISSUE_ID, ISSUE_TYPE AS type, DESCRIPTION, SEVERITY, STATUS,
           CREATED_AT, RESOLVED_AT
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
