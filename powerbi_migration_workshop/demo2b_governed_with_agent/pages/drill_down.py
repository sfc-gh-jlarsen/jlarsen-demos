"""
Drill Down page — Line-level detail with hourly production, issue log, changeover history.
"""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from data.synthetic_data import (
    LINES,
    get_changeover_history,
    get_issues,
    get_oee_data,
)

st.title("Production Line Drill Down")

selected_line = st.selectbox("Select Production Line", LINES)

# --- Hourly Production vs Target (simulated as daily for this demo) ---
st.subheader(f"Daily Production — {selected_line}")
oee_df = get_oee_data(weeks=2)
line_data = oee_df[oee_df["production_line"] == selected_line].tail(14).copy()
line_data["target_units"] = 150

fig = px.bar(line_data, x="date", y="good_units", labels={"good_units": "Good Units"})
fig.add_scatter(x=line_data["date"], y=line_data["target_units"],
                mode="lines", name="Target", line=dict(color="red", dash="dash"))
fig.update_layout(height=300, margin=dict(t=20), xaxis_title="", yaxis_title="Units")
st.plotly_chart(fig, use_container_width=True)

# --- Issue Log ---
st.subheader(f"Issue Log (Last 7 Days) — {selected_line}")
issues_df = get_issues()
line_issues = issues_df[issues_df["production_line"] == selected_line][
    ["issue_id", "type", "description", "severity", "status", "created_at", "resolved_at"]
]
if line_issues.empty:
    st.info("No issues recorded for this line in the last 7 days.")
else:
    st.dataframe(line_issues, use_container_width=True, hide_index=True)

# --- Changeover History ---
st.subheader(f"Changeover History — {selected_line}")
changeover_df = get_changeover_history()
line_changeovers = changeover_df[changeover_df["production_line"] == selected_line][
    ["changeover_time", "duration_minutes", "from_product", "to_product"]
]
if line_changeovers.empty:
    st.info("No changeovers recorded for this line.")
else:
    avg_duration = line_changeovers["duration_minutes"].mean()
    st.metric("Average Changeover Time", f"{avg_duration:.0f} min")
    st.dataframe(line_changeovers, use_container_width=True, hide_index=True)
