# NPO Logging Architecture

## How Logging Flows from Notebook to Event Table

```
┌─────────────────────────────────────────────────────────────────┐
│                   SNOWFLAKE TASK (Scheduler)                     │
│  EXECUTE TASK db.schema.my_task                                 │
│  └──> EXECUTE NOTEBOOK PROJECT db.schema.my_npo                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              SPCS COMPUTE POOL (Container Runtime)               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Pod (Single Instance)                   │  │
│  │                                                           │  │
│  │  ┌──────────────────────┐  ┌──────────────────────────┐  │  │
│  │  │  snowflake-notebook  │  │  OTel Collector Sidecar  │  │  │
│  │  │  (Main Container)    │  │                          │  │  │
│  │  │                      │  │  Intercepts Python        │  │  │
│  │  │  logging.info() ─────┼──┼──► LOG records           │  │  │
│  │  │  logging.error() ────┼──┼──► LOG records           │  │  │
│  │  │                      │  │                          │  │  │
│  │  │  print() ────────────┼──┼──► stdout (LOST)         │  │  │
│  │  │  print(flush=True) ──┼──┼──► stdout (LOST)         │  │  │
│  │  │                      │  │                          │  │  │
│  │  │  session.sql() ──────┼──┼──► Warehouse (SQL exec)  │  │  │
│  │  └──────────────────────┘  └────────────┬─────────────┘  │  │
│  └─────────────────────────────────────────┼─────────────────┘  │
└────────────────────────────────────────────┼────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EVENT TABLE (Account-Level)                     │
│                                                                 │
│  ┌─────────┬─────────────────────────────────────────────────┐  │
│  │ LOG     │ logging.info/warning/error/critical messages     │  │
│  ├─────────┼─────────────────────────────────────────────────┤  │
│  │ EVENT   │ Container lifecycle: PENDING → READY → DONE     │  │
│  ├─────────┼─────────────────────────────────────────────────┤  │
│  │ METRIC  │ CPU, memory, disk (automatic)                   │  │
│  └─────────┴─────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SNOWSIGHT UI                             │
│  Catalog > DB Explorer > NPO > Run History > Logs tab           │
└─────────────────────────────────────────────────────────────────┘
```

## What Goes Where

| What | Where It Ends Up | How to Access |
|---|---|---|
| `logging.info("msg")` | Event table (LOG records) | SQL query or Snowsight Logs tab |
| `print("msg")` | Container stdout | Nowhere after container exits |
| Container start/stop | Event table (EVENT records) | SQL query |
| CPU/memory usage | Event table (METRIC records) | SQL query |
| SQL run inside notebook | Warehouse (no separate query history entry) | Not individually visible |
| NPO execution itself | Query history as `EXECUTE_NOTEBOOK_PROJECT_VNEXT` | Query History in Snowsight |

## Why print() Doesn't Work

NPOs run inside SPCS containers. The telemetry pipeline uses an **OpenTelemetry sidecar** that hooks into Python's logging handlers at the runtime level. It does NOT capture raw file descriptor output (stdout/stderr).

This means:
- `print()` writes to stdout fd -> container local fs -> gone when container exits
- `logging.info()` writes via Python handler -> OTel sidecar intercepts -> event table

No amount of `flush=True` or `file=sys.stderr` changes this. The interception happens at the Python logging handler layer, not the OS output stream layer.

## Are SQL Queries from Inside the Notebook Visible in Query History?

**No.** SQL executed via Snowpark (`session.sql()`, `df.save_as_table()`) runs through an internal service session within the SPCS container. These queries are encapsulated within the single parent `EXECUTE_NOTEBOOK_PROJECT_VNEXT` query entry.

You will see ONE query in history:
```
QUERY_TYPE: EXECUTE_NOTEBOOK_PROJECT_VNEXT
QUERY_TEXT: EXECUTE NOTEBOOK PROJECT "DB"."SCHEMA"."PROJECT" ...
STATUS:     SUCCESS
ELAPSED:    ~50 seconds (includes all internal SQL)
```

Individual `USE DATABASE`, `CREATE TABLE`, `SELECT` statements from inside the notebook are NOT separately listed.

## Required Configuration

```
LOG_LEVEL = INFO          (generates log messages)
         +
LOG_EVENT_LEVEL = INFO    (writes them to event table)  <-- MOST COMMONLY MISSED
         +
EVENT_TABLE set at ACCOUNT level  (SPCS reads account, not database)
         +
Notebook code: import logging; logging.getLogger().setLevel(logging.INFO)
```

All four are required. Missing any one means no logs in the UI.
