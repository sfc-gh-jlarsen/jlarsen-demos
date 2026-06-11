/*
==============================================================================
NPO Logging Demo: Run and Test
==============================================================================
Execute the NPO manually and via task, then query the event table to see
what print() vs logging produces.
==============================================================================
*/

-- ============================================================
-- CONFIGURATION: Must match setup.sql values
-- ============================================================
SET event_table  = 'NPO_LOGGING_DEMO.OBSERVABILITY.PIPELINE_EVENTS';
SET warehouse    = 'COMPUTE_WH';
SET compute_pool = 'SYSTEM_COMPUTE_POOL_CPU';
SET runtime      = 'V2.2-CPU-PY3.11';

USE ROLE ACCOUNTADMIN;
USE DATABASE NPO_LOGGING_DEMO;
USE SCHEMA PIPELINE;

-- ============================================================
-- Option A: Execute NPO Manually (non-interactive)
-- ============================================================
EXECUTE NOTEBOOK PROJECT NPO_LOGGING_DEMO.PIPELINE.LOGGING_DEMO_PROJECT
  MAIN_FILE = 'npo_logging_demo.ipynb'
  COMPUTE_POOL = $compute_pool
  QUERY_WAREHOUSE = $warehouse
  RUNTIME = $runtime;

-- ============================================================
-- Option B: Execute via Task (simulates scheduled run)
-- ============================================================
-- EXECUTE TASK NPO_LOGGING_DEMO.PIPELINE.LOGGING_DEMO_TASK;

-- Check task status (wait ~60 seconds after EXECUTE TASK)
SELECT STATE, ERROR_MESSAGE, SCHEDULED_TIME, COMPLETED_TIME
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => 'LOGGING_DEMO_TASK',
    SCHEDULED_TIME_RANGE_START => DATEADD(minute, -10, CURRENT_TIMESTAMP())
))
ORDER BY SCHEDULED_TIME DESC LIMIT 5;

-- ============================================================
-- QUERY RESULTS
-- NOTE: 3-5 minute delay before logs appear in the event table.
-- ============================================================

-- Show ALL log records from NPO executions in the last hour
SELECT
  TIMESTAMP,
  RECORD_TYPE,
  RECORD:severity_text::STRING AS SEVERITY,
  VALUE::STRING AS LOG_MESSAGE,
  RESOURCE_ATTRIBUTES:"snow.service.name"::STRING AS SERVICE_NAME
FROM IDENTIFIER($event_table)
WHERE TIMESTAMP > DATEADD(hour, -1, CURRENT_TIMESTAMP())
  AND RECORD_TYPE = 'LOG'
  AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
ORDER BY TIMESTAMP DESC
LIMIT 100;

-- ============================================================
-- KEY TEST: print() output (WILL RETURN EMPTY)
-- ============================================================
SELECT
  TIMESTAMP, RECORD_TYPE, VALUE::STRING AS MESSAGE
FROM IDENTIFIER($event_table)
WHERE TIMESTAMP > DATEADD(hour, -1, CURRENT_TIMESTAMP())
  AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
  AND VALUE::STRING LIKE '%PRINT-TEST%'
ORDER BY TIMESTAMP DESC;
-- Expected: 0 rows

-- ============================================================
-- KEY TEST: logging module output (WILL RETURN DATA)
-- ============================================================
SELECT
  TIMESTAMP, RECORD_TYPE, RECORD:severity_text::STRING AS SEVERITY, VALUE::STRING AS MESSAGE
FROM IDENTIFIER($event_table)
WHERE TIMESTAMP > DATEADD(hour, -1, CURRENT_TIMESTAMP())
  AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
  AND VALUE::STRING LIKE '%LOG-TEST%'
ORDER BY TIMESTAMP DESC;
-- Expected: INFO, WARNING, ERROR, CRITICAL, STRUCTURED (no DEBUG at LOG_EVENT_LEVEL=INFO)

-- ============================================================
-- Container lifecycle events (PENDING -> READY -> DONE)
-- ============================================================
SELECT
  TIMESTAMP,
  RECORD:severity_text::STRING AS SEVERITY,
  VALUE::STRING AS EVENT_MESSAGE,
  RESOURCE_ATTRIBUTES:"snow.service.container.name"::STRING AS CONTAINER
FROM IDENTIFIER($event_table)
WHERE TIMESTAMP > DATEADD(hour, -1, CURRENT_TIMESTAMP())
  AND RECORD_TYPE = 'EVENT'
  AND RESOURCE_ATTRIBUTES:"snow.executable.type" = 'NOTEBOOK'
ORDER BY TIMESTAMP DESC
LIMIT 20;
