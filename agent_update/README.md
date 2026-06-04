# Cortex Agent - Updating Orchestration Instructions

Interactive walkthrough demonstrating how to safely update a Cortex Agent's orchestration instructions **without overwriting** other fields in the specification.

## The Problem

`ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION` **completely replaces** the existing spec. If you only include the field you want to change, all other fields (tools, models, tool_resources) are removed.

## The Solution

Use the **read-modify-write** pattern:

1. **Read** the current spec via `DESCRIBE AGENT` (SQL) or `GET /api/v2/.../agents/{name}` (REST)
2. **Modify** only the field(s) you need in memory
3. **Write** the full spec back via `ALTER AGENT` (SQL) or `PUT /api/v2/.../agents/{name}` (REST)

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your connection name and agent coordinates

# 2. Install dependencies and run (uv handles the venv automatically)
uv run streamlit run app.py
```

If you don't have `uv`, install it first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Alternatively, with pip:

```bash
pip install streamlit snowflake-connector-python python-dotenv requests
streamlit run app.py
```

## Configuration

All configuration is in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SNOWFLAKE_CONNECTION_NAME` | Connection name from `~/.snowflake/connections.toml` | `default` |
| `SNOWFLAKE_DATABASE` | Database containing the agent | `USER_LOOKUP_DEMO` |
| `SNOWFLAKE_SCHEMA` | Schema containing the agent | `AGENT_UPDATE_DEMO` |
| `SNOWFLAKE_AGENT_NAME` | Name of the Cortex Agent | `USER_LOOKUP_AGENT` |

## What's in the App

The Streamlit app has 4 tabs:

| Tab | Description |
|-----|-------------|
| **SQL Approach** | Step-by-step SQL with executable buttons (`CREATE AGENT`, `ALTER AGENT`) |
| **Python Connector** | Interactive step-through with a variable explorer showing state changes |
| **REST API** | `GET`/`PUT` workflow with curl equivalents and live execution |
| **Test Agent** | Send questions to verify PIN-gating behavior |

The sidebar shows a live **Agent Config Monitor** with current model, tools count, and PIN status.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit walkthrough app |
| `.env` | Environment config (connection, database, schema, agent name) |
| `.env.example` | Template for environment config |
| `01_agent_update_walkthrough.sql` | Standalone SQL walkthrough |
| `02_update_agent_python.py` | Python connector example |
| `03_update_agent_rest_api.py` | REST API example |
| `test_all_approaches.py` | Automated test suite |

## Key Technical Notes

- **Spec format**: `ALTER AGENT` accepts both YAML and JSON. Python scripts use JSON with `$$` delimiters.
- **REST API URL**: Uses the account locator (e.g., `https://<locator>.snowflakecomputing.com`) not the org-account name (which contains underscores invalid for SSL hostnames).
- **`orchestration` appears in two places** in the spec:
  - `models.orchestration` = which LLM model to use
  - `instructions.orchestration` = the prompt given to the orchestrator
- **REST PUT returns empty body** on success (HTTP 200 with no JSON).

## Prerequisites

- A Snowflake account with `CREATE AGENT` privileges
- A connection configured in `~/.snowflake/connections.toml`
- The Cortex Search Service (`USER_SEARCH`) must exist (created by `01_agent_update_walkthrough.sql`)
