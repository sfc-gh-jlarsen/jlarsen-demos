-- =============================================================================
-- Demo 2a: Plant Performance Queries
-- =============================================================================
-- Run these in order to explore the production data before building a dashboard.
-- This is the "old world" workflow — querying manually, then needing to export
-- to PowerBI for visualization. We'll replace that with SiS in the next step.
-- =============================================================================

USE DATABASE MFG_SCHEDULING_REPORTING;
USE SCHEMA RAW;

-- -----------------------------------------------------------------------------
-- 1. OEE by Production Line (last week)
-- "Which lines are underperforming?"
-- -----------------------------------------------------------------------------
SELECT LINE_NAME,
       ROUND(AVG(AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT) * 100, 1) AS oee_pct,
       SUM(GOOD_UNITS_PRODUCED) AS weekly_throughput,
       SUM(DOWNTIME_MINUTES) AS total_downtime_min
FROM DAILY_PRODUCTION_METRICS
WHERE PLANT_ID = 'DET01'
  AND PRODUCTION_DATE >= DATEADD(week, -1, CURRENT_DATE())
GROUP BY LINE_NAME
ORDER BY oee_pct;

-- -----------------------------------------------------------------------------
-- 2. OEE Trend (8 weeks) — is it getting better or worse?
-- -----------------------------------------------------------------------------
SELECT DATE_TRUNC('week', PRODUCTION_DATE) AS week_start,
       ROUND(AVG(AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT) * 100, 1) AS oee_pct
FROM DAILY_PRODUCTION_METRICS
WHERE PLANT_ID = 'DET01'
  AND PRODUCTION_DATE >= DATEADD(week, -8, CURRENT_DATE())
GROUP BY 1
ORDER BY 1;

-- -----------------------------------------------------------------------------
-- 3. OEE Breakdown — where is the loss?
-- -----------------------------------------------------------------------------
SELECT ROUND(AVG(AVAILABILITY_PCT) * 100, 1) AS avg_availability,
       ROUND(AVG(PERFORMANCE_PCT) * 100, 1) AS avg_performance,
       ROUND(AVG(QUALITY_PCT) * 100, 1) AS avg_quality,
       ROUND(AVG(AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT) * 100, 1) AS oee
FROM DAILY_PRODUCTION_METRICS
WHERE PLANT_ID = 'DET01'
  AND PRODUCTION_DATE >= DATEADD(week, -1, CURRENT_DATE());

-- -----------------------------------------------------------------------------
-- 4. On-Time Delivery — are we hitting our commitments?
-- -----------------------------------------------------------------------------
SELECT COUNT_IF(ON_TIME) AS on_time_count,
       COUNT(*) AS total_orders,
       ROUND(COUNT_IF(ON_TIME) / NULLIF(COUNT(*), 0) * 100, 1) AS otd_pct
FROM DELIVERIES
WHERE PLANT_ID = 'DET01';

-- -----------------------------------------------------------------------------
-- 5. At-Risk Deliveries — what's going to miss?
-- -----------------------------------------------------------------------------
SELECT WO_ID, PRODUCT_NAME, PROMISE_DATE,
       DATEDIFF(day, CURRENT_DATE(), PROMISE_DATE) AS days_until_due,
       RISK_REASON
FROM DELIVERIES
WHERE PLANT_ID = 'DET01'
  AND ON_TIME = FALSE
ORDER BY PROMISE_DATE;

-- -----------------------------------------------------------------------------
-- 6. Open Issues — what's blocking production right now?
-- -----------------------------------------------------------------------------
SELECT ISSUE_ID, PRODUCTION_LINE, ISSUE_TYPE, SEVERITY, DESCRIPTION,
       DATEDIFF(hour, CREATED_AT, CURRENT_TIMESTAMP()) AS hours_open
FROM ISSUES
WHERE PLANT_ID = 'DET01'
  AND STATUS = 'Open'
ORDER BY SEVERITY, CREATED_AT;

-- =============================================================================
-- "I can see the data. CNC Machining is underperforming, we have 3 at-risk
-- deliveries, and 4 open issues. But I need to VISUALIZE this, filter it
-- interactively, share it with my team. In the old world, I'd open PowerBI
-- Desktop and start building a .pbix file..."
--
-- NEXT: Open a new Streamlit app and use the AI prompt in DEMO_SCRIPT.md
-- =============================================================================
