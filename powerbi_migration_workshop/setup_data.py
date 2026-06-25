"""
Setup script: Materializes synthetic data into Snowflake tables.
Run this AFTER executing sql/01_setup_database.sql and sql/02_create_tables.sql.

Usage:
    python setup_data.py

Requires: snowflake-connector-python, pandas, numpy
Uses the default Snowflake connection from ~/.snowflake/connections.toml
"""

import sys
from pathlib import Path

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data.synthetic_data import (
    get_delivery_data,
    get_issues,
    get_material_availability,
    get_oee_data,
    get_work_orders,
)

DATABASE = "MFG_SCHEDULING_REPORTING"


def main():
    print("Connecting to Snowflake...")
    conn = snowflake.connector.connect(connection_name="default")
    conn.cursor().execute(f"USE DATABASE {DATABASE}")
    conn.cursor().execute("USE WAREHOUSE COMPUTE_WH")

    # --- OEE / Production Metrics ---
    print("Generating production metrics (8 weeks × 6 lines)...")
    oee_df = get_oee_data(weeks=8)
    oee_df = oee_df.rename(columns={
        "date": "PRODUCTION_DATE",
        "plant_id": "PLANT_ID",
        "plant_name": "PLANT_NAME",
        "production_line": "LINE_NAME",
        "oee": "_OEE",  # computed column in view, don't load
        "availability_pct": "AVAILABILITY_PCT",
        "performance_pct": "PERFORMANCE_PCT",
        "quality_pct": "QUALITY_PCT",
        "good_units": "GOOD_UNITS_PRODUCED",
        "total_units": "TOTAL_UNITS_PRODUCED",
        "scrap_units": "SCRAPPED_UNITS",
        "downtime_minutes": "DOWNTIME_MINUTES",
        "shift": "SHIFT_NAME",
    })
    # Add a product name for each row
    from data.synthetic_data import PRODUCTS, rng
    oee_df["PRODUCT_NAME"] = [PRODUCTS[i % len(PRODUCTS)] for i in range(len(oee_df))]
    oee_load = oee_df[[
        "PRODUCTION_DATE", "PLANT_ID", "PLANT_NAME", "LINE_NAME", "PRODUCT_NAME",
        "SHIFT_NAME", "AVAILABILITY_PCT", "PERFORMANCE_PCT", "QUALITY_PCT",
        "GOOD_UNITS_PRODUCED", "TOTAL_UNITS_PRODUCED", "SCRAPPED_UNITS", "DOWNTIME_MINUTES",
    ]]
    write_pandas(conn, oee_load, "DAILY_PRODUCTION_METRICS", schema="RAW", overwrite=True)
    print(f"  Loaded {len(oee_load)} rows into RAW.DAILY_PRODUCTION_METRICS")

    # --- Work Orders ---
    print("Generating work orders...")
    wo_df = get_work_orders()
    wo_df["plant_id"] = "DET01"
    wo_df = wo_df.rename(columns={
        "wo_id": "WO_ID",
        "product": "PRODUCT_NAME",
        "production_line": "PRODUCTION_LINE",
        "quantity": "QUANTITY",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "material_status": "MATERIAL_STATUS",
        "plant_id": "PLANT_ID",
    })
    write_pandas(conn, wo_df, "WORK_ORDERS", schema="RAW", overwrite=True)
    print(f"  Loaded {len(wo_df)} rows into RAW.WORK_ORDERS")

    # --- Materials ---
    print("Generating materials inventory...")
    mat_df = get_material_availability()
    mat_df = mat_df.rename(columns={
        "material": "MATERIAL_NAME",
        "qty_required": "QTY_REQUIRED",
        "qty_on_hand": "QTY_ON_HAND",
        "qty_short": "QTY_SHORT",
        "expected_resolution": "EXPECTED_RESOLUTION",
        "impact_severity": "IMPACT_SEVERITY",
        "affected_wo": "AFFECTED_WO",
    })
    write_pandas(conn, mat_df, "MATERIALS", schema="RAW", overwrite=True)
    print(f"  Loaded {len(mat_df)} rows into RAW.MATERIALS")

    # --- Issues ---
    print("Generating issues...")
    issues_df = get_issues()
    issues_df["plant_id"] = "DET01"
    issues_df = issues_df.rename(columns={
        "issue_id": "ISSUE_ID",
        "production_line": "PRODUCTION_LINE",
        "type": "ISSUE_TYPE",
        "description": "DESCRIPTION",
        "severity": "SEVERITY",
        "status": "STATUS",
        "created_at": "CREATED_AT",
        "resolved_at": "RESOLVED_AT",
        "plant_id": "PLANT_ID",
    })
    write_pandas(conn, issues_df, "ISSUES", schema="RAW", overwrite=True)
    print(f"  Loaded {len(issues_df)} rows into RAW.ISSUES")

    # --- Deliveries ---
    print("Generating delivery commitments...")
    del_df = get_delivery_data()
    del_df["plant_id"] = "DET01"
    del_df = del_df.rename(columns={
        "wo_id": "WO_ID",
        "product": "PRODUCT_NAME",
        "promise_date": "PROMISE_DATE",
        "estimated_ship": "ESTIMATED_SHIP",
        "on_time": "ON_TIME",
        "risk_reason": "RISK_REASON",
        "plant_id": "PLANT_ID",
    })
    del_df = del_df[["WO_ID", "PRODUCT_NAME", "PROMISE_DATE", "ESTIMATED_SHIP", "ON_TIME", "RISK_REASON", "PLANT_ID"]]
    write_pandas(conn, del_df, "DELIVERIES", schema="RAW", overwrite=True)
    print(f"  Loaded {len(del_df)} rows into RAW.DELIVERIES")

    # --- User-plant assignments ---
    print("Loading user-plant assignments...")
    import pandas as pd
    assignments = pd.DataFrame([
        {"USER_EMAIL": "detroit_pm@company.com", "PLANT_ID": "DET01"},
        {"USER_EMAIL": "austin_pm@company.com", "PLANT_ID": "AUS02"},
        {"USER_EMAIL": "monterrey_pm@company.com", "PLANT_ID": "MTY03"},
        {"USER_EMAIL": "regional_vp@company.com", "PLANT_ID": "DET01"},
        {"USER_EMAIL": "regional_vp@company.com", "PLANT_ID": "AUS02"},
        {"USER_EMAIL": "regional_vp@company.com", "PLANT_ID": "MTY03"},
    ])
    write_pandas(conn, assignments, "USER_PLANT_ASSIGNMENTS", schema="ADMIN", overwrite=True)
    print(f"  Loaded {len(assignments)} rows into ADMIN.USER_PLANT_ASSIGNMENTS")

    conn.close()
    print("\nDone. All synthetic data materialized in Snowflake.")
    print("Next steps:")
    print("  1. Run sql/04_semantic_view.sql")
    print("  2. Run sql/05_cortex_agent.sql")
    print("  3. Deploy apps to Snowsight")


if __name__ == "__main__":
    main()
