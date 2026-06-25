# PowerBI Migration Workshop

**60-minute workshop** demonstrating Snowflake as a replacement for PowerBI workloads using a manufacturing production scheduler domain.

## Key Messages

1. The semantic layer CAN and SHOULD live in Snowflake (via Semantic Views) — but it's not required to get started
2. Caller's rights provides the same governance as PowerBI RLS — enforced at the platform level
3. The progression from ad-hoc exploration to governed app to distributed app is seamless

## Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Python 3.10+ with `streamlit`, `pandas`, `numpy`, `plotly`
- Run SQL setup scripts in order (see `sql/` directory)

## Quick Start (Standalone with Synthetic Data)

Each demo app works independently without Snowflake setup:

```bash
cd powerbi_migration_workshop

# Demo 1: Ad-hoc material check
streamlit run demo1_adhoc_material_check/streamlit_app.py

# Demo 2b: Governed dashboard + Cortex Agent
streamlit run demo2b_governed_with_agent/streamlit_app.py

# Demo 4: SPCS operations guide
streamlit run demo4_spcs_ops_guide/streamlit_app.py
```

## Full Setup (with Snowflake)

```bash
# 1. Create database and tables
snowsql -f sql/01_setup_database.sql
snowsql -f sql/02_create_tables.sql

# 2. Materialize synthetic data into Snowflake
pip install snowflake-connector-python pandas numpy
python setup_data.py

# 3. Upload semantic view YAML and create objects
snow stage copy demo2b_governed_with_agent/manufacturing_semantic_view.yaml \
    @MFG_SCHEDULING_REPORTING.ANALYTICS.MODELS/ --overwrite
snowsql -f sql/04_semantic_view.sql
snowsql -f sql/05_cortex_agent.sql
snowsql -f sql/06_row_access_policy.sql

# 4. Deploy apps via Streamlit in Snowflake (container runtime)
```

## The Demo Narrative

The story arc starts in Snowflake itself — show the data lives here:

```sql
-- "Here's the production data sitting in Snowflake — same place your ERP lands it."
SELECT LINE_NAME, AVG(OEE) AS avg_oee, SUM(GOOD_UNITS_PRODUCED) AS throughput
FROM MFG_SCHEDULING_REPORTING.ANALYTICS.DAILY_PRODUCTION_METRICS
WHERE PLANT_ID = 'DET01' AND PRODUCTION_DATE >= DATEADD(week, -1, CURRENT_DATE())
GROUP BY LINE_NAME
ORDER BY avg_oee;

-- "Great, I can see CNC Machining is underperforming. But now I need to
--  visualize this, drill into it, share it with my team. In the old world,
--  I'd open PowerBI Desktop and start building a .pbix file..."
--
-- "Watch what happens instead."
```

Then open Demo 1 (workspace app) — the ad-hoc replacement. The transition is:
*"I queried the data. I need a visual. Instead of exporting to PowerBI, I build
it right here — in a workspace, private to me, zero deployment."*

## Demo Structure

| # | Demo | App | Persona |
|---|------|-----|---------|
| 1 | Ad-Hoc Material Check | `demo1_adhoc_material_check/` | Tactical Scheduler |
| 2a | Plant Dashboard (no SV) | `demo2a_plant_dashboard/` | Plant Manager |
| 2b | Governed + Agent | `demo2b_governed_with_agent/` | Plant Manager |
| 3 | Caller's Rights | `demo3_callers_rights/` | (code diff of 2b) |
| 4 | SPCS Ops Guide | `demo4_spcs_ops_guide/` | IT / Platform |

## Demo Flow (60 Minutes)

### Opening (3 min)
> "You've got PowerBI sprawl. Dozens of reports, fragmented DAX logic, RLS defined per model. Every time an analyst needs to 'quickly check something,' they create a new .pbix file that lives forever. Today I'm going to show you how Snowflake eliminates all three problems."

### Demo 1 — The Ad-Hoc Replacement (10 min)
> Start in a Snowflake worksheet. Run a quick query showing OEE by line. "See? The data's right here. Now I need to visualize it, filter it interactively, maybe share a screenshot. In the old world, I'd open PowerBI Desktop..."
>
> Open workspace app. "Instead, I build it right here. Same data, instant interactivity." Change the date filter live — instant refresh. "This is private to ME. No deployment. When I'm done, I close it. No report sprawl."

### Demo 2a — Governed Dashboard (8 min)
> Show deployed multi-page app. OEE, OTD, drill-down. Point out hardcoded SQL with business logic. "Works fine... until someone in Austin defines OEE differently."

### Demo 2b — Semantic View + Agent (10 min)
> Show semantic view definition (metrics defined ONCE). Show the badge. Expand the AI sidebar, ask "What's driving the OEE drop this week?" Show the agent querying the semantic view. "Your PowerBI .pbix can be imported via Semantic View Autopilot."

### Demo 3 — Caller's Rights (5 min)
> Show one-line connection change. Show CURRENT_USER(). Show filtered results. "The Austin plant manager opens this same URL — sees only their data."

### Demo 4 — SPCS Ops (5 min)
> Quick tour of ops guide tabs — sizing, scaling, monitoring. "Warm pools eliminate cold start. Auto-scaling handles variable load."

### Closing (6 min)
> Migration path slide. "Upload .pbix, pilot workspace apps, convert certified reports, add agent, map RLS. Someone needs to own the semantic layer — let it be Snowflake."

## Database

- **Name:** `MFG_SCHEDULING_REPORTING`
- **Schemas:** `RAW`, `ANALYTICS`, `ADMIN`
- **Teardown:** `sql/99_teardown.sql`

## Slides

See `slides/slide_content.md` for all 6 slide descriptions. Build your deck from these descriptions — binary slide files (PDF/PPTX) are gitignored.
