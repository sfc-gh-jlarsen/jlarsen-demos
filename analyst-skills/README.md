# Power User Skill Demo: SAP ERP + Salesforce CRM on Snowflake

## What This Is

An end-to-end demo of a SAP ERP + Salesforce CRM data integration on Snowflake, built with a Bronze/Silver/Gold medallion architecture and deployed as a native dbt Project. Includes feature demos for CHECK constraints and DML Error Logging, plus two Cortex Code custom skill files.

## Prerequisites

- Snowflake account with ACCOUNTADMIN (or equivalent)
- [Snow CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) v3.14+
- A Snow CLI connection configured (update connection name in commands below)

## Project Structure

```
dcm/                          -- Database Change Management project
  manifest.yml.template       -- DCM manifest template (copy and fill in your account)
  sources/definitions/
    infrastructure.sql        -- DEFINE DATABASE + 5 schemas

docs/                         -- Reference documentation
  business_context.md         -- SAP/SFDC field mappings, lookup tables, architecture
  coco_workflow_ideas.md      -- Two workflow concepts for CoCo skill files

dbt/                          -- dbt project (deploys natively to Snowflake)
  dbt_project.yml             -- Project config
  profiles.yml                -- Connection profile (no credentials needed for native deploy)
  models/
    bronze/                   -- Source definitions for 9 raw tables
    silver/                   -- 3 enriched models (customer_master, order_lines, opportunities)
    gold/                     -- 2 consumption views (customer_360, revenue_summary)

scripts/                      -- SQL notebook-style scripts (run in order)
  01_create_bronze_data.sql   -- Creates 9 bronze tables with sample data
  02_feature_demo_check.sql   -- CHECK constraints demo (13 steps)
  03_feature_demo_error_log.sql -- DML Error Logging demo (11 steps)
  04_combined_check_and_error_logging.sql -- Both features together (4 steps)
  999_cleanup.sql             -- Drops all objects

skills/                       -- Cortex Code custom skill files
  revenue-reconciliation/
    SKILL.md                  -- 5-step revenue reconciliation workflow
  customer-onboarding-check/
    SKILL.md                  -- 5-step customer onboarding completeness check
```

## Setup Steps

### 1. Configure DCM Manifest

The `dcm/manifest.yml` is gitignored because it contains your account identifier. Create it from the template:

```bash
cp dcm/manifest.yml.template dcm/manifest.yml
```

Edit `dcm/manifest.yml` and replace `<YOUR_ACCOUNT_IDENTIFIER>` with your Snowflake account locator (e.g., `KSB99694`).

### 2. Deploy Infrastructure (DCM)

```bash
# Create a stage and upload DCM files
snow sql -q "CREATE SCHEMA IF NOT EXISTS DATA_PRODUCT_CONTROL.PROJECTS" -c <connection>
snow sql -q "CREATE STAGE IF NOT EXISTS DATA_PRODUCT_CONTROL.PROJECTS.POWER_USER_SKILL_DEMO_STAGE" -c <connection>
snow stage copy dcm/manifest.yml @DATA_PRODUCT_CONTROL.PROJECTS.POWER_USER_SKILL_DEMO_STAGE/ -c <connection>
snow stage copy dcm/sources/definitions/infrastructure.sql @DATA_PRODUCT_CONTROL.PROJECTS.POWER_USER_SKILL_DEMO_STAGE/sources/definitions/ -c <connection>

# Deploy via SQL
snow sql -q "EXECUTE DCM PROJECT DATA_PRODUCT_CONTROL.PROJECTS.POWER_USER_SKILL_DEMO DEPLOY FROM '@DATA_PRODUCT_CONTROL.PROJECTS.POWER_USER_SKILL_DEMO_STAGE'" -c <connection>
```

### 3. Create Bronze Data

Run `scripts/01_create_bronze_data.sql` in Snowsight or via Snow CLI. This creates 9 tables with realistic sample data (10 SAP customers, 12 sales orders, 25 line items, 12 SFDC accounts, etc.).

### 4. Deploy dbt Project

```bash
cd dbt
snow dbt deploy -c <connection> --database POWER_USER_SKILL_DEMO --schema DBT_PROJECT
snow dbt execute POWER_USER_SKILL_DEMO.DBT_PROJECT.POWER_USER_SKILL_DEMO_DBT -c <connection> --database POWER_USER_SKILL_DEMO --schema DBT_PROJECT
```

This creates Silver tables and Gold views via Snowflake-native dbt execution.

### 5. Run Feature Demos

Run scripts in order in Snowsight (notebook mode recommended):

- `02_feature_demo_check.sql` -- CHECK constraints
- `03_feature_demo_error_log.sql` -- DML Error Logging
- `04_combined_check_and_error_logging.sql` -- Both together

### 6. Cleanup

Run `scripts/999_cleanup.sql` to drop all objects.

## Data Architecture

```
SAP ERP                         Salesforce CRM
  KNA1 (customers)                SFDC_ACCOUNT
  T005T (countries)               SFDC_OPPORTUNITY
  T001 (company codes)            SFDC_CONTACT
  MARA (materials)
  VBAK (order headers)
  VBAP (order line items)
         |                              |
         v                              v
    [ BRONZE -- raw staging layer ]
         |                              |
         v                              v
    [ SILVER -- enriched & joined ]
      customer_master        opportunity_enriched
      order_lines_enriched
         |                              |
         v                              v
    [ GOLD -- business-ready views ]
      customer_360           revenue_summary
```

Cross-system matching: `SAP KNA1.KUNNR` = `SFDC_ACCOUNT.SAP_ACCOUNT_ID__C`

## CoCo Skills

The `skills/` directory contains two Cortex Code custom skill files:

- **revenue-reconciliation** -- Guides CoCo through a monthly revenue comparison between SAP orders and Salesforce closed-won deals, flagging variances above a configurable threshold.
- **customer-onboarding-check** -- Guides CoCo through assessing cross-system customer completeness, categorizing accounts as complete, incomplete, or unlinked.

To use: place the skill folders in your project root or register via Cortex Code settings.
