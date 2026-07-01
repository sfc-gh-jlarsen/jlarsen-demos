# PR Readiness Subagent

Validates a changeset is ready to merge — catching the kind of issues that slow down code review or cause incidents after deploy.

## What It Finds

- TODO/FIXME comments indicating unfinished work
- Hardcoded credentials in code or config files
- SQL injection vulnerabilities (string interpolation in queries)
- Unsafe DDL (DROP without migration safety)
- Missing error handling in critical paths
- Missing changelog or version bump

## Running the Demo

Copy the prompt from `PROMPT.md` and paste it into CoCo, or adapt it to point at your own PR files.
