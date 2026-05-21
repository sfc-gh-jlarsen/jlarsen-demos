# Supply Chain Agent Evaluation Demo

End-to-end demonstration of [Cortex Agent Evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent/cortex-agent-evaluations) using a supply chain order analytics scenario. Build an agent, establish a baseline, optimize it, and compare evaluation results side-by-side.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Cortex Agent                              │
│              SUPPLY_CHAIN_AGENT                             │
│                                                             │
│   ┌──────────────────┐ ┌─────────────────┐ ┌────────────┐ │
│   │query_order_metrics│ │search_order_notes│ │gen_report  │ │
│   └────────┬─────────┘ └────────┬────────┘ └─────┬──────┘ │
└────────────┼────────────────────┼─────────────────┼────────┘
             │                    │                  │
             ▼                    ▼                  ▼
   ┌─────────────────┐  ┌────────────────┐  ┌─────────────────┐
   │  Semantic View   │  │ Cortex Search  │  │ Stored Procedure │
   │SUPPLY_CHAIN_     │  │ORDER_NOTES_    │  │GENERATE_ORDER_   │
   │  ANALYST         │  │  SEARCH        │  │ SUMMARY_REPORT   │
   └────────┬────────┘  └───────┬────────┘  └────────┬────────┘
            │                    │                     │
            ▼                    ▼                     ▼
   ┌─────────────────────────────────────────────────────────┐
   │          SALES_ORDERS  │  ORDER_LINE_ITEMS              │
   │          ORDER_FULFILLMENT  │  ORDER_NOTES              │
   └─────────────────────────────────────────────────────────┘
```

**Tools:**
| Tool | Type | Purpose |
|------|------|---------|
| `query_order_metrics` | Semantic View (Cortex Analyst) | Revenue, shipping costs, fulfillment KPIs |
| `search_order_notes` | Cortex Search | Issues, feedback, escalations, resolutions |
| `generate_order_report` | Stored Procedure | HTML order summary reports |

## Prerequisites

- Snowflake account with **ACCOUNTADMIN** access
- [Cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-functions#label-cortex-llm-availability) enabled (required for evaluation LLM judges)
- Python 3.8+ with `snowflake-connector-python` installed
- A [Snowflake connection](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/specify-connections) configured in `~/.snowflake/connections.toml`

## Setup

### 1. Clone and configure

```bash
git clone <this-repo>
cd supply-chain-agent-eval-demo
cp .env.example .env
```

Edit `.env` with your connection name and warehouse:
```
SNOWFLAKE_CONNECTION_NAME=my_connection
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

### 2. Generate synthetic data

```bash
python data_generator.py
```

This creates CSV files in `data/` with ~50 orders, ~200 line items, ~48 fulfillment records, 75 order notes, and 18 evaluation queries with ground truth.

### 3. Execute the setup SQL

Run `SETUP.sql` in Snowsight or SnowSQL. The script is divided into numbered sections:

| Section | Description |
|---------|-------------|
| 1-2 | Database, schema, role creation |
| 3 | File format and stage |
| 4 | Upload CSVs (see options below) |
| 5-6 | Create tables, load data, validate |
| 7 | Semantic View |
| 8 | Cortex Search Service |
| 9 | Report generation stored procedure |
| 10 | Cortex Agent (baseline) |
| 11 | Validate services |
| 12-13 | Evaluation dataset and baseline run |
| 14 | Optimized agent (ALTER AGENT) |
| 15 | Optimized evaluation run |
| 16 | Review results |

### 4. Upload data files

**Option A** (recommended): Use the upload script which handles both CSVs and the eval config YAML:

```bash
python upload_files.py
```

**Option B**: Use PUT commands in SnowSQL (update paths to your local clone):

```sql
PUT file://<path-to-repo>/data/SALES_ORDERS.csv @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- ... repeat for each CSV
```

### 5. Run evaluations

After executing through Section 13, the baseline evaluation starts. Wait for it to complete:

```sql
CALL EXECUTE_AI_EVALUATION(
  'STATUS',
  OBJECT_CONSTRUCT('run_name', 'BASELINE_SUPPLY_CHAIN_EVAL'),
  '@AGENT_EVALUATION_DEMO.SUPPLY_CHAIN.EVAL_CONFIG_STAGE/supply_chain_eval_config.yaml'
);
```

Then continue with Sections 14-15 to optimize the agent and run the second evaluation.

## Viewing Evaluation Results in the UI

Once both evaluations complete:

1. Navigate to **Snowsight** (https://app.snowflake.com)
2. Go to **AI & ML** > **Agents** in the left sidebar
3. Select **SUPPLY_CHAIN_AGENT**
4. Click the **Evaluations** tab
5. You will see both runs listed:
   - `BASELINE_SUPPLY_CHAIN_EVAL`
   - `OPTIMIZED_SUPPLY_CHAIN_EVAL`
6. Click into each run to see per-query scores across all 5 metrics
7. Use the **Compare** view to see side-by-side improvement between baseline and optimized

The evaluation metrics measured are:

| Metric | Type | What it measures |
|--------|------|-----------------|
| `answer_correctness` | Built-in | Factual accuracy of responses |
| `logical_consistency` | Built-in | Internal logical coherence |
| `groundedness` | Custom | Whether claims are supported by tool outputs |
| `execution_efficiency` | Custom | Optimal use of tools (minimal redundant calls) |
| `tool_selection` | Custom | Correct decomposition and routing to tools |

## File Structure

```
.
├── README.md
├── .env.example
├── .gitignore
├── SETUP.sql                        # Complete Snowflake setup (run in order)
├── supply_chain_eval_config.yaml    # Evaluation config with 5 metrics
├── data_generator.py                # Generates all synthetic CSVs
├── upload_files.py                  # Uploads CSVs + YAML to Snowflake stages
└── data/
    ├── SALES_ORDERS.csv
    ├── ORDER_LINE_ITEMS.csv
    ├── ORDER_FULFILLMENT.csv
    ├── ORDER_NOTES.csv
    └── EVALS_TABLE.csv
```

## Cleanup

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS AGENT_EVALUATION_DEMO;
DROP ROLE IF EXISTS SUPPLY_CHAIN_EVAL_ROLE;
```
