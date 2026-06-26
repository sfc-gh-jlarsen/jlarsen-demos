# Slide Content — PowerBI Migration Workshop

Six slides for the 60-minute workshop. Use these descriptions to build your deck.

---

## Slide 1: "The PowerBI Problem"

**Layout:** Left = diagram, Right = bullet list

**Left side — PowerBI sprawl diagram:**
- Central PowerBI Service cloud connected to 12+ .pbix icons labeled "Ad-hoc Report 1", "Ad-hoc Report 2", ..., "Finance v3 FINAL", "OEE Dashboard (old)"
- Fragmented semantic models icon (3 separate DAX cubes with different formulas)
- RLS padlock icons scattered on individual reports
- Red X on "IT Governance" trying to connect

**Right side — Three anti-patterns:**
1. One-time reports that never die (data hoarding)
2. Slow iteration cycles (Desktop -> Service -> wait -> republish)
3. Fragmented semantic layer (DAX logic scattered across reports)

**Bottom callout:**
> "What if the data, logic, governance, AND app all lived in one place?"

---

## Slide 2: "The Snowflake Answer" (Architecture)

**Full-slide architecture diagram:**

```
            SNOWFLAKE PLATFORM
 ┌──────────────────────────────────────────────────┐
 │                                                  │
 │  [Raw Tables]  ──────►  [Semantic Views]         │
 │   ERP / MES /             (optional but          │
 │   IoT data                 recommended)          │
 │                                │                 │
 │         ┌────────────────────┬─┴──────────┐      │
 │         ▼                    ▼            ▼      │
 │  [Workspace App]    [Deployed App]   [Cortex]    │
 │   (ad-hoc,           (governed,       Agent]     │
 │    private)           + agent         (NL Q&A)   │
 │         │             sidebar)                   │
 │         └── Caller's Rights ──┘                  │
 │              (each user sees only their data)    │
 └──────────────────────────────────────────────────┘
```

**Callout box:**
> "Semantic View = PowerBI Semantic Model equivalent — but governed centrally and consumed by EVERY tool (apps, agents, SQL, notebooks)."

---

## Slide 3: "From Ad-Hoc to Governed"

**Visual progression (horizontal arrow with 3 stops):**

| Level | Deployment | Audience | Governance |
|-------|-----------|----------|------------|
| 1. Workspace App | Private, ephemeral | Just me | None needed |
| 2. Deployed App | Shared URL, role-gated | My team | Semantic View + caller's rights |
| 3. App Framework | Packaged, distributed | Enterprise | Full RBAC + Native App |

**Key insight (bottom):**
> "Same Python code. Same data. Different deployment posture."

---

## Slide 4: "Caller's Rights = Your New RLS"

**Side-by-side comparison table:**

| | PowerBI RLS | Snowflake Caller's Rights |
|---|---|---|
| Where defined | DAX per model | Once at the data layer |
| Scope | Only works in PowerBI | Works in ANY app/tool |
| Who manages | Report developers | Data platform admins |
| Bypassable? | Yes (Desktop mode) | No |
| Per-app config | Yes (each .pbix) | No (one policy, all apps) |
| Audit trail | Limited | Full ACCESS_HISTORY |

**Code snippet (centered):**
```python
# One line enables personalized access:
conn = st.connection("snowflake-callers-rights")
df = conn.query("SELECT * FROM production_data")
# -> User only sees THEIR plant's data automatically
```

**Badge:** "GA June 2026 — Streamlit Container Runtime v1.53.1+"

---

## Slide 5: "SPCS Under the Hood"

**Architecture diagram:**
```
Compute Pool ──► Nodes (VMs) ──► Service Instances ──► Your App ──► Users
```

**Key operational facts (icon + one-liner each):**
- Warm Pools (GA Feb 2025): Pre-provisioned nodes, instant cold start
- Auto-Scaling (GA May 2026): MIN/MAX nodes and instances
- Container Runtime (GA Mar 2026): Any Python package, full Docker freedom
- Monitoring: Event tables, SYSTEM$GET_SERVICE_LOGS, Snowsight UI
- Cost: Credit-per-node-hour, AUTO_SUSPEND for control

**Sizing quick-reference table:**

| App Type | Instance | Nodes | Est. Credits/hr |
|----------|----------|-------|-----------------|
| Simple dashboard | CPU_X64_XS | 1 | ~0.5 |
| Interactive app | CPU_X64_S | 1-2 | ~1.0 |
| Data-intensive | CPU_X64_M | 2-3 | ~2.0 |

---

## Slide 6: "Your Migration Path"

**5-step numbered progression (vertical timeline or staircase):**

1. Upload .pbit/.pbix to Semantic View Autopilot -> instant semantic model
2. Pilot 5 "throwaway report" users with Workspace apps
3. Convert top 3 certified reports to governed Streamlit apps
4. Add Cortex Agent for natural language access
5. Map PowerBI RLS to row access policies + caller's rights

**Bottom CTA (bold, large):**
> "Someone needs to own the semantic layer. Let it be Snowflake."
