# NPO Observability Demo: print() vs logging in Scheduled Notebooks

## TL;DR

| Output Method | Appears in Event Table? | Appears in Snowsight Logs tab? |
|---|---|---|
| `print("hello")` | NO | NO |
| `print("hello", flush=True)` | NO | NO |
| `print("hello", file=sys.stderr)` | NO | NO |
| `sys.stdout.write("hello\n")` | NO | NO |
| `sys.stderr.write("hello\n")` | NO | NO |
| `logging.info("hello")` | YES | YES |
| `logging.warning("hello")` | YES | YES |
| `logging.error("hello")` | YES | YES |
| `logging.debug("hello")` | Only if LOG_EVENT_LEVEL=DEBUG | Only if LOG_EVENT_LEVEL=DEBUG |

**Bottom line:** `print()` output is NOT captured by the event table regardless of flush or stderr. You MUST use Python's `logging` module for observability in scheduled NPOs.

---

## Problem Statement

When a Notebook Project Object (NPO) runs on a schedule (via a Snowflake Task), customers expect to see execution output in:
1. The **Snowsight Run History > Logs** tab for the NPO
2. The **Event Table** via SQL queries

If the notebook only uses `print()` statements, nothing appears in either location.

## Root Cause

NPOs execute as **SPCS container jobs**. The telemetry pipeline only captures output from Python's `logging` module (which integrates with the OpenTelemetry collector running in the container sidecar). Standard output (`stdout`/`stderr`) from `print()` statements goes to the container's local filesystem and is NOT ingested into the event table.

## Requirements for NPO Logs to Appear

### 1. Account-Level Event Table (REQUIRED for NPO/SPCS)

NPOs run as SPCS jobs, and SPCS uses the **account-level** event table setting. Database-level settings alone are NOT sufficient.

```sql
ALTER ACCOUNT SET EVENT_TABLE = '<db>.<schema>.<event_table>';
```

### 2. Both LOG_LEVEL and LOG_EVENT_LEVEL Must Be Set

This is the single most common misconfiguration. They do different things:

| Parameter | What It Controls |
|---|---|
| `LOG_LEVEL` | Which log messages the runtime **generates** |
| `LOG_EVENT_LEVEL` | Which generated logs are **written to the event table** |

If you only set `LOG_LEVEL`, logs are generated but silently dropped before reaching the event table.

```sql
ALTER ACCOUNT SET LOG_LEVEL = 'INFO';
ALTER ACCOUNT SET LOG_EVENT_LEVEL = 'INFO';  -- COMMONLY MISSED
```

### 3. Notebook Code Must Use Python logging Module

```python
import logging

# Set up logging (do this in the FIRST cell)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('my_pipeline')
logger.setLevel(logging.INFO)

# These WILL appear in event table and Snowsight Logs tab:
logger.info("Pipeline started")
logger.warning("Data quality issue detected")
logger.error("Model training failed")

# These will NOT appear anywhere in observability:
print("Pipeline started")       # LOST
print("Done!", flush=True)      # ALSO LOST
```

## Demo Contents

| File | Description |
|---|---|
| `npo_logging_demo.ipynb` | Notebook that tests print() vs logging at all levels |
| `setup.sql` | Creates database, event table, NPO, and task from scratch |
| `run_and_test.sql` | Executes NPO and queries event table for results |
| `cleanup.sql` | Tears down all demo objects |
| `README.md` | This file |

## Running the Demo

### Prerequisites
- ACCOUNTADMIN role
- An active compute pool (e.g., `SYSTEM_COMPUTE_POOL_CPU`)
- A warehouse (e.g., `COMPUTE_WH`)

### Steps

1. **Upload the notebook:**
   ```sql
   PUT 'file:///path/to/npo_logging_demo.ipynb' @NPO_LOGGING_DEMO.PIPELINE.NOTEBOOK_FILES AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
   ```

2. **Run setup.sql** (creates everything)

3. **Execute the NPO** (pick one):
   ```sql
   -- Manual execution
   EXECUTE NOTEBOOK PROJECT NPO_LOGGING_DEMO.PIPELINE.LOGGING_DEMO_PROJECT
     MAIN_FILE = 'npo_logging_demo.ipynb'
     COMPUTE_POOL = 'SYSTEM_COMPUTE_POOL_CPU'
     QUERY_WAREHOUSE = 'COMPUTE_WH'
     RUNTIME = 'V2.2-CPU-PY3.11';

   -- Or via task (simulates scheduled run)
   EXECUTE TASK NPO_LOGGING_DEMO.PIPELINE.LOGGING_DEMO_TASK;
   ```

4. **Wait 3-5 minutes** for logs to be ingested

5. **Query event table** (see `run_and_test.sql` for full queries):
   ```sql
   -- See what logging module produced (will have results)
   SELECT TIMESTAMP, RECORD:severity_text::STRING AS SEVERITY, VALUE::STRING AS LOG_MESSAGE
   FROM <your_event_table>
   WHERE RECORD_TYPE = 'LOG'
     AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
     AND TIMESTAMP > DATEADD(hour, -1, CURRENT_TIMESTAMP())
   ORDER BY TIMESTAMP DESC;

   -- Search for print() output (will be EMPTY)
   SELECT * FROM <your_event_table>
   WHERE VALUE::STRING LIKE '%PRINT-TEST%';
   ```

## Test Results

### Manual Execution (EXECUTE NOTEBOOK PROJECT)
- logging.info() messages: CAPTURED
- logging.warning() messages: CAPTURED
- logging.error() messages: CAPTURED
- logging.critical() messages: CAPTURED
- logging.debug() messages: NOT captured (filtered by LOG_EVENT_LEVEL=INFO)
- print() statements: NOT captured
- print(flush=True): NOT captured
- print(file=sys.stderr): NOT captured
- sys.stdout.write(): NOT captured
- sys.stderr.write(): NOT captured

### Scheduled Execution (EXECUTE TASK -> EXECUTE NOTEBOOK PROJECT)
- Identical results to manual execution
- Same logging messages captured
- Same print() statements NOT captured

### Event Table Record Types Produced by NPO Execution
| Record Type | Content |
|---|---|
| LOG | Python logging module output (logger name + message) |
| EVENT | Container lifecycle (PENDING, READY, DONE) |
| METRIC | Resource usage (CPU, memory, disk) |

### Resource Attributes Available for Filtering
```json
{
  "snow.account.name": "<your_account>",
  "snow.compute_pool.name": "SYSTEM_COMPUTE_POOL_CPU",
  "snow.database.name": "NPO_LOGGING_DEMO",
  "snow.schema.name": "PIPELINE",
  "snow.executable.engine": "SnowparkContainers",
  "snow.executable.type": "NOTEBOOK",
  "snow.service.name": "NB_NON_INTERACTIVE_<timestamp>_<id>",
  "snow.service.type": "Job"
}
```

## Troubleshooting Checklist

If logs are not appearing for a scheduled NPO:

1. **Check account-level event table is set:**
   ```sql
   SHOW PARAMETERS LIKE 'EVENT_TABLE' IN ACCOUNT;
   ```
   If value is empty or `snowflake.telemetry.events` (default), you need to set it.

2. **Check LOG_EVENT_LEVEL is set (most common miss):**
   ```sql
   SHOW PARAMETERS LIKE 'LOG_EVENT_LEVEL' IN ACCOUNT;
   ```
   If value is `OFF`, no logs will be written to the event table.

3. **Check the notebook code uses logging module:**
   ```python
   import logging
   logging.getLogger().setLevel(logging.INFO)  # REQUIRED
   ```

4. **Wait 3-5 minutes** - there is a documented ingestion delay.

5. **Query the event table directly** to confirm logs exist (they may appear in the event table before the UI updates):
   ```sql
   SELECT * FROM <event_table>
   WHERE RECORD_TYPE = 'LOG'
     AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
     AND TIMESTAMP > DATEADD(minute, -30, CURRENT_TIMESTAMP())
   ORDER BY TIMESTAMP DESC;
   ```

6. **Check permissions** - the role viewing run history needs OWNERSHIP on the task to see result files and logs in the Snowsight UI.

## Guidance for Customers Migrating from print() to logging

Replace this pattern:
```python
print(f"Step 1: Loading data...")
print(f"Loaded {len(df)} rows")
print(f"Model accuracy: {r2:.4f}")
```

With this:
```python
import logging
logger = logging.getLogger('my_pipeline')
logger.setLevel(logging.INFO)

logger.info("Step 1: Loading data...")
logger.info(f"Loaded {len(df)} rows")
logger.info(f"Model accuracy: {r2:.4f}")
```

For structured observability (recommended for production):
```python
import logging
import json

logger = logging.getLogger('ml_pipeline')
logger.setLevel(logging.INFO)

# Structured log for easy querying
logger.info(json.dumps({
    "event": "model_training_complete",
    "metrics": {"mse": 0.123, "r2": 0.95},
    "dataset_size": 10000,
    "model_type": "XGBoost"
}))
```

Then query with:
```sql
SELECT
  TIMESTAMP,
  PARSE_JSON(VALUE):"event"::STRING AS EVENT,
  PARSE_JSON(VALUE):"metrics" AS METRICS
FROM <event_table>
WHERE RECORD_TYPE = 'LOG'
  AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK';
```
