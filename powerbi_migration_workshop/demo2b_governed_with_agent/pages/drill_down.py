"""
Drill Down page — Line-level detail with hourly production, issue log, changeover history.
"""

import plotly.express as px
import streamlit as st

conn = st.connection("snowflake")

st.title("Production Line Drill Down")

lines = conn.query("""
    SELECT DISTINCT LINE_NAME
    FROM MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS
    WHERE PLANT_ID = 'DET01' ORDER BY 1
""")
selected_line = st.selectbox("Select Production Line", lines["LINE_NAME"].tolist())

# --- Daily Production vs Target ---
st.subheader(f"Daily Production — {selected_line}")
line_data = conn.query(f"""
    SELECT PRODUCTION_DATE AS date, GOOD_UNITS_PRODUCED AS good_units, 150 AS target_units
    FROM MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS
    WHERE PLANT_ID = 'DET01' AND LINE_NAME = '{selected_line}'
      AND PRODUCTION_DATE >= DATEADD(day, -14, CURRENT_DATE())
    ORDER BY PRODUCTION_DATE
""")

fig = px.bar(line_data, x="DATE", y="GOOD_UNITS", labels={"GOOD_UNITS": "Good Units"})
fig.add_scatter(x=line_data["DATE"], y=line_data["TARGET_UNITS"],
                mode="lines", name="Target", line=dict(color="red", dash="dash"))
fig.update_layout(height=300, margin=dict(t=20), xaxis_title="", yaxis_title="Units")
st.plotly_chart(fig, use_container_width=True)

# --- Issue Log ---
st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
line_issues = conn.query(f"""
    SELECT ISSUE_ID, ISSUE_TYPE AS type, DESCRIPTION, SEVERITY, STATUS,
           CREATED_AT, RESOLVED_AT
    FROM MFG_SCHEDULING_REPORTING.RAW.ISSUES
    WHERE PLANT_ID = 'DET01' AND PRODUCTION_LINE = '{selected_line}'
      AND CREATED_AT >= DATEADD(day, -7, CURRENT_DATE())
    ORDER BY CREATED_AT DESC
""")
if line_issues.empty:
    st.info("No issues recorded for this line in the last 7 days.")
else:
    st.dataframe(line_issues, use_container_width=True, hide_index=True)
