"""
Demo 1: Ad-Hoc Material Availability Check
===========================================
Single-file Streamlit workspace app for a Tactical Scheduler.
Replaces the "spin up a quick PowerBI file to check something" pattern.

Runtime: Container (Workspaces — private, ephemeral)
Persona: Tactical Scheduler
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.synthetic_data import LINES, get_material_availability, get_work_orders

st.set_page_config(page_title="Material Availability Check", layout="wide")
st.title("Material Availability Check")

# --- Sidebar Filters ---
with st.sidebar:
    st.header("Filters")
    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
    target_date = st.date_input("Production Date", value=next_monday)
    selected_lines = st.multiselect("Production Lines", LINES, default=LINES[:3])

# --- Load Data ---
wo_df = get_work_orders(target_date=datetime.combine(target_date, datetime.min.time()))
mat_df = get_material_availability()

# Filter work orders by selected lines
wo_filtered = wo_df[wo_df["production_line"].isin(selected_lines)]

# --- KPI Row ---
total_wos = len(wo_filtered)
materials_available_pct = (
    len(mat_df[mat_df["qty_short"] == 0]) / len(mat_df) * 100 if len(mat_df) > 0 else 0
)
at_risk = len(wo_filtered[wo_filtered["material_status"] != "Available"])
shortage_count = len(mat_df[mat_df["qty_short"] > 0])

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
wo_display["material_status"] = wo_display["material_status"].map(
    lambda s: f"{STATUS_ICONS.get(s, '')} {s}"
)
st.dataframe(
    wo_display[["wo_id", "product", "production_line", "quantity", "due_date", "status", "material_status"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "wo_id": "WO ID",
        "product": "Product",
        "production_line": "Line",
        "quantity": "Qty",
        "due_date": "Due Date",
        "status": "Status",
        "material_status": "Material",
    },
)

# --- Material Shortages ---
st.subheader("Material Shortages")
shortages = mat_df[mat_df["qty_short"] > 0][
    ["material", "qty_short", "expected_resolution", "impact_severity", "affected_wo"]
]
if shortages.empty:
    st.success("No material shortages detected.")
else:
    st.dataframe(
        shortages,
        use_container_width=True,
        hide_index=True,
        column_config={
            "material": "Material",
            "qty_short": "Qty Short",
            "expected_resolution": "Expected Resolution",
            "impact_severity": "Severity",
            "affected_wo": "Affected WO",
        },
    )

# --- Bar Chart: Material Availability by Line ---
st.subheader("Material Availability by Production Line")
import pandas as pd

line_availability = (
    wo_filtered.groupby("production_line")["material_status"]
    .apply(lambda x: (x == "Available").sum() / len(x) * 100)
    .reset_index()
)
line_availability.columns = ["production_line", "availability_pct"]

import plotly.express as px

fig = px.bar(
    line_availability.sort_values("availability_pct"),
    x="availability_pct",
    y="production_line",
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
