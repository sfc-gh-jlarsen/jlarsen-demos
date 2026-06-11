/*
==============================================================================
NPO Logging Demo: Cleanup
==============================================================================
*/

SET demo_db = 'NPO_LOGGING_DEMO';

USE ROLE ACCOUNTADMIN;

ALTER TASK NPO_LOGGING_DEMO.PIPELINE.LOGGING_DEMO_TASK SUSPEND;
DROP DATABASE IF EXISTS IDENTIFIER($demo_db);

-- NOTE: This does NOT reset account-level settings.
-- Uncomment below to revert account telemetry to defaults:
-- ALTER ACCOUNT SET EVENT_TABLE = 'snowflake.telemetry.events';
-- ALTER ACCOUNT SET LOG_LEVEL = 'OFF';
-- ALTER ACCOUNT SET LOG_EVENT_LEVEL = 'OFF';
-- ALTER ACCOUNT SET TRACE_LEVEL = 'OFF';
-- ALTER ACCOUNT SET METRIC_LEVEL = 'NONE';
