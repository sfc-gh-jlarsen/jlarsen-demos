---
name: revenue-reconciliation
description: "Compare SAP order revenue against Salesforce closed-won amounts for matched accounts. Identify discrepancies. Use when: monthly close, revenue reconciliation, account review, variance analysis, SAP vs Salesforce comparison. Triggers: reconcile revenue, revenue variance, SAP vs SFDC, mismatch, unreconciled."
---

# Revenue Reconciliation: SAP vs Salesforce

Compare SAP ERP order revenue with Salesforce CRM closed-won deals to find discrepancies at the customer and month level.

## Domain Knowledge

- SAP amounts are in **document currency** (USD, EUR, JPY, BRL) per order. SFDC amounts are typically in the account's currency.
- Currency differences between systems are **not necessarily real discrepancies** -- flag them separately.
- The `revenue_summary` gold view already joins both systems by customer and month.
- A customer is matched across systems via `SAP_ACCOUNT_ID__C` on the Salesforce Account matching `KUNNR` on the SAP Customer Master.
- Variance = SAP order revenue - SFDC closed revenue. Positive means SAP has more; negative means SFDC has more.

## Data Sources

| View | Database.Schema | Purpose |
|------|-----------------|---------|
| `REVENUE_SUMMARY` | `POWER_USER_SKILL_DEMO.DBT_PROJECT_GOLD` | Monthly revenue by customer from both systems with variance |
| `ORDER_LINES_ENRICHED` | `POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER` | SAP order line detail for drill-down |
| `OPPORTUNITY_ENRICHED` | `POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER` | SFDC opportunity detail for drill-down |

## Workflow

### Step 1: Determine Scope

Ask the user for:
- **Time period**: Specific month (e.g., "March 2026"), quarter, or date range
- **Variance threshold**: Default 10% -- what percentage difference is worth investigating?
- **Customer filter** (optional): Specific customer or all customers

### Step 2: Run Summary Query

```sql
SELECT
    customer_number,
    customer_name,
    country_name,
    industry,
    revenue_month,
    sap_currency,
    sap_order_count,
    sap_order_revenue,
    sfdc_deal_count,
    sfdc_closed_revenue,
    revenue_variance,
    data_source,
    CASE
        WHEN sap_order_revenue = 0 AND sfdc_closed_revenue = 0 THEN 0
        WHEN sap_order_revenue = 0 THEN 100
        ELSE ROUND(ABS(revenue_variance) / sap_order_revenue * 100, 1)
    END AS variance_pct
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_GOLD.REVENUE_SUMMARY
WHERE revenue_month >= :start_date
  AND revenue_month <= :end_date
ORDER BY ABS(revenue_variance) DESC;
```

Replace `:start_date` and `:end_date` with the user's requested period.

### Step 3: Identify Mismatches

Filter to rows where `variance_pct > :threshold` (user's threshold, default 10).

Present a summary:
- Total customers analyzed
- Customers with matching revenue (within threshold)
- Customers with variance exceeding threshold
- Total unreconciled amount (sum of absolute variances for flagged customers)
- Customers appearing in only one system (`data_source = 'SAP Only'` or `'SFDC Only'`)

### Step 4: Drill Into Flagged Customers

For each flagged customer, run two queries side by side:

**SAP side:**
```sql
SELECT order_number, order_date, material_description,
       order_quantity, unit_price, line_total, currency
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.ORDER_LINES_ENRICHED
WHERE customer_number = :customer_number
  AND order_date BETWEEN :start_date AND :end_date
ORDER BY order_date, order_number;
```

**SFDC side:**
```sql
SELECT opportunity_name, close_date, opportunity_amount,
       stage, opportunity_type, lead_source
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.OPPORTUNITY_ENRICHED
WHERE sap_customer_number = :customer_number
  AND stage_category = 'WON'
  AND close_date BETWEEN :start_date AND :end_date
ORDER BY close_date;
```

### Step 5: Generate Narrative Summary

Produce a concise report:
1. Period analyzed and threshold used
2. High-level match rate
3. For each flagged customer: what the variance is, likely cause (currency mismatch, timing difference, missing data), and recommended action
4. List of single-system-only entries that may need investigation

## Stopping Points

- After Step 3: Present summary and ask if user wants drill-down on specific customers
- After Step 5: Ask if user wants to adjust threshold or expand the time range

## Output

A narrative reconciliation report with supporting data tables showing matched/mismatched revenue between SAP and Salesforce.
