-- ============================================================
-- 04: Semantic View
-- ============================================================
-- Upload the YAML first:
--   PUT file://demo2b_governed_with_agent/manufacturing_semantic_view.yaml
--       @MFG_SCHEDULING_REPORTING.ANALYTICS.MODELS
--       AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

USE DATABASE MFG_SCHEDULING_REPORTING;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE SEMANTIC VIEW MANUFACTURING_OPERATIONS
    FROM @MFG_SCHEDULING_REPORTING.ANALYTICS.MODELS/manufacturing_semantic_view.yaml;

-- Grant access
GRANT SELECT ON SEMANTIC VIEW MANUFACTURING_OPERATIONS TO ROLE mfg_plant_manager;
GRANT SELECT ON SEMANTIC VIEW MANUFACTURING_OPERATIONS TO ROLE mfg_scheduler;
