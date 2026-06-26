"""
Shared synthetic data generation for the PowerBI Migration Workshop demos.
Deterministic seed ensures reproducible data across runs.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

# --- Constants ---

PLANTS = [
    {"id": "DET01", "name": "Detroit Manufacturing Center"},
    {"id": "AUS02", "name": "Austin Advanced Assembly"},
    {"id": "MTY03", "name": "Monterrey Precision"},
]

LINES = [
    "CNC Machining Bay A",
    "Assembly Line 1 North",
    "Weld Cell 3",
    "Paint & Coat Booth B",
    "Final Assembly South",
    "Pack & Ship Dock 1",
]

PRODUCTS = [
    "Hydraulic Valve Assembly HV-200",
    "Precision Gear Set PG-450",
    "Electric Motor Housing EMH-100",
    "Control Panel Assembly CPA-75",
    "Brake Rotor BR-300X",
    "Transmission Shaft TS-500",
]

SHIFTS = ["Day (6AM-2PM)", "Swing (2PM-10PM)", "Night (10PM-6AM)"]

MATERIALS = [
    "Alloy Steel Billet 4140",
    "Aluminum Extrusion 6061-T6",
    "Copper Winding Wire 12AWG",
    "Carbide Insert CNMG-120408",
    "Hydraulic Seal Kit HSK-200",
    "Bearing Assembly 6205-2RS",
    "Stainless Fastener Set M10",
    "Epoxy Coating RAL-7035",
    "Circuit Board PCB-MK4",
    "Rubber Gasket RG-150",
    "Titanium Rod Grade 5",
    "Polyurethane Bushing PU-40",
    "Servo Motor NEMA-23",
    "Precision Spring SPR-080",
    "Heat Shield Ceramic HSC-12",
    "Weld Wire ER70S-6",
    "Pneumatic Cylinder PC-50",
    "Optical Sensor OS-200",
    "Carbon Fiber Sheet CF-3K",
    "Thermal Paste TP-100",
]

# --- Data Generation Functions ---


def get_work_orders(target_date=None):
    """Generate 30 work orders across production lines."""
    if target_date is None:
        target_date = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)

    statuses = ["Scheduled", "In Progress", "Material Hold", "Complete", "At Risk"]
    material_statuses = ["Available", "Partial", "Shortage"]

    records = []
    for i in range(30):
        line = LINES[i % len(LINES)]
        product = rng.choice(PRODUCTS)
        status = rng.choice(statuses, p=[0.35, 0.25, 0.10, 0.15, 0.15])
        mat_status = rng.choice(material_statuses, p=[0.65, 0.20, 0.15])
        qty = int(rng.integers(10, 500))
        due_date = target_date + timedelta(days=int(rng.integers(-2, 5)))

        records.append({
            "wo_id": f"WO-2026-{1000 + i}",
            "product": product,
            "production_line": line,
            "quantity": qty,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "status": status,
            "material_status": mat_status,
        })
    return pd.DataFrame(records)


def get_material_availability():
    """Generate material inventory with 3 shortages."""
    records = []
    shortage_indices = [2, 7, 14]
    for i, mat in enumerate(MATERIALS):
        qty_required = int(rng.integers(50, 500))
        if i in shortage_indices:
            qty_on_hand = int(qty_required * rng.uniform(0.3, 0.7))
            shortage = qty_required - qty_on_hand
            resolution = (datetime.now() + timedelta(days=int(rng.integers(2, 7)))).strftime("%Y-%m-%d")
            severity = rng.choice(["High", "Critical"])
            affected_wo = f"WO-2026-{1000 + rng.integers(0, 30)}"
        else:
            qty_on_hand = int(qty_required * rng.uniform(1.0, 1.8))
            shortage = 0
            resolution = None
            severity = "None"
            affected_wo = None

        records.append({
            "material": mat,
            "qty_required": qty_required,
            "qty_on_hand": qty_on_hand,
            "qty_short": shortage,
            "expected_resolution": resolution,
            "impact_severity": severity,
            "affected_wo": affected_wo,
        })
    return pd.DataFrame(records)


def get_oee_data(weeks=8):
    """Generate daily OEE data for all lines over N weeks."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=weeks * 7)
    dates = pd.date_range(start_date, end_date, freq="D")

    records = []
    for line in LINES:
        base_availability = rng.uniform(0.82, 0.94)
        base_performance = rng.uniform(0.85, 0.95)
        base_quality = rng.uniform(0.88, 0.97)

        for date in dates:
            avail = np.clip(base_availability + rng.normal(0, 0.03), 0.60, 0.99)
            perf = np.clip(base_performance + rng.normal(0, 0.02), 0.65, 0.99)
            qual = np.clip(base_quality + rng.normal(0, 0.015), 0.75, 0.99)
            oee = avail * perf * qual

            records.append({
                "date": date.date(),
                "production_line": line,
                "plant_id": "DET01",
                "plant_name": "Detroit Manufacturing Center",
                "availability_pct": round(avail, 4),
                "performance_pct": round(perf, 4),
                "quality_pct": round(qual, 4),
                "oee": round(oee, 4),
                "good_units": int(rng.integers(80, 200)),
                "total_units": int(rng.integers(180, 220)),
                "scrap_units": int(rng.integers(2, 15)),
                "downtime_minutes": int(rng.integers(10, 90)),
                "shift": rng.choice(SHIFTS),
            })
    return pd.DataFrame(records)


def get_delivery_data():
    """Generate 15 delivery commitments, 3 at risk."""
    records = []
    for i in range(15):
        promise_date = datetime.now() + timedelta(days=int(rng.integers(1, 14)))
        if i < 3:
            actual_ship = promise_date + timedelta(days=int(rng.integers(1, 5)))
            risk = rng.choice(["Material delay", "Machine breakdown", "Quality hold"])
            on_time = False
        else:
            actual_ship = promise_date - timedelta(days=int(rng.integers(0, 3)))
            risk = None
            on_time = True

        records.append({
            "wo_id": f"WO-2026-{1000 + i}",
            "product": rng.choice(PRODUCTS),
            "promise_date": promise_date.strftime("%Y-%m-%d"),
            "estimated_ship": actual_ship.strftime("%Y-%m-%d"),
            "days_until_due": (promise_date - datetime.now()).days,
            "on_time": on_time,
            "risk_reason": risk,
        })
    return pd.DataFrame(records)


def get_issues():
    """Generate 4 active issues and 12 resolved."""
    issue_types = ["Machine Breakdown", "Quality Hold", "Material Delay", "Staffing Gap"]
    records = []

    for i in range(16):
        is_active = i < 4
        issue_type = issue_types[i % 4] if i < 4 else rng.choice(issue_types)
        created = datetime.now() - timedelta(days=int(rng.integers(0, 7)))
        resolved = None if is_active else created + timedelta(hours=int(rng.integers(1, 48)))

        records.append({
            "issue_id": f"ISS-{2000 + i}",
            "production_line": rng.choice(LINES),
            "type": issue_type,
            "description": _issue_description(issue_type, i),
            "severity": "High" if i < 2 else "Medium",
            "status": "Open" if is_active else "Resolved",
            "created_at": created.strftime("%Y-%m-%d %H:%M"),
            "resolved_at": resolved.strftime("%Y-%m-%d %H:%M") if resolved else None,
        })
    return pd.DataFrame(records)


def get_on_time_delivery_trend(weeks=8):
    """Weekly on-time delivery percentage for trend charts."""
    records = []
    base_otd = 0.89
    for w in range(weeks):
        week_start = datetime.now().date() - timedelta(weeks=weeks - w - 1)
        otd = np.clip(base_otd + rng.normal(0.005, 0.025), 0.78, 0.98)
        records.append({
            "week_start": week_start,
            "on_time_delivery_pct": round(otd * 100, 1),
        })
    return pd.DataFrame(records)


def get_line_utilization():
    """Current utilization percentage per production line."""
    records = []
    for line in LINES:
        util = round(rng.uniform(55, 95), 1)
        records.append({
            "production_line": line,
            "utilization_pct": util,
            "status": "High" if util >= 80 else ("Medium" if util >= 60 else "Low"),
        })
    return pd.DataFrame(records)


def get_changeover_history():
    """Changeover events for each line in the last 7 days."""
    records = []
    for line in LINES:
        num_changeovers = int(rng.integers(2, 6))
        for _ in range(num_changeovers):
            dt = datetime.now() - timedelta(days=int(rng.integers(0, 7)),
                                            hours=int(rng.integers(0, 12)))
            duration = int(rng.integers(15, 90))
            records.append({
                "production_line": line,
                "changeover_time": dt.strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": duration,
                "from_product": rng.choice(PRODUCTS),
                "to_product": rng.choice(PRODUCTS),
            })
    return pd.DataFrame(records).sort_values("changeover_time", ascending=False).reset_index(drop=True)


def _issue_description(issue_type, idx):
    descriptions = {
        "Machine Breakdown": [
            "Spindle motor overheating on CNC-04, thermal shutdown triggered",
            "Hydraulic press cylinder leak detected on HP-02",
        ],
        "Quality Hold": [
            "Dimensional variance exceeding 0.05mm tolerance on gear batch PG-450-B12",
            "Surface finish defects on EMH-100 batch — roughness Ra > 3.2",
        ],
        "Material Delay": [
            "Supplier delayed shipment of Alloy Steel Billet 4140 — ETA pushed 3 days",
            "Copper Winding Wire 12AWG backordered, alternate supplier quoted",
        ],
        "Staffing Gap": [
            "Night shift 2 operators short — overtime approved for swing coverage",
            "Certified welder on medical leave, contractor approved",
        ],
    }
    options = descriptions.get(issue_type, ["Unspecified issue"])
    return options[idx % len(options)]
