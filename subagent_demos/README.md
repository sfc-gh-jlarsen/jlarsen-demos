# Subagent CI/CD Demos

Demos showing how to use Cortex Code (CoCo) agents as quality gates for your Snowflake projects.

## What Are Subagents?

Subagents are stateless task workers you can define and invoke from CoCo to perform focused, repeatable checks. You give them a system prompt describing what to look for, specify which tools they can use, and they report back findings — similar to a linter or CI check, but powered by an LLM that understands intent, not just syntax.

Key characteristics:
- **Stateless** — each invocation starts fresh with no memory of prior runs
- **Focused** — best results come from a single, well-scoped task per agent
- **Parallel** — you can spawn multiple agents simultaneously for independent checks
- **Context-isolated** — output stays in the agent; only the summary returns to your main session
- **Configurable** — choose the model, tools, and behavior via YAML frontmatter

## Agent Definition Format

Each `PROMPT.md` is a full agent definition using CoCo's frontmatter format:

```yaml
---
name: my-agent-name
description: What this agent does (shown in agent listings)
tools:
  - Read          # Read files
  - Grep          # Search file contents
  - Glob          # Find files by pattern
  - Bash          # Run shell commands
model: claude-haiku-4-5   # Fast + cheap for review tasks
---

# System prompt goes here
Your instructions for the agent...
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `name` | Identifier used to invoke the agent |
| `description` | One-line summary (shown in listings and help) |
| `tools` | Which CoCo tools the agent can access |
| `model` | LLM to use — `claude-haiku-4-5` is fast/cheap for review tasks |

## When to Use Subagents

| Use Case | Why Subagents Help |
|----------|-------------------|
| Code review gates | Consistent checks every time, no reviewer fatigue |
| Security scanning | Catches patterns a regex linter would miss (context-aware) |
| Pre-merge validation | Ensures standards are met before a PR is approved |
| dbt model auditing | Validates modeling patterns, test coverage, documentation |

## How These Demos Work

Each demo folder contains:

1. **Sample files** with intentional issues — realistic code you'd find in a real project
2. **`PROMPT.md`** — a complete agent definition you can install or invoke directly

### Running a Demo

**Option 1: Invoke directly** — Tell CoCo to run the agent against the sample files:

```
Run the sql-review agent defined in subagent_demos/sql_review/PROMPT.md
against subagent_demos/sql_review/sample_queries.sql
```

**Option 2: Ad-hoc** — Copy the system prompt section from `PROMPT.md` and paste it as instructions:

```
Review subagent_demos/sql_review/sample_queries.sql for correctness issues.
[paste the check criteria from PROMPT.md]
```

### Adapting for Your Own Projects

1. Copy a `PROMPT.md` to your project
2. Edit the system prompt to add your team's specific rules
3. Point it at your files when invoking

## Demos

| Demo | Agent Name | What It Catches |
|------|-----------|----------------|
| [`sql_review/`](sql_review/) | `sql-review` | NULL handling, join fanout, type precision, cartesian risk |
| [`security_scan/`](security_scan/) | `security-scan` | Hardcoded secrets, overly permissive grants, network exposure |
| [`pr_readiness/`](pr_readiness/) | `pr-readiness` | TODOs, credentials in config, unsafe DDL, injection vulnerabilities |
| [`dbt_audit/`](dbt_audit/) | `dbt-audit` | Missing tests/docs, wrong materialization, join correctness |

## Model Selection Guide

| Model | Best For | Tradeoff |
|-------|----------|----------|
| `claude-haiku-4-5` | Fast reviews, simple pattern matching | Cheapest, may miss subtle issues |
| `claude-sonnet-4-5` | Balanced depth and speed | Good default for most checks |
| `claude-opus-4` | Complex reasoning, architectural review | Slowest but most thorough |

For CI/CD gates where you want fast feedback, `claude-haiku-4-5` is the right choice. For deep security audits or architectural review, consider `claude-sonnet-4-5` or `claude-opus-4`.
