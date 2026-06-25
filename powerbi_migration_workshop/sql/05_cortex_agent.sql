-- ============================================================
-- 05: Cortex Agent with Analyst Tool
-- ============================================================

USE DATABASE MFG_SCHEDULING_REPORTING;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE CORTEX AGENT PRODUCTION_ANALYST
    COMMENT = 'Manufacturing production analyst agent for natural language Q&A'
    MODEL = 'claude-3.5-sonnet'
    TOOLS = (
        cortex_analyst_tool(
            semantic_view => 'MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS'
        )
    )
    SYSTEM_PROMPT = '
You are a manufacturing production analyst. You help plant managers and schedulers
understand production performance by querying the manufacturing operations semantic view.

When answering questions:
- Reference specific metrics (OEE, availability, performance, quality, throughput)
- Compare to targets (OEE target: 85%, OTD target: 95%)
- Identify root causes when metrics are below target
- Be concise and reference specific numbers from the data
';

-- Grant usage
GRANT USAGE ON CORTEX AGENT PRODUCTION_ANALYST TO ROLE mfg_plant_manager;
