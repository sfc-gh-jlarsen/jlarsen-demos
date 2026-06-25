# Plan: PowerBI Migration Workshop Demo

## Context

- **Database**: `MFG_SCHEDULING_REPORTING`
- **Agent approach**: Full Cortex Agent API with `cortex_analyst_tool` pointing at the semantic view (no Complete() fallback)
- **Branch**: `demo/powerbi-migration` (local only)
- **Domain**: Generic manufacturing production scheduler (no customer references)
- **Existing repo pattern**: Each demo is a top-level folder with README, app.py/streamlit_app.py, and supporting files

## Project Structure

```
powerbi_migration_workshop/
├── README.md                              # Workshop overview, setup, demo flow script
├── .gitignore                             # *.pdf, *.pptx, slides/*.pdf
├── data/
│   └── synthetic_data.py                  # Shared data generation module
├── demo1_adhoc_material_check/
│   └── streamlit_app.py                   # Single-file workspace app (Tactical Scheduler)
├── demo2a_plant_dashboard/
│   └── streamlit_app.py                   # Multi-page governed dashboard, direct SQL
├── demo2b_governed_with_agent/
│   ├── streamlit_app.py                   # Dashboard + Cortex Agent sidebar
│   └── manufacturing_semantic_view.yaml   # Semantic view YAML definition
├── demo3_callers_rights/
│   └── README.md                          # Code diffs, SQL snippets, setup instructions
├── demo4_spcs_ops_guide/
│   └── streamlit_app.py                   # Multi-tab SPCS reference app
├── sql/
│   ├── 01_setup_database.sql              # CREATE DATABASE MFG_SCHEDULING_REPORTING, schemas, roles
│   ├── 02_create_tables.sql               # Table DDL
│   ├── 03_load_synthetic_data.sql         # INSERT synthetic data
│   ├── 04_semantic_view.sql               # CREATE SEMANTIC VIEW
│   ├── 05_cortex_agent.sql                # CREATE CORTEX AGENT with cortex_analyst_tool
│   ├── 06_row_access_policy.sql           # RAP + caller grants for demo 3
│   └── 99_teardown.sql                    # DROP objects
└── slides/
    └── slide_content.md                   # 6 slide text descriptions (no binary files)
```

## Key Design Decisions

1. **Cortex Agent (Demo 2b)**: Full agent using `cortex_analyst_tool` pointed at `@MFG_SCHEDULING_REPORTING.ANALYTICS.MODELS/manufacturing_semantic_view.yaml`. The sidebar uses `snowflake.core` agent API to send messages and stream responses.

2. **Data strategy**: `data/synthetic_data.py` generates pandas DataFrames for standalone demo use. SQL scripts in `sql/` create and populate real Snowflake tables for production deployment. Apps detect whether they have a Snowflake connection or fall back to synthetic data.

3. **Database schema layout**:
   - `MFG_SCHEDULING_REPORTING.RAW` — source tables (production_metrics, work_orders, materials, etc.)
   - `MFG_SCHEDULING_REPORTING.ANALYTICS` — views/aggregations consumed by apps
   - `MFG_SCHEDULING_REPORTING.ANALYTICS.MODELS` — stage for semantic view YAML

4. **No customer specifics**: Plants are "Detroit Manufacturing Center", "Austin Advanced Assembly", "Monterrey Precision". Products are generic industrial (Hydraulic Valve Assembly, Precision Gear Set, etc.).

## Implementation Steps

### Step 1: Create branch and scaffold

- `git checkout -b demo/powerbi-migration` from main
- Create directory structure
- Add project-level `.gitignore` (PDFs, PPTX, slides binaries)

### Step 2: Build shared synthetic data module

`data/synthetic_data.py` generates:
- 30 work orders across 5 production lines (mix of statuses)
- 56 days x 6 lines = 336 OEE records (8 weeks)
- 20 materials, 3 with shortages
- 4 active issues + 12 resolved
- 15 delivery commitments, 3 at risk
- Deterministic seed so data is reproducible

### Step 3: Build Demo 2b — Governed dashboard + Cortex Agent (highest priority)

Multi-page Streamlit app with:
- Page 1: Plant Overview — KPIs (OEE, OTD, throughput, issues), trend charts, production line status
- Page 2: Drill-down — line-level hourly production, issue log, changeover history
- Cortex Agent sidebar (collapsible `st.expander`):
  - Full agent chat using `snowflake.core` API
  - Agent configured with `cortex_analyst_tool` pointing to semantic view
  - Message history in session state
  - Sample questions displayed as buttons
- Badge: "Powered by Semantic View: manufacturing_operations"
- Separate `manufacturing_semantic_view.yaml` file

### Step 4: Build Demo 1 — Ad-hoc material check

Single-file workspace app:
- Sidebar: date picker, production line multiselect
- KPI row: scheduled WOs, material availability %, at-risk orders, shortage count
- Work order table with material status indicators
- Shortage table with severity and affected WOs
- Bar chart: material availability by line

### Step 5: Build Demo 4 — SPCS operations guide

Multi-tab reference app (5 tabs):
- Architecture (diagram + explanation)
- Scaling and Warm Pools (code examples, cost calculator)
- Monitoring and Logging (SQL examples)
- External Access (setup pattern)
- Container vs Warehouse Runtime (comparison table)

### Step 6: Build Demo 3 — Caller's rights additions

README.md with:
- One-line code change (connection type)
- Row access policy SQL
- GRANT statements for caller grants
- Side-by-side comparison with PowerBI RLS

### Step 7: SQL setup scripts

- `01_setup_database.sql`: CREATE DATABASE, schemas, roles, warehouse
- `02_create_tables.sql`: DDL for all tables in RAW schema
- `03_load_synthetic_data.sql`: INSERT statements from synthetic data
- `04_semantic_view.sql`: CREATE SEMANTIC VIEW from YAML
- `05_cortex_agent.sql`: CREATE CORTEX AGENT with analyst tool
- `06_row_access_policy.sql`: RAP + caller grants
- `99_teardown.sql`: DROP everything

### Step 8: Slide content + project README

- `slides/slide_content.md`: All 6 slide descriptions (text/diagrams, no binary)
- Project `README.md`: Workshop overview, prerequisites, setup instructions, full demo flow script with presenter notes

## Verification

- Each Streamlit app runs standalone with synthetic data (`streamlit run streamlit_app.py`)
- SQL scripts compile without errors (verify with `only_compile=true`)
- Semantic view YAML passes `reflect_semantic_model` validation
- No customer-specific names or references in any file

## Critical Files

- `data/synthetic_data.py` — Foundation for all demo apps; must be imported cleanly
- `demo2b_governed_with_agent/streamlit_app.py` — Highest priority demo, most complex (agent + dashboard)
- `demo2b_governed_with_agent/manufacturing_semantic_view.yaml` — Semantic view definition consumed by agent
- `sql/05_cortex_agent.sql` — Agent DDL with cortex_analyst_tool configuration
- `sql/06_row_access_policy.sql` — Caller's rights enablement for Demo 3
