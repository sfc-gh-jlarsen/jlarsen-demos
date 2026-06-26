-- ============================================================
-- 99: Teardown — Remove all demo objects
-- ============================================================

USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS MFG_SCHEDULING_REPORTING;
DROP WAREHOUSE IF EXISTS MFG_REPORTING_WH;
DROP ROLE IF EXISTS mfg_plant_manager;
DROP ROLE IF EXISTS mfg_scheduler;
DROP ROLE IF EXISTS mfg_platform_admin;
