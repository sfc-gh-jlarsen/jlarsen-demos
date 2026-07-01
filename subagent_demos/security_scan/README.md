# Security Scan Subagent

Catches security anti-patterns in Snowflake deployment scripts — hardcoded secrets, overly permissive access, and dangerous account-level changes.

## What It Finds

- Hardcoded passwords and AWS keys
- Grants to PUBLIC or ACCOUNTADMIN on service accounts
- Network policies open to 0.0.0.0/0
- Data retention set to 0 (disabling Time Travel)
- Unrestricted shares exposing all tables
- Caller's rights procedures without input validation

## Running the Demo

Copy the prompt from `PROMPT.md` and paste it into CoCo, or adapt it to point at your own deployment scripts.
