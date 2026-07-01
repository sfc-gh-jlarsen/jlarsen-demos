# CoCo Workflow Ideas for SAP + Salesforce Integration

These are two workflows that could be built as Cortex Code skill files to help analysts and business users work with this data pipeline. We're documenting the concepts here -- not building the skill files yet -- to show how CoCo skills can be designed around your data.

---

## Workflow 1: Revenue Reconciliation

### Purpose
Compare SAP order revenue against Salesforce closed-won amounts for matched accounts. Identify discrepancies that need investigation.

### When to Use
- Monthly close process
- Account review meetings
- Finance reconciliation

### How It Would Work

1. **Query the revenue_summary gold view** filtered to a specific month or customer
2. **Flag mismatches** where SAP order revenue differs from Salesforce closed-won revenue by more than a threshold (e.g., 10%)
3. **Drill into details**: For each mismatch, show the individual SAP orders (from order_lines_enriched) and SFDC opportunities (from opportunity_enriched) side by side
4. **Generate a summary** with:
   - Number of customers with matching revenue
   - Number with variance > threshold
   - Total unreconciled amount
   - Specific customers to investigate

### Example Prompts a User Might Ask
- "Show me revenue reconciliation for March 2026"
- "Which customers have more than 15% variance between SAP and Salesforce?"
- "What's the total unreconciled revenue for Q1?"

### Key SQL Patterns the Skill Would Use
```sql
-- Find mismatches
SELECT * FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_GOLD.REVENUE_SUMMARY
WHERE revenue_month = '2026-03-01'
  AND ABS(revenue_variance) > (sap_order_revenue * 0.10);

-- Drill into SAP side for a specific customer
SELECT order_number, order_date, material_description, line_total, currency
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.ORDER_LINES_ENRICHED
WHERE customer_number = '0000001000'
  AND order_date BETWEEN '2026-03-01' AND '2026-03-31';
```

### Why This is a Good CoCo Skill
- Combines multiple queries in a logical sequence
- Requires business context (what threshold matters, what's "normal" variance)
- Output should be narrative + data (not just a raw query result)
- The skill file can encode domain knowledge: "SAP amounts are in document currency, SFDC amounts are always USD -- currency differences are not real discrepancies"

---

## Workflow 2: Customer Onboarding Completeness Check

### Purpose
For each Salesforce account, verify whether the corresponding SAP customer master exists and is complete. Flag gaps in cross-system data linkage.

### When to Use
- New customer setup
- Quarterly data quality review
- Before major account reviews

### How It Would Work

1. **Start from Salesforce accounts** and check for SAP linkage via SAP_ACCOUNT_ID__C
2. **For linked accounts**, validate completeness:
   - Does the SAP customer have a valid country (T005T lookup resolves)?
   - Does the SAP customer have a company code assigned?
   - Are there any SAP orders for this customer?
3. **For unlinked accounts**, determine if they should be linked:
   - Has the account been in Salesforce for > 90 days?
   - Has a deal closed-won?
   - Is annual revenue above a threshold?
4. **Generate a report** with three categories:
   - Fully linked and complete
   - Linked but SAP data incomplete
   - Not linked -- should be investigated

### Example Prompts a User Might Ask
- "Which Salesforce accounts are missing SAP linkage?"
- "Run the onboarding completeness check for all accounts"
- "Show me accounts with closed-won deals but no SAP customer number"

### Key SQL Patterns the Skill Would Use
```sql
-- Find SFDC accounts with closed-won deals but no SAP link
SELECT
    a.NAME,
    a.INDUSTRY,
    a.ANNUAL_REVENUE,
    COUNT(o.ID) AS won_deals,
    SUM(o.AMOUNT) AS total_won
FROM POWER_USER_SKILL_DEMO.BRONZE.SFDC_ACCOUNT a
JOIN POWER_USER_SKILL_DEMO.BRONZE.SFDC_OPPORTUNITY o
    ON o.ACCOUNT_ID = a.ID AND o.STAGE_NAME = 'Closed Won'
WHERE a.SAP_ACCOUNT_ID__C IS NULL
GROUP BY ALL;

-- Check completeness of linked customers
SELECT
    customer_number,
    customer_name,
    country_name,
    company_name,
    is_linked_to_salesforce,
    CASE WHEN country_name IS NULL THEN 'Missing country lookup' ELSE 'OK' END AS country_check,
    CASE WHEN company_name IS NULL THEN 'Missing company code' ELSE 'OK' END AS company_check
FROM POWER_USER_SKILL_DEMO.DBT_PROJECT_SILVER.CUSTOMER_MASTER;
```

### Why This is a Good CoCo Skill
- Encodes business rules (what "complete" means for a customer record)
- Handles the nuance of cross-system data quality
- Produces actionable output (which accounts need attention, what's missing)
- The skill can track completeness over time if run periodically
