-- =============================================================================
-- Demo 2b: Querying the Semantic View
-- =============================================================================
-- This worksheet demonstrates querying the MANUFACTURING_OPERATIONS semantic view.
-- The semantic view provides governed, centrally-defined metrics — replacing
-- fragmented PowerBI semantic models with a single source of truth.
--
-- Semantic View: MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Explore what's available in the semantic view
-- -----------------------------------------------------------------------------
SHOW SEMANTIC METRICS IN MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS;

SHOW SEMANTIC DIMENSIONS IN MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS;

-- -----------------------------------------------------------------------------
-- 2. Simple metric query: OEE by production line
-- "Which lines are underperforming?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.production_line
  METRICS daily_production_metrics.oee, daily_production_metrics.throughput
)
ORDER BY oee;

-- -----------------------------------------------------------------------------
-- 3. OEE broken down into components (Availability, Performance, Quality)
-- "Where is the loss?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.production_line
  METRICS daily_production_metrics.availability,
          daily_production_metrics.performance,
          daily_production_metrics.quality,
          daily_production_metrics.oee
)
ORDER BY oee;

-- -----------------------------------------------------------------------------
-- 4. OEE trend over time (weekly)
-- "Is it getting better or worse?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.production_date
  METRICS daily_production_metrics.oee, daily_production_metrics.throughput
)
ORDER BY production_date;

-- -----------------------------------------------------------------------------
-- 5. Scrap rate by product
-- "Which products have the most waste?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.product_name
  METRICS daily_production_metrics.scrap_rate, daily_production_metrics.throughput
)
ORDER BY scrap_rate DESC;

-- -----------------------------------------------------------------------------
-- 6. Downtime by shift
-- "Which shift has the most unplanned downtime?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.shift
  METRICS daily_production_metrics.total_downtime_minutes, daily_production_metrics.oee
)
ORDER BY total_downtime_minutes DESC;

-- -----------------------------------------------------------------------------
-- 7. Work order status summary
-- "How many orders are at risk?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS work_orders.status
  METRICS work_orders.order_count, work_orders.total_quantity
);

-- -----------------------------------------------------------------------------
-- 8. At-risk work orders by production line
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS work_orders.production_line
  METRICS work_orders.at_risk_count, work_orders.order_count
)
ORDER BY at_risk_count DESC;

-- -----------------------------------------------------------------------------
-- 9. Open issues by type
-- "What kinds of problems are we having?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS issues.issue_type
  METRICS issues.open_issue_count
);

-- -----------------------------------------------------------------------------
-- 10. Filter with WHERE — OEE for a specific line
-- "How is CNC Machining performing this month?"
-- -----------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS
  DIMENSIONS daily_production_metrics.production_date
  METRICS daily_production_metrics.oee, daily_production_metrics.throughput
  WHERE daily_production_metrics.production_line = 'CNC Machining Bay A'
)
ORDER BY production_date;

-- =============================================================================
-- KEY TAKEAWAY:
-- Every metric above uses the SAME governed definition. OEE is always
-- AVG(Availability x Performance x Quality). Throughput is always
-- SUM(GOOD_UNITS_PRODUCED). There's no ambiguity, no per-report DAX logic.
--
-- This is what replaces the PowerBI semantic model — but it's enforced by the
-- platform, consumed by every tool (apps, agents, SQL, notebooks), and
-- governed via Snowflake RBAC.
-- =============================================================================
