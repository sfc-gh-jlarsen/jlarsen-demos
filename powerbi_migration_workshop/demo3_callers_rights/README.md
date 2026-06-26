# Demo 3: Caller's Rights in Action

This is **not a separate app** — it's a modification to Demo 2b showing how one connection change enables personalized data access per user.

## The One-Line Change

```python
# BEFORE (owner's rights — all users see all data):
conn = st.connection("snowflake")

# AFTER (caller's rights — each user sees only their authorized data):
conn = st.connection("snowflake-callers-rights")
```

That's it. The app code stays identical. The data layer does the filtering.

## Show Current User Context

```python
import streamlit as st

conn = st.connection("snowflake-callers-rights")

# Show who is viewing
current_user = conn.query("SELECT CURRENT_USER() as user, CURRENT_ROLE() as role")
st.caption(f"Viewing as: {current_user['USER'][0]} | Role: {current_user['ROLE'][0]}")

# Same query, different results depending on viewer's role:
df = conn.query("""
    SELECT * FROM MFG_SCHEDULING_REPORTING.ANALYTICS.DAILY_PRODUCTION_METRICS
""")
# Detroit Plant Manager → sees only Detroit data
# Austin Plant Manager  → sees only Austin data
# Regional VP          → sees all plants
```

## Row Access Policy

```sql
-- Mapping table: which user can see which plant
CREATE OR REPLACE TABLE MFG_SCHEDULING_REPORTING.ADMIN.USER_PLANT_ASSIGNMENTS (
    user_email VARCHAR,
    plant_id   VARCHAR
);

INSERT INTO MFG_SCHEDULING_REPORTING.ADMIN.USER_PLANT_ASSIGNMENTS VALUES
    ('detroit_pm@company.com', 'DET01'),
    ('austin_pm@company.com', 'AUS02'),
    ('regional_vp@company.com', 'DET01'),
    ('regional_vp@company.com', 'AUS02'),
    ('regional_vp@company.com', 'MTY03');

-- Row access policy: enforce at the data layer
CREATE OR REPLACE ROW ACCESS POLICY MFG_SCHEDULING_REPORTING.ADMIN.PLANT_ACCESS
AS (plant_id VARCHAR) RETURNS BOOLEAN ->
    -- Admins bypass
    CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN')
    OR
    -- Users see only their assigned plants
    plant_id IN (
        SELECT plant_id
        FROM MFG_SCHEDULING_REPORTING.ADMIN.USER_PLANT_ASSIGNMENTS
        WHERE user_email = CURRENT_USER()
    );

-- Apply to the metrics table
ALTER TABLE MFG_SCHEDULING_REPORTING.ANALYTICS.DAILY_PRODUCTION_METRICS
    ADD ROW ACCESS POLICY MFG_SCHEDULING_REPORTING.ADMIN.PLANT_ACCESS
    ON (PLANT_ID);
```

## Caller Grants (Admin Setup)

```sql
-- One-time setup by a platform admin:

-- 1. Allow the app-deployer role to use caller's rights
GRANT MANAGE CALLER GRANTS ON ACCOUNT TO ROLE data_platform_admin;

-- 2. Grant caller-scoped access for the app
GRANT CALLER USAGE ON DATABASE MFG_SCHEDULING_REPORTING
    TO ROLE streamlit_app_dev;
GRANT CALLER USAGE ON SCHEMA MFG_SCHEDULING_REPORTING.ANALYTICS
    TO ROLE streamlit_app_dev;
GRANT CALLER SELECT ON ALL TABLES IN SCHEMA MFG_SCHEDULING_REPORTING.ANALYTICS
    TO ROLE streamlit_app_dev;
```

## PowerBI RLS vs Snowflake Caller's Rights

| Aspect | PowerBI RLS | Snowflake Caller's Rights |
|--------|-------------|--------------------------|
| Where defined | DAX per model | Once at the data layer |
| Scope | Only works in PowerBI | Works in ANY app/tool |
| Who manages | Report developers | Data platform admins |
| Bypassable? | Yes (Desktop mode) | No — enforced by platform |
| Per-app config needed? | Yes (each .pbix) | No — one policy, all apps |
| Audit trail | Limited | Full ACCESS_HISTORY |

## Key Demo Talking Points

1. ONE line of code change enables personalized data access
2. No per-app RLS definition — it's at the DATA layer
3. Admins control what the app CAN access via caller grants
4. Users' existing role-based access controls apply automatically
5. Mix modes: owner's rights for reference data, caller's rights for sensitive data
