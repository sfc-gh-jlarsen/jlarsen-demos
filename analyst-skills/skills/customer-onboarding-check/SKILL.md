---
name: customer-onboarding-check
description: "Validate cross-system customer data completeness between Salesforce and SAP. Flag missing linkages, incomplete SAP records, and unlinked accounts that should be investigated. Use when: onboarding check, data quality review, missing SAP linkage, customer completeness, cross-system validation. Triggers: onboarding check, missing SAP, unlinked accounts, customer completeness, data quality."
---

# Customer Onboarding Completeness Check

Verify that Salesforce accounts are properly linked to SAP customer master records and that linked records are complete.

## Domain Knowledge

- The link between systems is `SFDC_ACCOUNT.SAP_ACCOUNT_ID__C` = `SAP_KNA1.KUNNR`.
- Not every SFDC account should have an SAP link -- new prospects and pre-sales accounts may not be in SAP yet.
- An account **should** be investigated for SAP linkage if: it has closed-won deals, has been in SFDC > 90 days, or has annual revenue > $1M.
- A "complete" SAP customer record has: valid country (T005T resolves), company code assigned (T001 resolves), and at least one SAP order.

## Data Sources

| Table/View | Database.Schema | Purpose |
|------------|-----------------|---------|
| `CUSTOMER_MASTER` | `POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER` | Unified customer view with linkage flags |
| `SFDC_ACCOUNT` | `POWER_USER_SKILL_DEMO.BRONZE` | Raw Salesforce accounts |
| `SFDC_OPPORTUNITY` | `POWER_USER_SKILL_DEMO.BRONZE` | Opportunities for deal-based filtering |
| `ORDER_LINES_ENRICHED` | `POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER` | SAP orders to check activity |

## Workflow

### Step 1: Run Completeness Assessment

Execute a single query that categorizes every Salesforce account:

```sql
WITH account_deals AS (
    SELECT
        ACCOUNT_ID,
        COUNT(*) AS total_deals,
        SUM(CASE WHEN STAGE_NAME = 'Closed Won' THEN 1 ELSE 0 END) AS won_deals,
        SUM(CASE WHEN STAGE_NAME = 'Closed Won' THEN AMOUNT ELSE 0 END) AS won_amount
    FROM POWER_USER_SKILL_DEMO.BRONZE.SFDC_OPPORTUNITY
    GROUP BY ACCOUNT_ID
),
sap_orders AS (
    SELECT customer_number, COUNT(DISTINCT order_number) AS order_count
    FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.ORDER_LINES_ENRICHED
    GROUP BY customer_number
)
SELECT
    a.NAME AS account_name,
    a.INDUSTRY,
    a.ANNUAL_REVENUE,
    a.SAP_ACCOUNT_ID__C AS sap_link,
    a.CREATED_DATE AS sfdc_created,
    DATEDIFF('day', a.CREATED_DATE, CURRENT_DATE()) AS days_in_sfdc,
    COALESCE(d.won_deals, 0) AS won_deals,
    COALESCE(d.won_amount, 0) AS won_amount,
    cm.country_name,
    cm.company_name,
    COALESCE(so.order_count, 0) AS sap_order_count,
    CASE
        WHEN a.SAP_ACCOUNT_ID__C IS NOT NULL AND cm.country_name IS NOT NULL
             AND cm.company_name IS NOT NULL AND so.order_count > 0
            THEN 'COMPLETE'
        WHEN a.SAP_ACCOUNT_ID__C IS NOT NULL
            THEN 'LINKED_INCOMPLETE'
        WHEN d.won_deals > 0 OR a.ANNUAL_REVENUE > 1000000
             OR DATEDIFF('day', a.CREATED_DATE, CURRENT_DATE()) > 90
            THEN 'UNLINKED_INVESTIGATE'
        ELSE 'UNLINKED_OK'
    END AS status
FROM POWER_USER_SKILL_DEMO.BRONZE.SFDC_ACCOUNT a
LEFT JOIN account_deals d ON d.ACCOUNT_ID = a.ID
LEFT JOIN POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.CUSTOMER_MASTER cm
    ON cm.customer_number = a.SAP_ACCOUNT_ID__C
LEFT JOIN sap_orders so ON so.customer_number = a.SAP_ACCOUNT_ID__C
ORDER BY
    CASE status
        WHEN 'UNLINKED_INVESTIGATE' THEN 1
        WHEN 'LINKED_INCOMPLETE' THEN 2
        WHEN 'COMPLETE' THEN 3
        ELSE 4
    END,
    COALESCE(d.won_amount, 0) DESC;
```

### Step 2: Present Category Summary

Group results by status and present counts:

| Status | Meaning | Action |
|--------|---------|--------|
| `COMPLETE` | Linked to SAP, all fields populated, has orders | No action needed |
| `LINKED_INCOMPLETE` | SAP link exists but missing country, company code, or no orders | Review SAP master data |
| `UNLINKED_INVESTIGATE` | No SAP link but has won deals, high revenue, or > 90 days old | Create SAP customer record |
| `UNLINKED_OK` | No SAP link, but no strong reason to link yet | Monitor |

### Step 3: Detail Incomplete Records

For `LINKED_INCOMPLETE` accounts, show what's missing:

```sql
SELECT
    customer_number,
    customer_name,
    CASE WHEN country_name IS NULL THEN 'MISSING' ELSE 'OK' END AS country_lookup,
    CASE WHEN company_name IS NULL THEN 'MISSING' ELSE 'OK' END AS company_code,
    is_linked_to_salesforce,
    salesforce_account_name
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.CUSTOMER_MASTER
WHERE is_linked_to_salesforce = TRUE
  AND (country_name IS NULL OR company_name IS NULL);
```

### Step 4: Detail Unlinked Accounts Needing Investigation

For `UNLINKED_INVESTIGATE` accounts, show the business case for linking:

Present: account name, industry, annual revenue, won deals count, won amount, days in Salesforce.

### Step 5: Generate Summary

Produce a report with:
1. Total accounts assessed and breakdown by category
2. List of `LINKED_INCOMPLETE` accounts with specific gaps
3. List of `UNLINKED_INVESTIGATE` accounts ranked by priority (won amount descending)
4. Recommended next steps for each category

## Stopping Points

- After Step 2: Ask if user wants to drill into a specific category
- After Step 5: Ask if user wants to adjust thresholds (revenue cutoff, days threshold)

## Output

A completeness report categorizing all Salesforce accounts by their SAP linkage status with specific remediation actions for incomplete or unlinked records.
