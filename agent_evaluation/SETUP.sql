-- ====================================================================
-- SUPPLY CHAIN ORDER ANALYTICS - COMPLETE SETUP SCRIPT
-- ====================================================================
-- This script creates a complete supply chain analytics system with:
-- - Database and tables with sample data
-- - Semantic view for Cortex Analyst
-- - Cortex Search service for order notes
-- - Stored procedure for report generation
-- - Cortex Agent integrating all tools
-- - Evaluation dataset and configuration
--
-- Prerequisites:
-- - ACCOUNTADMIN role
-- - COMPUTE_WH warehouse
-- - Cross-region inference enabled (for eval LLM judges)
--
-- Estimated runtime: 5-10 minutes
-- ====================================================================

-- ====================================================================
-- SECTION 1: DATABASE AND SCHEMA CREATION
-- ====================================================================

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS AGENT_EVALUATION_DEMO;
CREATE OR REPLACE SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN;
USE SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN;
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH WAREHOUSE_SIZE='SMALL';
USE WAREHOUSE COMPUTE_WH;

-- ====================================================================
-- SECTION 2: ROLE CONFIGURATION
-- ====================================================================

CREATE OR REPLACE ROLE SUPPLY_CHAIN_EVAL_ROLE;

SET EVAL_USER = CURRENT_USER();
GRANT ROLE SUPPLY_CHAIN_EVAL_ROLE TO USER IDENTIFIER($EVAL_USER);

GRANT USAGE ON DATABASE AGENT_EVALUATION_DEMO TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT USAGE ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE TABLE ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE STAGE ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE VIEW ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT APPLICATION ROLE SNOWFLAKE.AI_OBSERVABILITY_EVENTS_LOOKUP TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT CREATE FILE FORMAT ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE DATASET ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT CREATE TASK ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT MONITOR ON FUTURE AGENTS IN SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

GRANT CREATE SEMANTIC VIEW ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE PROCEDURE ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;
GRANT CREATE AGENT ON SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN TO ROLE SUPPLY_CHAIN_EVAL_ROLE;

-- ====================================================================
-- SECTION 3: FILE FORMAT AND DATA STAGE
-- ====================================================================

USE ROLE SUPPLY_CHAIN_EVAL_ROLE;
USE SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN;
USE WAREHOUSE COMPUTE_WH;

CREATE OR REPLACE FILE FORMAT SC_CSV_FORMAT
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  COMPRESSION = 'AUTO';

CREATE OR REPLACE STAGE DATA_STAGE
  FILE_FORMAT = SC_CSV_FORMAT
  COMMENT = 'Stage for loading supply chain CSV data';

-- ====================================================================
-- SECTION 4: UPLOAD CSV FILES
-- ====================================================================
-- Option A (recommended): Run upload_files.py from the project root
--   python upload_files.py
--
-- Option B: Use PUT from SnowSQL (update paths to your local clone)
--   PUT file://<path-to-repo>/data/SALES_ORDERS.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--   PUT file://<path-to-repo>/data/ORDER_LINE_ITEMS.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--   PUT file://<path-to-repo>/data/ORDER_FULFILLMENT.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--   PUT file://<path-to-repo>/data/ORDER_NOTES.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--   PUT file://<path-to-repo>/data/EVALS_TABLE.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
--
-- After uploading, verify files are present:

LS @DATA_STAGE;

-- ====================================================================
-- SECTION 5: CREATE AND POPULATE TABLES
-- ====================================================================

CREATE OR REPLACE TABLE SALES_ORDERS (
    order_id INT,
    customer_name VARCHAR(200) NOT NULL,
    region VARCHAR(50),
    order_date DATE,
    requested_ship_date DATE,
    status VARCHAR(50),
    priority VARCHAR(50),
    channel VARCHAR(50),
    sales_rep VARCHAR(100)
);

INSERT INTO SALES_ORDERS (order_id, customer_name, region, order_date, requested_ship_date, status, priority, channel, sales_rep)
SELECT $1,$2,$3,$4,$5,$6,$7,$8,$9
FROM @DATA_STAGE/SALES_ORDERS.csv (FILE_FORMAT => SC_CSV_FORMAT);

CREATE OR REPLACE TABLE ORDER_LINE_ITEMS (
    line_item_id INT,
    order_id INT,
    product_name VARCHAR(200),
    category VARCHAR(100),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_pct DECIMAL(5,2),
    total_amount DECIMAL(12,2)
);

INSERT INTO ORDER_LINE_ITEMS (line_item_id, order_id, product_name, category, quantity, unit_price, discount_pct, total_amount)
SELECT $1,$2,$3,$4,$5,$6,$7,$8
FROM @DATA_STAGE/ORDER_LINE_ITEMS.csv (FILE_FORMAT => SC_CSV_FORMAT);

CREATE OR REPLACE TABLE ORDER_FULFILLMENT (
    fulfillment_id INT,
    order_id INT,
    ship_date DATE,
    warehouse VARCHAR(50),
    on_time BOOLEAN,
    days_to_ship INT,
    shipping_cost DECIMAL(10,2),
    carrier VARCHAR(50)
);

INSERT INTO ORDER_FULFILLMENT (fulfillment_id, order_id, ship_date, warehouse, on_time, days_to_ship, shipping_cost, carrier)
SELECT $1,$2,$3,$4,$5,$6,$7,$8
FROM @DATA_STAGE/ORDER_FULFILLMENT.csv (FILE_FORMAT => SC_CSV_FORMAT);

CREATE OR REPLACE TABLE ORDER_NOTES (
    note_id INT,
    order_id INT,
    note_type VARCHAR(50),
    note_content TEXT
);

INSERT INTO ORDER_NOTES (note_id, order_id, note_type, note_content)
SELECT $1,$2,$3,$4
FROM @DATA_STAGE/ORDER_NOTES.csv (FILE_FORMAT => SC_CSV_FORMAT);

CREATE OR REPLACE TABLE EVALS_TABLE (
    INPUT_QUERY TEXT,
    GROUND_TRUTH_DATA VARCHAR
);

INSERT INTO EVALS_TABLE (INPUT_QUERY, GROUND_TRUTH_DATA)
SELECT $1, $2
FROM @DATA_STAGE/EVALS_TABLE.csv (FILE_FORMAT => SC_CSV_FORMAT);

CREATE OR REPLACE TABLE EVALS_TABLE AS
SELECT INPUT_QUERY, PARSE_JSON(GROUND_TRUTH_DATA) AS GROUND_TRUTH_DATA
FROM EVALS_TABLE;

-- ====================================================================
-- SECTION 6: VALIDATE DATA
-- ====================================================================

SELECT 'SALES_ORDERS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM SALES_ORDERS
UNION ALL
SELECT 'ORDER_LINE_ITEMS', COUNT(*) FROM ORDER_LINE_ITEMS
UNION ALL
SELECT 'ORDER_FULFILLMENT', COUNT(*) FROM ORDER_FULFILLMENT
UNION ALL
SELECT 'ORDER_NOTES', COUNT(*) FROM ORDER_NOTES
UNION ALL
SELECT 'EVALS_TABLE', COUNT(*) FROM EVALS_TABLE;

-- ====================================================================
-- SECTION 7: CREATE SEMANTIC VIEW
-- ====================================================================

CREATE OR REPLACE SEMANTIC VIEW SUPPLY_CHAIN_ANALYST
  TABLES (
    orders AS SALES_ORDERS PRIMARY KEY (order_id),
    line_items AS ORDER_LINE_ITEMS PRIMARY KEY (line_item_id),
    fulfillment AS ORDER_FULFILLMENT PRIMARY KEY (fulfillment_id)
  )
  RELATIONSHIPS (
    line_items(order_id) REFERENCES orders(order_id),
    fulfillment(order_id) REFERENCES orders(order_id)
  )
  DIMENSIONS (
    PUBLIC orders.order_id AS order_id,
    PUBLIC orders.customer_name AS customer_name,
    PUBLIC orders.region AS region,
    PUBLIC orders.status AS status,
    PUBLIC orders.priority AS priority,
    PUBLIC orders.channel AS channel,
    PUBLIC orders.sales_rep AS sales_rep,
    PUBLIC orders.order_date AS order_date,
    PUBLIC orders.requested_ship_date AS requested_ship_date,
    PUBLIC line_items.product_name AS product_name,
    PUBLIC line_items.category AS category,
    PUBLIC fulfillment.warehouse AS warehouse,
    PUBLIC fulfillment.carrier AS carrier,
    PUBLIC fulfillment.ship_date AS ship_date,
    PUBLIC fulfillment.on_time AS on_time
  )
  METRICS (
    PUBLIC line_items.total_revenue AS SUM(total_amount),
    PUBLIC orders.total_orders AS COUNT(DISTINCT order_id),
    PUBLIC line_items.total_quantity AS SUM(quantity),
    PUBLIC line_items.avg_unit_price AS AVG(unit_price),
    PUBLIC line_items.avg_discount AS AVG(discount_pct),
    PUBLIC fulfillment.avg_days_to_ship AS AVG(days_to_ship),
    PUBLIC fulfillment.avg_shipping_cost AS AVG(shipping_cost),
    PUBLIC fulfillment.total_shipping_cost AS SUM(shipping_cost),
    PUBLIC fulfillment.on_time_count AS SUM(CASE WHEN on_time THEN 1 ELSE 0 END),
    PUBLIC fulfillment.total_fulfillments AS COUNT(fulfillment_id)
  )
  COMMENT = 'Semantic view for analyzing supply chain order performance, fulfillment, and revenue';

SHOW SEMANTIC VIEWS LIKE 'SUPPLY_CHAIN_ANALYST';

-- ====================================================================
-- SECTION 8: CREATE CORTEX SEARCH SERVICE
-- ====================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE ORDER_NOTES_SEARCH
  ON combined_text
  ATTRIBUTES order_id, note_type, customer_name
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
AS (
    SELECT
      n.note_id,
      n.order_id,
      n.note_type,
      o.customer_name,
      o.region,
      CONCAT(
        'Order: ', o.order_id, ' | ',
        'Customer: ', o.customer_name, ' | ',
        'Region: ', o.region, ' | ',
        'Status: ', o.status, ' | ',
        'Priority: ', o.priority, ' | ',
        'Note Type: ', n.note_type, ' | ',
        'Content: ', n.note_content
      ) AS combined_text
    FROM ORDER_NOTES n
    JOIN SALES_ORDERS o ON n.order_id = o.order_id
);

SHOW CORTEX SEARCH SERVICES LIKE 'ORDER_NOTES_SEARCH';

-- ====================================================================
-- SECTION 9: CREATE REPORT GENERATION STORED PROCEDURE
-- ====================================================================

CREATE OR REPLACE STAGE ORDER_REPORTS
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Internal stage to host generated order reports';

CREATE OR REPLACE PROCEDURE GENERATE_ORDER_SUMMARY_REPORT(p_order_id NUMBER)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  report_html VARCHAR;
  order_info VARCHAR;
  line_items_html VARCHAR;
  fulfillment_html VARCHAR;
  file_name VARCHAR;
  upload_result VARCHAR;
  org_name VARCHAR;
  account_name VARCHAR;
BEGIN
  SELECT
    '<h1>Order Summary Report</h1>' ||
    '<h2>Order #' || order_id || ' - ' || customer_name || '</h2>' ||
    '<table border="1" style="border-collapse:collapse; width:100%">' ||
    '<tr><th>Field</th><th>Value</th></tr>' ||
    '<tr><td>Region</td><td>' || region || '</td></tr>' ||
    '<tr><td>Order Date</td><td>' || order_date || '</td></tr>' ||
    '<tr><td>Requested Ship Date</td><td>' || requested_ship_date || '</td></tr>' ||
    '<tr><td>Status</td><td>' || status || '</td></tr>' ||
    '<tr><td>Priority</td><td>' || priority || '</td></tr>' ||
    '<tr><td>Channel</td><td>' || channel || '</td></tr>' ||
    '<tr><td>Sales Rep</td><td>' || sales_rep || '</td></tr>' ||
    '</table>'
  INTO order_info
  FROM SALES_ORDERS
  WHERE order_id = :p_order_id;

  SELECT
    '<h3>Line Items</h3>' ||
    '<table border="1" style="border-collapse:collapse; width:100%">' ||
    '<tr><th>Product</th><th>Category</th><th>Qty</th><th>Unit Price</th><th>Discount</th><th>Total</th></tr>' ||
    LISTAGG(
      '<tr><td>' || product_name || '</td>' ||
      '<td>' || category || '</td>' ||
      '<td>' || quantity || '</td>' ||
      '<td>$' || unit_price || '</td>' ||
      '<td>' || discount_pct || '%</td>' ||
      '<td>$' || total_amount || '</td></tr>',
      ''
    ) WITHIN GROUP (ORDER BY line_item_id) ||
    '</table>' ||
    '<p><strong>Order Total: $' || TO_CHAR(SUM(total_amount), '999,999,999.99') || '</strong></p>'
  INTO line_items_html
  FROM ORDER_LINE_ITEMS
  WHERE order_id = :p_order_id;

  SELECT
    '<h3>Fulfillment Details</h3>' ||
    '<table border="1" style="border-collapse:collapse; width:100%">' ||
    '<tr><th>Ship Date</th><th>Warehouse</th><th>On Time</th><th>Days to Ship</th><th>Shipping Cost</th><th>Carrier</th></tr>' ||
    LISTAGG(
      '<tr><td>' || ship_date || '</td>' ||
      '<td>' || warehouse || '</td>' ||
      '<td>' || CASE WHEN on_time THEN 'Yes' ELSE 'No' END || '</td>' ||
      '<td>' || days_to_ship || '</td>' ||
      '<td>$' || shipping_cost || '</td>' ||
      '<td>' || carrier || '</td></tr>',
      ''
    ) WITHIN GROUP (ORDER BY fulfillment_id) ||
    '</table>'
  INTO fulfillment_html
  FROM ORDER_FULFILLMENT
  WHERE order_id = :p_order_id;

  report_html :=
    '<!DOCTYPE html><html><head><style>' ||
    'body { font-family: Arial, sans-serif; margin: 20px; }' ||
    'table { margin: 20px 0; }' ||
    'th { background-color: #2196F3; color: white; padding: 10px; text-align: left; }' ||
    'td { padding: 10px; }' ||
    'tr:nth-child(even) { background-color: #f2f2f2; }' ||
    '</style></head><body>' ||
    order_info ||
    COALESCE(line_items_html, '<p>No line items found</p>') ||
    COALESCE(fulfillment_html, '<p>No fulfillment data available</p>') ||
    '<hr><p style="text-align:center; color:#666;">Report Generated: ' || CURRENT_TIMESTAMP() || '</p>' ||
    '</body></html>';

  file_name := 'ORDER_' || p_order_id || '_' || TO_CHAR(CURRENT_TIMESTAMP(), 'YYYY-MM-DD_HH_MI') || '.html';

  EXECUTE IMMEDIATE '
    CREATE OR REPLACE FILE FORMAT html_format
    TYPE = ''CSV''
    FIELD_DELIMITER = NONE
    RECORD_DELIMITER = NONE
    SKIP_HEADER = 0
    FIELD_OPTIONALLY_ENCLOSED_BY = NONE
    ESCAPE_UNENCLOSED_FIELD = NONE
    COMPRESSION = NONE
    ENCODING = ''UTF8''
  ';

  EXECUTE IMMEDIATE 'CREATE OR REPLACE TEMPORARY TABLE temp_report_' || p_order_id || ' (html_content VARCHAR(16777216))';
  EXECUTE IMMEDIATE 'INSERT INTO temp_report_' || p_order_id || ' VALUES (?)' USING (report_html);
  EXECUTE IMMEDIATE
    'COPY INTO @ORDER_REPORTS/' || file_name ||
    ' FROM (SELECT html_content FROM temp_report_' || p_order_id || ')' ||
    ' FILE_FORMAT = html_format' ||
    ' SINGLE = TRUE OVERWRITE = TRUE HEADER = FALSE';
  EXECUTE IMMEDIATE 'DROP TABLE temp_report_' || p_order_id;

  SELECT CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME()
  INTO org_name, account_name;

  upload_result := 'Report ' || file_name || ' generated and uploaded to stage. View here - https://app.snowflake.com/' || org_name || '/' || account_name || '/#/data/databases/AGENT_EVALUATION_DEMO/schemas/SUPPLY_CHAIN/stage/ORDER_REPORTS';

  RETURN upload_result;
END;
$$;

SHOW PROCEDURES LIKE 'GENERATE_ORDER_SUMMARY_REPORT';

-- ====================================================================
-- SECTION 10: CREATE CORTEX AGENT (BASELINE - minimal instructions)
-- ====================================================================

CREATE OR REPLACE AGENT SUPPLY_CHAIN_AGENT
WITH PROFILE = '{ "display_name": "SUPPLY_CHAIN_AGENT" }'
    COMMENT = $$ Agent specializing in supply chain order analytics, fulfillment tracking, and order note insights. $$
FROM SPECIFICATION $$
{
    "models": {"orchestration": "auto"},
    "instructions": {
        "orchestration": "",
        "response": "",
        "sample_questions": [
            {"question": "What is the total revenue by region?"},
            {"question": "Which warehouse has the best on-time delivery rate?"},
            {"question": "What shipping delays have been reported?"},
            {"question": "Generate a report for order 5"}
        ]
    },
    "tools": [
        {
            "tool_spec": {
                "type": "cortex_analyst_text_to_sql",
                "name": "query_order_metrics",
                "description": "Query structured order performance data including revenue, shipping metrics, and fulfillment KPIs."
            }
        },
        {
            "tool_spec": {
                "type": "cortex_search",
                "name": "search_order_notes",
                "description": "Search order notes for issues, feedback, resolutions, and escalations."
            }
        },
        {
            "tool_spec": {
                "type": "generic",
                "name": "generate_order_report",
                "description": "Generate an HTML report for a specific order.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "integer",
                            "description": "The order ID to generate a report for"
                        }
                    },
                    "required": ["order_id"]
                }
            }
        }
    ],
    "tool_resources": {
        "query_order_metrics": {
            "execution_environment": {
                "query_timeout": 299,
                "type": "warehouse",
                "warehouse": "COMPUTE_WH"
            },
            "semantic_view": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.SUPPLY_CHAIN_ANALYST"
        },
        "search_order_notes": {
            "execution_environment": {
                "query_timeout": 299,
                "type": "warehouse",
                "warehouse": "COMPUTE_WH"
            },
            "search_service": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.ORDER_NOTES_SEARCH"
        },
        "generate_order_report": {
            "type": "procedure",
            "identifier": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.GENERATE_ORDER_SUMMARY_REPORT",
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            }
        }
    }
}
$$;

DESCRIBE AGENT SUPPLY_CHAIN_AGENT;

-- ====================================================================
-- SECTION 11: TEST SERVICES
-- ====================================================================

SELECT
    region,
    total_orders,
    total_revenue,
    avg_days_to_ship
FROM SEMANTIC_VIEW(
    SUPPLY_CHAIN_ANALYST
    DIMENSIONS region
    METRICS total_orders, total_revenue, avg_days_to_ship
);

SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'ORDER_NOTES_SEARCH',
        '{"query": "shipping delays", "columns": ["order_id", "note_type", "combined_text"], "limit": 3}'
    )
) AS search_results;

CALL GENERATE_ORDER_SUMMARY_REPORT(1);

-- ====================================================================
-- SECTION 12: CREATE EVALUATION DATASET
-- ====================================================================

CALL SYSTEM$CREATE_EVALUATION_DATASET(
    'Cortex Agent',
    'AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVALS_TABLE',
    'AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.SUPPLY_CHAIN_EVALSET',
    OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH_DATA')
);

SHOW DATASETS;

-- ====================================================================
-- SECTION 13: UPLOAD EVAL CONFIG AND RUN BASELINE EVALUATION
-- ====================================================================

CREATE OR REPLACE STAGE EVAL_CONFIG_STAGE
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Internal stage to host evaluation config files';

-- Upload eval config YAML (use upload_files.py or adjust path below)
-- PUT file://<path-to-repo>/supply_chain_eval_config.yaml @EVAL_CONFIG_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

LS @EVAL_CONFIG_STAGE;

CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'BASELINE_SUPPLY_CHAIN_EVAL'),
  '@AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVAL_CONFIG_STAGE/supply_chain_eval_config.yaml'
);

CALL EXECUTE_AI_EVALUATION(
  'STATUS',
  OBJECT_CONSTRUCT('run_name', 'BASELINE_SUPPLY_CHAIN_EVAL'),
  '@AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVAL_CONFIG_STAGE/supply_chain_eval_config.yaml'
);

-- ====================================================================
-- SECTION 14: OPTIMIZE AGENT (improved instructions and tool descriptions)
-- ====================================================================

ALTER AGENT SUPPLY_CHAIN_AGENT
MODIFY LIVE VERSION SET SPECIFICATION = $$
{
  "models": {"orchestration": "auto"},
  "instructions": {
    "orchestration": "You are a Supply Chain Order Analytics Agent with three specialized tools. Follow these routing rules:\n\n## Tool Routing Rules\n\n### Rule 1: Quantitative Analysis (query_order_metrics)\nUse for:\n- Revenue, order counts, totals, averages, rankings\n- Shipping metrics: days to ship, on-time rates, shipping costs\n- Comparisons by region, warehouse, carrier, channel, category\n- Time-series trends (monthly, quarterly revenue)\n- Keywords: revenue, ROI, cost, orders, average, rate, top, bottom, compare, trend\n\n### Rule 2: Qualitative Analysis (search_order_notes)\nUse for:\n- Order issues, delays, quality problems\n- Customer feedback and satisfaction comments\n- Escalations requiring attention\n- Resolution details and outcomes\n- Keywords: feedback, issue, delay, escalation, comment, quality, resolution\n\n### Rule 3: Report Generation (generate_order_report)\nUse ONLY when user explicitly requests a report.\n- FIRST use query_order_metrics to find the order_id if given a customer name\n- THEN call generate_order_report with the order_id\n- Share key highlights after generating\n\n### Rule 4: Multi-Tool Queries\nFor questions needing BOTH quantitative AND qualitative data:\n1. Use query_order_metrics for numbers first\n2. Then search_order_notes for qualitative context\n3. Combine in response\n\n### Rule 5: Out-of-Scope\nIf the query is outside supply chain analytics, explain your capabilities without calling tools.\n\n## Consistency Requirements\n- Minimize tool calls (aim for 1-2 per question)\n- Never use search_order_notes for numerical analysis\n- Never use query_order_metrics for text content or feedback",
    "response": "## Response Format\n- Lead with the direct answer\n- Use markdown: headers, bold, bullet points, tables for multi-row data\n- Include units (dollars, percentages, counts, days)\n- Format numbers with commas\n- Cite specific orders, customers, warehouses by name\n- Be concise, professional, data-driven\n- Never fabricate data\n- When data is unavailable, state what is missing",
    "sample_questions": [
      {"question": "What is the total revenue by region?"},
      {"question": "Which warehouse has the best on-time delivery rate?"},
      {"question": "What shipping delays have been reported?"},
      {"question": "Generate a report for order 5"}
    ]
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "query_order_metrics",
        "description": "Query structured supply chain data using natural language.\n\n## Data Available\n- Order metadata: order_id, customer_name, region, order_date, requested_ship_date, status, priority, channel, sales_rep\n- Line items: product_name, category, quantity, unit_price, discount_pct, total_amount\n- Fulfillment: ship_date, warehouse, on_time, days_to_ship, shipping_cost, carrier\n\n## When to Use\n- Questions about revenue, costs, quantities, counts\n- Comparing performance across regions, warehouses, carriers, channels\n- Analyzing trends over time\n- Getting order IDs for report generation\n- Aggregations, rankings, statistical summaries\n\n## When NOT to Use\n- Customer feedback or issue details (use search_order_notes)\n- Escalations or resolution narratives (use search_order_notes)"
      }
    },
    {
      "tool_spec": {
        "type": "cortex_search",
        "name": "search_order_notes",
        "description": "Search unstructured order notes including issues, resolutions, customer feedback, updates, and escalations.\n\n## Data Available\n- Issue reports: shipping delays, quality problems, inventory discrepancies\n- Resolution details: replacements, credits, RMA processing\n- Customer feedback: satisfaction scores, comments, improvement requests\n- Status updates: shipping confirmations, priority changes\n- Escalations: overdue orders, repeated problems, high-value customer complaints\n\n## When to Use\n- Finding reported issues and their resolutions\n- Customer feedback and satisfaction insights\n- Escalation details requiring attention\n- Qualitative context about specific orders or patterns\n\n## When NOT to Use\n- Numerical metrics, totals, or averages (use query_order_metrics)\n- Revenue, shipping cost, or fulfillment rate calculations (use query_order_metrics)"
      }
    },
    {
      "tool_spec": {
        "type": "generic",
        "name": "generate_order_report",
        "description": "Generate a comprehensive HTML report for a specific order including all details, line items, fulfillment info.\n\n## When to Use\n- User explicitly asks to generate or create a report\n- User wants a formatted document for a specific order\n\n## Required Input\n- order_id (integer): Get this by first querying with query_order_metrics if only customer name is provided\n\n## Error Handling\nIf this tool fails, fall back to assembling the report manually using query_order_metrics and search_order_notes.",
        "input_schema": {
          "type": "object",
          "properties": {
            "order_id": {
              "type": "integer",
              "description": "The unique order identifier. Look up via query_order_metrics if only customer name is given."
            }
          },
          "required": ["order_id"]
        }
      }
    }
  ],
  "tool_resources": {
    "query_order_metrics": {
      "execution_environment": {
        "query_timeout": 299,
        "type": "warehouse",
        "warehouse": "COMPUTE_WH"
      },
      "semantic_view": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.SUPPLY_CHAIN_ANALYST"
    },
    "search_order_notes": {
      "execution_environment": {
        "query_timeout": 299,
        "type": "warehouse",
        "warehouse": "COMPUTE_WH"
      },
      "search_service": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.ORDER_NOTES_SEARCH"
    },
    "generate_order_report": {
      "type": "procedure",
      "identifier": "AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.GENERATE_ORDER_SUMMARY_REPORT",
      "execution_environment": {
        "type": "warehouse",
        "warehouse": "COMPUTE_WH",
        "query_timeout": 300
      }
    }
  }
}
$$;

DESCRIBE AGENT SUPPLY_CHAIN_AGENT;

-- ====================================================================
-- SECTION 15: RUN OPTIMIZED EVALUATION
-- ====================================================================

CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'OPTIMIZED_SUPPLY_CHAIN_EVAL'),
  '@AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVAL_CONFIG_STAGE/supply_chain_eval_config.yaml'
);

CALL EXECUTE_AI_EVALUATION(
  'STATUS',
  OBJECT_CONSTRUCT('run_name', 'OPTIMIZED_SUPPLY_CHAIN_EVAL'),
  '@AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVAL_CONFIG_STAGE/supply_chain_eval_config.yaml'
);

-- ====================================================================
-- SECTION 16: REVIEW RESULTS
-- ====================================================================

-- Get baseline evaluation data
SELECT * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
  'AGENT_EVALUATION_DEMO',
  'SUPPLY_CHAIN',
  'SUPPLY_CHAIN_AGENT',
  'cortex agent',
  'BASELINE_SUPPLY_CHAIN_EVAL'
));

-- Get optimized evaluation data
SELECT * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
  'AGENT_EVALUATION_DEMO',
  'SUPPLY_CHAIN',
  'SUPPLY_CHAIN_AGENT',
  'cortex agent',
  'OPTIMIZED_SUPPLY_CHAIN_EVAL'
));

-- ====================================================================
-- SECTION 17: SETUP COMPLETE
-- ====================================================================

SELECT
$$
=====================================================
SUPPLY CHAIN ORDER ANALYTICS - SETUP COMPLETE
=====================================================
Database: AGENT_EVALUATION_DEMO
Schema: SUPPLY_CHAIN

Tables:
  - SALES_ORDERS (50 records)
  - ORDER_LINE_ITEMS (~205 records)
  - ORDER_FULFILLMENT (~48 records)
  - ORDER_NOTES (75 records)

Services:
  - Semantic View: SUPPLY_CHAIN_ANALYST
  - Cortex Search: ORDER_NOTES_SEARCH
  - Stored Procedure: GENERATE_ORDER_SUMMARY_REPORT
  - Agent: SUPPLY_CHAIN_AGENT

Evaluations:
  - Baseline: BASELINE_SUPPLY_CHAIN_EVAL
  - Optimized: OPTIMIZED_SUPPLY_CHAIN_EVAL

Navigate to AI & ML > Agents > SUPPLY_CHAIN_AGENT > Evaluations
to compare baseline vs optimized results.
=====================================================
$$ AS setup_status;
