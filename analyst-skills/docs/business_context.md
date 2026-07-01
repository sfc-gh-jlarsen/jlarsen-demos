# Business Context: SAP + Salesforce Manufacturing Integration

## The Scenario

A mid-size industrial manufacturer uses two core systems:

- **SAP ERP** handles order management, material planning, customer master data, and financials
- **Salesforce CRM** manages the sales pipeline, customer relationships, and opportunity tracking

The company needs a unified view of customer activity and revenue to answer questions like:
"How does our Salesforce pipeline compare to actual SAP order volume by customer?"

## The Data Challenge

### SAP Field Names are Cryptic
SAP uses short, coded field names that originated decades ago. Without tribal knowledge or documentation, they're opaque:

| SAP Field | Meaning | Table |
|-----------|---------|-------|
| VBELN | Sales Order Number | VBAK/VBAP |
| KUNNR | Customer Number | KNA1/VBAK |
| MATNR | Material Number | MARA/VBAP |
| POSNR | Item Number (line item position) | VBAP |
| NETWR | Net Value (order total) | VBAK |
| KWMENG | Order Quantity | VBAP |
| ERDAT | Created Date | VBAK |
| BUKRS | Company Code | T001/VBAK |
| LAND1 | Country Key (2-3 char code) | KNA1/T005T |
| BRSCH | Industry Sector Code | KNA1 |
| KTOKD | Account Group (customer classification) | KNA1 |

### Lookup Tables are Required
SAP stores codes, not readable values. You need lookup joins to make data usable:

- **T005T** (Country Text): Translates `LAND1 = 'DE'` into `'Germany'`
- **T001** (Company Code): Translates `BUKRS = '2000'` into `'European Operations'` and gives you the local currency
- **Industry codes**: `BRSCH = 'MACH'` means `'Machinery'` -- these are mapped via CASE expressions (no standard SAP table covers all)
- **Account groups**: `KTOKD = 'ZDOM'` means `'Domestic'` customer, `'ZINT'` means `'International'`

### Cross-System Customer Matching
The critical link between SAP and Salesforce is a **custom Salesforce field**: `SAP_ACCOUNT_ID__C`. This field stores the SAP customer number (KUNNR) and is manually maintained by the sales team. Not every Salesforce account has it (new prospects may not be in SAP yet), and not every SAP customer has a Salesforce account (legacy accounts).

## The Data Pipeline (Bronze -> Silver -> Gold)

### Bronze Layer (Raw)
Exact replicas of SAP extracts and Salesforce sync data. No transformations. Nine tables across two source systems.

### Silver Layer (Cleaned & Enriched)
Three intermediate tables that do the heavy lifting:

1. **customer_master**: Joins SAP KNA1 with T005T (country names), T001 (company info), and SFDC_ACCOUNT (CRM data). Produces one row per customer with both SAP and Salesforce attributes. Flags whether the customer is linked across systems.

2. **order_lines_enriched**: Joins VBAK (order header) + VBAP (order items) + MARA (material master). Translates all SAP codes to readable names. Calculates line totals and total weight.

3. **opportunity_enriched**: Joins SFDC_OPPORTUNITY with SFDC_ACCOUNT and SFDC_CONTACT. Standardizes stage names into categories (WON, LOST, LATE_STAGE, EARLY_STAGE). Calculates days-to-close.

### Gold Layer (Business-Ready)
Two consumption views:

1. **customer_360**: One row per customer with SAP order history aggregates, Salesforce pipeline/won aggregates, and an engagement_status flag (Active - Both Systems, Active - SAP Only, etc.)

2. **revenue_summary**: Monthly revenue by customer from both systems with a variance calculation. Enables revenue reconciliation between SAP orders and Salesforce closed deals.

## What This Enables

- **Revenue reconciliation**: Spot discrepancies where Salesforce says deal X closed for $100K but SAP shows $85K in orders
- **Customer completeness**: Identify Salesforce accounts missing SAP linkage (or vice versa)
- **Cross-system reporting**: "Show me total business with this customer across both systems"
- **Pipeline to fulfillment tracking**: Compare Salesforce pipeline stages to actual SAP order patterns
