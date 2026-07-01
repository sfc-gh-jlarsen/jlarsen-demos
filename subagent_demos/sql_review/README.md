# SQL Review Subagent

Catches silent correctness bugs in Snowflake SQL — the kind that don't throw errors but produce wrong results.

## What It Finds

- `WHERE col = NULL` (always false)
- Integer division precision loss
- LEFT JOIN converted to INNER by WHERE filter
- UNION deduplication when UNION ALL is intended
- Missing join conditions causing cartesian products
- GROUP BY granularity mismatches
- FLATTEN silently dropping rows with NULL/empty arrays

## Running the Demo

Copy the prompt from `PROMPT.md` and paste it into CoCo, or adapt it to point at your own SQL files.
