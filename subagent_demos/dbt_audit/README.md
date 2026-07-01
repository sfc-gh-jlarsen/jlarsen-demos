# dbt Model Audit Subagent

Validates dbt models against best practices — catching issues with testing, documentation, materialization choices, and join logic.

## What It Finds

- `SELECT *` in staging models (breaks downstream if source schema changes)
- Missing `not_null` and `unique` tests on primary keys
- Undocumented models and columns
- Wrong materialization (view for expensive aggregations that should be table/incremental)
- Join fanout risks (missing join conditions causing row duplication)
- Missing `accepted_values` tests on categorical columns
- No grain definition on fact tables

## Running the Demo

Copy the prompt from `PROMPT.md` and paste it into CoCo, or adapt it to point at your own dbt project.
