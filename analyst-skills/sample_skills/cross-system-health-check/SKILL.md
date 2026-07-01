---
name: cross-system-health-check
description: Monthly cross-system health check comparing Salesforce CRM and SAP ERP data. Run when user asks about CRM/ERP reconciliation, missing SAP links, revenue variance, data quality between Salesforce and SAP, or cross-system health check.
---

# Cross-System Health Check: Salesforce ↔ SAP

Run these checks in order against the `POWER_USER_SKILL_DEMO` database. Use warehouse `COMPUTE_WH`. Present results with clear tables and flag any issues found.

## Check 1: Accounts Missing SAP Customer Link

Find Salesforce accounts that have no SAP customer master record (KNA1). Include any associated pipeline or closed-won revenue as "revenue at risk."

```sql
SELECT
    a.ID                        AS SFDC_ACCOUNT_ID,
    a.NAME                      AS ACCOUNT_NAME,
    a.INDUSTRY,
    a.BILLINGCOUNTRY,
    a.OWNER_NAME,
    a.ANNUAL_REVENUE,
    COUNT(o.ID)                 AS TOTAL_OPPORTUNITIES,
    SUM(CASE WHEN o.STAGE_NAME = 'Closed Won' THEN 1 ELSE 0 END) AS CLOSED_WON_DEALS,
    COALESCE(SUM(CASE WHEN o.STAGE_NAME = 'Closed Won' THEN o.AMOUNT END), 0) AS CLOSED_WON_REVENUE,
    COALESCE(SUM(o.AMOUNT), 0)  AS TOTAL_PIPELINE_AT_RISK
FROM POWER_USER_SKILL_DEMO.BRONZE.SFDC_ACCOUNT a
LEFT JOIN POWER_USER_SKILL_DEMO.BRONZE.SFDC_OPPORTUNITY o
    ON o.ACCOUNT_ID = a.ID
WHERE a.SAP_ACCOUNT_ID__C IS NULL
   OR a.SAP_ACCOUNT_ID__C = ''
GROUP BY a.ID, a.NAME, a.INDUSTRY, a.BILLINGCOUNTRY, a.OWNER_NAME, a.ANNUAL_REVENUE
ORDER BY TOTAL_PIPELINE_AT_RISK DESC;
```

**What to report:**
- Number of accounts missing SAP links
- Total pipeline at risk (sum of all opportunity amounts)
- Total closed-won revenue at risk (deals won but can't flow to SAP for fulfillment)
- Call out any accounts with Closed Won deals — these are urgent

## Check 2: Revenue Variance — SFDC Closed Won vs SAP Orders

For accounts that DO have SAP links, compare total Closed Won revenue in Salesforce against total sales order value in SAP (VBAK). Flag anything over 10% variance.

```sql
WITH sfdc AS (
    SELECT
        a.SAP_ACCOUNT_ID__C                      AS SAP_CUSTOMER_ID,
        a.NAME                                    AS ACCOUNT_NAME,
        a.INDUSTRY,
        a.OWNER_NAME,
        COUNT(o.ID)                               AS SFDC_CLOSED_WON_DEALS,
        SUM(o.AMOUNT)                             AS SFDC_CLOSED_WON_TOTAL
    FROM POWER_USER_SKILL_DEMO.BRONZE.SFDC_ACCOUNT a
    JOIN POWER_USER_SKILL_DEMO.BRONZE.SFDC_OPPORTUNITY o
        ON o.ACCOUNT_ID = a.ID
        AND o.STAGE_NAME = 'Closed Won'
    WHERE a.SAP_ACCOUNT_ID__C IS NOT NULL
      AND a.SAP_ACCOUNT_ID__C <> ''
    GROUP BY a.SAP_ACCOUNT_ID__C, a.NAME, a.INDUSTRY, a.OWNER_NAME
),
sap AS (
    SELECT
        h.KUNNR                                   AS SAP_CUSTOMER_ID,
        COUNT(DISTINCT h.VBELN)                   AS SAP_ORDER_COUNT,
        SUM(h.NETWR)                              AS SAP_ORDER_TOTAL
    FROM POWER_USER_SKILL_DEMO.BRONZE.SAP_VBAK h
    GROUP BY h.KUNNR
)
SELECT
    s.SAP_CUSTOMER_ID,
    s.ACCOUNT_NAME,
    s.INDUSTRY,
    s.OWNER_NAME,
    s.SFDC_CLOSED_WON_DEALS,
    s.SFDC_CLOSED_WON_TOTAL,
    COALESCE(p.SAP_ORDER_COUNT, 0)                AS SAP_ORDER_COUNT,
    COALESCE(p.SAP_ORDER_TOTAL, 0)                AS SAP_ORDER_TOTAL,
    s.SFDC_CLOSED_WON_TOTAL - COALESCE(p.SAP_ORDER_TOTAL, 0) AS REVENUE_DELTA,
    CASE
        WHEN COALESCE(p.SAP_ORDER_TOTAL, 0) = 0 AND s.SFDC_CLOSED_WON_TOTAL > 0 THEN 100.0
        WHEN s.SFDC_CLOSED_WON_TOTAL = 0 THEN 0.0
        ELSE ROUND(ABS(s.SFDC_CLOSED_WON_TOTAL - p.SAP_ORDER_TOTAL)
              / GREATEST(s.SFDC_CLOSED_WON_TOTAL, p.SAP_ORDER_TOTAL) * 100, 1)
    END                                           AS VARIANCE_PCT,
    CASE
        WHEN COALESCE(p.SAP_ORDER_TOTAL, 0) = 0 AND s.SFDC_CLOSED_WON_TOTAL > 0
            THEN 'NO SAP ORDERS'
        WHEN ABS(s.SFDC_CLOSED_WON_TOTAL - COALESCE(p.SAP_ORDER_TOTAL, 0))
              / GREATEST(s.SFDC_CLOSED_WON_TOTAL, COALESCE(p.SAP_ORDER_TOTAL, 0)) > 0.10
            THEN 'VARIANCE > 10%'
        ELSE 'OK'
    END                                           AS FLAG
FROM sfdc s
LEFT JOIN sap p ON s.SAP_CUSTOMER_ID = p.SAP_CUSTOMER_ID
ORDER BY VARIANCE_PCT DESC;
```

**What to report:**
- Table of all accounts with SFDC vs SAP amounts, delta, variance %, and flag
- Call out any accounts flagged `VARIANCE > 10%` or `NO SAP ORDERS`
- For flagged accounts, suggest likely root causes:
  - SAP > SFDC: orders may exist in SAP without corresponding Salesforce opportunities
  - SFDC > SAP: closed-won deals not yet converted to SAP sales orders (fulfillment risk)

## Check 3: Summary Scorecard

After running both checks, present a summary scorecard:

- **Accounts missing SAP link:** count and total pipeline at risk
- **Revenue variance flags:** count of accounts over 10% and total delta dollars
- **Overall health:** PASS if no issues, WARN if minor issues, FAIL if closed-won revenue can't reconcile

## Tables Used

- `POWER_USER_SKILL_DEMO.BRONZE.SFDC_ACCOUNT` — Salesforce accounts with SAP_ACCOUNT_ID__C link field
- `POWER_USER_SKILL_DEMO.BRONZE.SFDC_OPPORTUNITY` — Salesforce opportunities (STAGE_NAME = 'Closed Won' for closed deals)
- `POWER_USER_SKILL_DEMO.BRONZE.SAP_KNA1` — SAP customer master (KUNNR = customer ID)
- `POWER_USER_SKILL_DEMO.BRONZE.SAP_VBAK` — SAP sales order headers (KUNNR = customer, NETWR = order value)
