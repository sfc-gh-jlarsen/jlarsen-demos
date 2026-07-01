DEFINE DATABASE POWER_USER_SKILL_DEMO;

DEFINE SCHEMA POWER_USER_SKILL_DEMO.BRONZE
    COMMENT = 'Raw source data from SAP ERP and Salesforce CRM';

DEFINE SCHEMA POWER_USER_SKILL_DEMO.SILVER
    COMMENT = 'Cleaned, enriched, and joined intermediate tables';

DEFINE SCHEMA POWER_USER_SKILL_DEMO.GOLD
    COMMENT = 'Business-ready consumption layer';

DEFINE SCHEMA POWER_USER_SKILL_DEMO.FEATURE_DEMO
    COMMENT = 'CHECK constraints and Error Logging feature demonstrations';

DEFINE SCHEMA POWER_USER_SKILL_DEMO.DBT_PROJECT
    COMMENT = 'dbt project object storage';
