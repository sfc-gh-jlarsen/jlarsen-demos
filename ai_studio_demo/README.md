# AI Function Studio Demo: Enterprise Support Ticket Classification

## The Business Problem

An enterprise industrial manufacturer receives ~15,000 B2B support tickets per month across six divisions. Each ticket needs to be classified by division, issue type, priority, customer segment, and routed to the correct team queue — all within SLA. Today, 3 FTEs manually triage tickets with a 6-hour average time-to-route and an 18% misroute rate. Every misroute costs ~$400 in rework. Missed P1 escalations (production line down, safety incidents) cost orders of magnitude more.

The classification task is complex because a single ticket requires **10 interdependent output fields simultaneously**: the routing queue depends on both division and issue type, the response template depends on priority, and escalation indicators inform whether the SLA flag should fire. This isn't "which bucket does this go in" — it's structured multi-field extraction with business logic.

## Why Not Just Use...

### `AI_CLASSIFY`?

`AI_CLASSIFY` maps one input to one category from a flat list. It's built for single-taxonomy problems: "Is this spam or not-spam?" or "Which department: Sales, Support, Billing?"

This use case requires 10 structured outputs from one input — division, issue_type, priority, priority_reasoning, routing_queue, product_family, customer_segment, sla_flag, escalation_indicators (array), and suggested_response_template. These fields are interdependent. You'd need 4+ separate `AI_CLASSIFY` calls per ticket (one per taxonomy), with no way to produce reasoning, routing codes, or arrays, and no cross-field coherence. Wrong tool for the job.

### A raw `AI_COMPLETE` UDF?

Writing `CREATE FUNCTION ... AS $$ SELECT AI_COMPLETE(...) $$` works. You get structured output via `response_format` and batch execution. It's a valid approach for teams that want full control.

What you don't get: any tooling for measuring whether the function is accurate, systematically comparing models, optimizing prompts, or tracking experiments over time. You build all of that from scratch — evaluation framework, metric UDFs, model comparison harness, experiment tracking. AI Function Studio gives you that tooling out of the box. The function it produces IS a SQL UDF calling AI_COMPLETE under the hood — it just comes with the managed evaluate/optimize loop.

### CoCo / conversational AI?

CoCo is for humans asking questions. It's exploratory, ad-hoc, one-at-a-time. You can't call it from a scheduled task, grant RBAC on it, batch-process 15K tickets nightly, or version-control its prompt. It has no evaluation framework, no experiment tracking, no model comparison workflow. It's the right tool for prototyping the prompt and understanding the data — then you graduate to a governed function for production.

### The Cortex REST API?

Same story as the raw UDF — it works, but you're building the production scaffolding yourself. The REST API is the right choice for application-layer integration (calling from a microservice, a Next.js app, etc.) where you need HTTP semantics. For in-warehouse batch processing against Snowflake tables, a SQL function is more natural and the Studio tooling makes it faster to iterate.

## Why AI Function Studio

AI Function Studio fills the gap between "I wrote a prompt that works in chat" and "I have a governed, evaluated, cost-controlled AI pipeline in production."

| Capability | Conversational AI (CoCo, chat) | DIY UDF + Cortex REST API | AI Function Studio |
|------------|-------------------------------|--------------------------|-------------------|
| **Governance** | Freeform — no schema enforcement | You build it yourself | Strict output schema, enum constraints, versioned functions |
| **Evaluation** | Manual spot-checking | You build it yourself | Formal metrics (exact_match, llm_judge, custom UDFs), tracked experiments |
| **Optimization** | N/A | Manual prompt iteration | Automated prompt + model optimization (OPTIMIZE stored procedure) |
| **Reproducibility** | Same question can yield different formats | Depends on your implementation | Deterministic function signature, materialized results |
| **RBAC** | User-level access | Function-level (you manage it) | Function-level grants, database roles, least-privilege |
| **Cost control** | Pay per conversation | You track it yourself | Per-function model selection, budget guardrails, materialized results |

| **Auditability** | Chat logs | Query history only | Query history + Snowflake Experiments + run tracking |
| **Scale** | One-at-a-time | Batch via UDF (you build it) | Batch classification (15K tickets/night via INSERT...SELECT) |
| **Time to production** | N/A | Days-weeks (build eval, optimize, RBAC yourself) | Hours (integrated create → evaluate → optimize workflow) |

The DIY approach (write a Python/SQL UDF wrapping the Cortex REST API or `AI_COMPLETE` directly) absolutely works. But you're building the evaluation framework, optimization loop, experiment tracking, and metric comparison from scratch. AI Function Studio packages all of that into a managed workflow. The function it produces *is* a SQL UDF calling `AI_COMPLETE` — it just also gives you the tooling to iterate on it systematically.

**When to use AI Function Studio vs. conversational AI:**
- **Ad-hoc exploration, one-off questions, prototyping** → CoCo / chat
- **Repeated classification at scale, governed pipelines, SLA-bound routing** → AI Function Studio

## Cost Controls & Token Economics

### Monitoring & Budgets

AI functions consume Cortex AI credits based on token usage. Snowflake provides built-in controls:

- **Cortex AI credit monitoring** — Track usage via `SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY` (service type `AI_SERVICES`)
- **Budgets** — Set spending limits at the account or object level; functions stop executing when the budget is exhausted
- **Resource monitors** — Alert or suspend when credit consumption crosses thresholds

### Thinking About Token Cost

Every AI function call has a cost proportional to **input tokens + output tokens**:

```
Cost per call = (input_tokens + output_tokens) x model_rate_per_token
```

For this ticket classification use case:
- **Input:** ~1,200-1,800 tokens (prompt template + ticket text)
- **Output:** ~150-250 tokens (structured JSON response)
- **Total per call:** ~1,500-2,000 tokens

At 15,000 tickets/month:
- Budget model (gpt-5-mini): ~30M tokens/month
- Premium model (claude-sonnet): ~30M tokens/month at higher per-token rate

### Design Pattern: Materialize Results

**Call the AI function once, query the result many times.** This is the most important cost optimization:

```sql
-- BAD: Calling AI function on every SELECT (pays per query)
SELECT CLASSIFY_SUPPORT_TICKET(TICKET_TEXT):priority::VARCHAR
FROM SUPPORT_TICKETS
WHERE ...;

-- GOOD: Materialize once, query the result for free
INSERT INTO ROUTED_TICKETS (TICKET_ID, TICKET_TEXT, CLASSIFICATION)
SELECT TICKET_ID, TICKET_TEXT, CLASSIFY_SUPPORT_TICKET(TICKET_TEXT)
FROM SUPPORT_TICKETS
WHERE RECEIVED_AT >= DATEADD('hour', -24, CURRENT_TIMESTAMP());

-- Then query the materialized results (no AI cost)
SELECT CLASSIFICATION:priority::VARCHAR FROM ROUTED_TICKETS WHERE ...;
```

This pattern means:
- **Batch processing** (nightly, hourly) is far cheaper than real-time per-query classification
- Downstream dashboards, alerts, and reports read from the materialized table at zero AI cost
- You can re-classify only new/changed tickets instead of the full table

### Sizing Guidelines

| Volume | Recommended Approach | Model Tier |
|--------|---------------------|------------|
| <100 tickets/day | Real-time (on SELECT) | Any — cost is negligible |
| 100-1,000/day | Hourly batch INSERT | Budget or mid-range |
| 1,000-10,000/day | Nightly batch INSERT | Budget with premium re-classify on P1/P2 |
| 10,000+/day | Streaming via Snowpipe + task | Budget for triage, premium for escalations |

## What This Demo Builds

The AI function takes raw ticket text and returns structured JSON with:
- **Division** routing (Industrial Adhesives, Safety, Electronics, Healthcare, etc.)
- **Issue type** classification (Product Defect, RMA, Regulatory, etc.)
- **Priority** assignment (P1-Critical through P4-Low)
- **Routing queue** (e.g., `IAT-AppEng-Automotive`, `SI-QA-Americas`)
- **Escalation indicators** (production_line_down, safety_incident, etc.)
- **Customer segment** and **SLA flag**
- **Suggested response template**

## Notebooks (Primary Demo Path)

Run these in order in Snowsight (Projects > Notebooks > Import .ipynb):

| # | Notebook | What It Does |
|---|----------|--------------|
| 1 | `notebooks/1_setup.ipynb` | Creates database, tables, 15 sample tickets |
| 2 | `notebooks/2_function_creation.ipynb` | Builds V1 and V2 of the classifier |
| 3 | `notebooks/3_evaluation_iteration.ipynb` | Evaluation framework, V1 vs V2 comparison |
| 4 | `notebooks/4_model_comparison_rbac.ipynb` | 6-model scorecard + RBAC patterns |

Each notebook checks whether prior notebooks have been run and warns you if prerequisites are missing. All notebooks are idempotent (safe to re-run).

## Streamlit App (Interactive Dashboard)

A Streamlit-in-Snowflake app provides a visual walkthrough of the demo results:

```bash
cd streamlit_app
snow streamlit deploy --open
```

| Page | What It Shows |
|------|--------------|
| Overview | Business context, demo progress tracker (which notebooks have been run) |
| Live Classification | Paste any ticket text, classify in real-time, see structured results |
| Evaluation | V1 vs V2 accuracy bar charts, custom metric demo |
| Model Comparison | 6-model scorecard, P1 safety deep-dive, cost/quality scatter, RBAC summary |

The app reads materialized results from the database — pages gracefully warn you if prerequisite notebooks haven't been run yet.

## Sample Output

```json
{
  "division": "Industrial Adhesives & Tapes",
  "issue_type": "Product Defect / Failure",
  "priority": "P1-Critical",
  "priority_reasoning": "Production line down blocking 2,200 units/day...",
  "routing_queue": "IAT-AppEng-Automotive",
  "product_family": "Structural Bonding Tapes",
  "customer_segment": "OEM",
  "sla_flag": true,
  "escalation_indicators": ["production_line_down", "executive_involvement", "contractual_risk"],
  "suggested_response_template": "ACK-P1-DEFECT"
}
```

## Cleanup

```sql
DROP DATABASE IF EXISTS AI_STUDIO_DEMO;
```
