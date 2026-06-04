/*
=============================================================================
  CORTEX AGENT - Updating Orchestration Instructions Without Overwriting
=============================================================================

  USE CASE:
  "I want to add an additional orchestration instruction to the Cortex agent,
   but when I asked COCO about this, it said that doing so would omit the
   other fields and overwrite the existing orchestration."

  THE ANSWER:
  ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION replaces the ENTIRE
  spec. The recommended pattern is:
    1. DESCRIBE AGENT to get the current spec
    2. Modify the field you want (in-app or via script)
    3. ALTER AGENT with the FULL updated spec

  This walkthrough demonstrates the pattern end-to-end.
=============================================================================
*/

-- ============================================
-- STEP 1: Setup - Create the demo agent
-- ============================================

CREATE DATABASE IF NOT EXISTS USER_LOOKUP_DEMO;
CREATE SCHEMA IF NOT EXISTS USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO;

-- Sample user directory
CREATE OR REPLACE TABLE USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_DIRECTORY (
    UPIN VARCHAR(10),
    DISPLAY_NAME VARCHAR(100),
    EMAIL VARCHAR(100),
    DEPARTMENT VARCHAR(50),
    ACCESS_LEVEL VARCHAR(20),
    STATUS VARCHAR(10)
);

INSERT INTO USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_DIRECTORY VALUES
('U1001', 'Alice Johnson', 'alice.johnson@company.com', 'Engineering', 'Admin', 'Active'),
('U1002', 'Bob Smith', 'bob.smith@company.com', 'Sales', 'Standard', 'Active'),
('U1003', 'Carol Davis', 'carol.davis@company.com', 'Finance', 'Elevated', 'Active'),
('U1004', 'David Lee', 'david.lee@company.com', 'Engineering', 'Standard', 'Active'),
('U1005', 'Eva Martinez', 'eva.martinez@company.com', 'HR', 'Admin', 'Active');

-- Cortex Search Service on the directory
CREATE OR REPLACE CORTEX SEARCH SERVICE USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_SEARCH
    ON DISPLAY_NAME
    ATTRIBUTES UPIN, EMAIL, DEPARTMENT, ACCESS_LEVEL, STATUS
    WAREHOUSE = COMPUTE_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT UPIN, DISPLAY_NAME, EMAIL, DEPARTMENT, ACCESS_LEVEL, STATUS
        FROM USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_DIRECTORY
        WHERE STATUS = 'Active'
    );

-- Create the agent with INITIAL instructions (no PIN requirement yet)
CREATE OR REPLACE AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT
COMMENT = 'Demo agent for user directory lookups'
FROM SPECIFICATION
$$
models:
  orchestration: auto

instructions:
  orchestration: "You are a user directory assistant. Help users find information about employees in the directory. Use the search tool to look up users by name."
  response: "Be concise. Format results in a clear, readable manner."

tools:
  - tool_spec:
      type: "cortex_search"
      name: "search_users"
      description: "Search the employee directory by name to find user details including UPIN, email, department, and access level."

tool_resources:
  search_users:
    name: "USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_SEARCH"
    id_column: "UPIN"
    title_column: "DISPLAY_NAME"
    max_results: 5
$$;


-- ============================================
-- STEP 2: Verify the current spec
-- ============================================

DESCRIBE AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT;
-- Note the agent_spec column - this is what we need to preserve


-- ============================================
-- STEP 3: ALTER AGENT - Add PIN Requirement
-- ============================================

/*
  KEY INSIGHT from the docs:
  "The new specification completely replaces the existing one.
   Fields that are not included in the new specification are removed."

  This means you MUST include ALL fields (models, tools, tool_resources, etc.)
  when you alter the spec - not just the field you're changing.

  The pattern is: GET full spec -> MODIFY what you need -> PUT full spec back.
*/

ALTER AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT
  MODIFY LIVE VERSION SET SPECIFICATION =
  $$
  models:
    orchestration: auto

  instructions:
    orchestration: |
      You are a user directory assistant. Help users find information about employees in the directory. Use the search tool to look up users by name.

      IMPORTANT - PIN VERIFICATION REQUIREMENT:
      When a user asks about their OWN information (e.g., "what is my access level", "show my profile", "what groups am I in"), you MUST ask them to provide their 4-digit PIN before revealing any personal information. Do NOT proceed without PIN verification for self-lookup requests.

      For lookups about OTHER users (e.g., "find Alice Johnson", "who is in Engineering"), no PIN is required.
    response: "Be concise. Format results in a clear, readable manner."

  tools:
    - tool_spec:
        type: "cortex_search"
        name: "search_users"
        description: "Search the employee directory by name to find user details including UPIN, email, department, and access level."

  tool_resources:
    search_users:
      name: "USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_SEARCH"
      id_column: "UPIN"
      title_column: "DISPLAY_NAME"
      max_results: 5
  $$;


-- ============================================
-- STEP 4: Verify the update
-- ============================================

DESCRIBE AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT;


-- ============================================
-- STEP 5: Test the agent
-- ============================================

-- Test: Lookup another user (should NOT require PIN)
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT',
    $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Find Alice Johnson"}]}]}$$
);

-- Test: Self-lookup (SHOULD trigger PIN requirement)
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT',
    $${"messages": [{"role": "user", "content": [{"type": "text", "text": "What is my access level?"}]}]}$$
);


-- ============================================
-- CLEANUP
-- ============================================
-- DROP AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT;
-- DROP CORTEX SEARCH SERVICE USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_SEARCH;
-- DROP TABLE USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_DIRECTORY;
-- DROP SCHEMA USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO;
