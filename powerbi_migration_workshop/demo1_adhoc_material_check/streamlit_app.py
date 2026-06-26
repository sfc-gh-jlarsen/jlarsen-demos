"""
Demo 1: Ad-Hoc Material Availability Check
===========================================
Single-file Streamlit workspace app for a Tactical Scheduler.
Replaces the "spin up a quick PowerBI file to check something" pattern.

Runtime: Container (Workspaces — private, ephemeral)
Persona: Tactical Scheduler
"""

from datetime import datetime, timedelta

import plotly.express as px
import streamlit as st

# --- Configuration ---
DATABASE = "MFG_SCHEDULING_REPORTING"
SCHEMA_RAW = f"{DATABASE}.RAW"

st.set_page_config(page_title="Material Availability Check", layout="wide")
st.title("Material Availability Check")

conn = st.connection("snowflake")

# --- Sidebar Filters ---
lines_df = conn.query(
    f"SELECT DISTINCT PRODUCTION_LINE FROM {SCHEMA_RAW}.WORK_ORDERS ORDER BY 1"
)
all_lines = lines_df["PRODUCTION_LINE"].tolist()

with st.sidebar:
    st.header("Filters")
    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
    target_date = st.date_input("Production Date", value=next_monday)
    selected_lines = st.multiselect("Production Lines", all_lines, default=all_lines[:3])

# --- Load Data ---
wo_df = conn.query(
    f"""
    SELECT WO_ID, PRODUCT_NAME, PRODUCTION_LINE, QUANTITY, DUE_DATE, STATUS, MATERIAL_STATUS
    FROM {SCHEMA_RAW}.WORK_ORDERS
    WHERE DUE_DATE BETWEEN DATEADD(day, -2, :1) AND DATEADD(day, 5, :1)
    """,
    params=[target_date.isoformat()],
)

mat_df = conn.query(f"""
    SELECT MATERIAL_NAME, QTY_REQUIRED, QTY_ON_HAND, QTY_SHORT,
           EXPECTED_RESOLUTION, IMPACT_SEVERITY, AFFECTED_WO
    FROM {SCHEMA_RAW}.MATERIALS
""")

# Filter work orders by selected lines
wo_filtered = wo_df[wo_df["PRODUCTION_LINE"].isin(selected_lines)]

# --- KPI Row ---
total_wos = len(wo_filtered)
materials_available_pct = (
    len(mat_df[mat_df["QTY_SHORT"] == 0]) / len(mat_df) * 100 if len(mat_df) > 0 else 0
)
at_risk = len(wo_filtered[wo_filtered["MATERIAL_STATUS"] != "Available"])
shortage_count = len(mat_df[mat_df["QTY_SHORT"] > 0])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Scheduled Work Orders", total_wos)
col2.metric("Materials Available", f"{materials_available_pct:.0f}%")
col3.metric("At-Risk Orders", at_risk)
col4.metric("Material Shortages", shortage_count)

st.divider()

# --- Work Order Table ---
st.subheader(f"Work Orders — {target_date.strftime('%A, %B %d')}")

STATUS_ICONS = {"Available": "🟢", "Partial": "🟡", "Shortage": "🔴"}
wo_display = wo_filtered.copy()
wo_display["MATERIAL_STATUS"] = wo_display["MATERIAL_STATUS"].map(
    lambda s: f"{STATUS_ICONS.get(s, '')} {s}"
)
st.dataframe(
    wo_display[["WO_ID", "PRODUCT_NAME", "PRODUCTION_LINE", "QUANTITY", "DUE_DATE", "STATUS", "MATERIAL_STATUS"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "WO_ID": "WO ID",
        "PRODUCT_NAME": "Product",
        "PRODUCTION_LINE": "Line",
        "QUANTITY": "Qty",
        "DUE_DATE": "Due Date",
        "STATUS": "Status",
        "MATERIAL_STATUS": "Material",
    },
)

# --- Material Shortages ---
st.subheader("Material Shortages")
shortages = mat_df[mat_df["QTY_SHORT"] > 0][
    ["MATERIAL_NAME", "QTY_SHORT", "EXPECTED_RESOLUTION", "IMPACT_SEVERITY", "AFFECTED_WO"]
]
if shortages.empty:
    st.success("No material shortages detected.")
else:
    st.dataframe(
        shortages,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MATERIAL_NAME": "Material",
            "QTY_SHORT": "Qty Short",
            "EXPECTED_RESOLUTION": "Expected Resolution",
            "IMPACT_SEVERITY": "Severity",
            "AFFECTED_WO": "Affected WO",
        },
    )

# --- Bar Chart: Material Availability by Line ---
st.subheader("Material Availability by Production Line")

line_availability = (
    wo_filtered.groupby("PRODUCTION_LINE")["MATERIAL_STATUS"]
    .apply(lambda x: (x.str.contains("Available")).sum() / len(x) * 100)
    .reset_index()
)
line_availability.columns = ["PRODUCTION_LINE", "availability_pct"]

fig = px.bar(
    line_availability.sort_values("availability_pct"),
    x="availability_pct",
    y="PRODUCTION_LINE",
    orientation="h",
    color="availability_pct",
    color_continuous_scale=["#F44336", "#FF9800", "#4CAF50"],
    range_color=[0, 100],
)
fig.update_layout(
    xaxis_title="Availability %",
    xaxis_range=[0, 100],
    yaxis_title="",
    height=250,
    margin=dict(t=10, l=180),
    coloraxis_showscale=False,
)
st.plotly_chart(fig, use_container_width=True)
