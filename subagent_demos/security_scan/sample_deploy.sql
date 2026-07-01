-- ============================================================================
-- NOTE: This file contains INTENTIONALLY INSECURE code for DEMO PURPOSES ONLY.
-- All credentials, keys, and account identifiers are fake/example values.
-- DO NOT use any patterns from this file in production.
-- ============================================================================

-- Sample deployment script with security anti-patterns.
-- Use the prompt in PROMPT.md to have a CoCo subagent identify each issue.

-- 1. Hardcoded password in CREATE USER
CREATE USER svc_etl_loader
    PASSWORD = 'Pr0duction_P@ss2024!'
    DEFAULT_ROLE = ETL_LOADER
    DEFAULT_WAREHOUSE = LOAD_WH;

-- 2. Overly permissive grant to PUBLIC
GRANT ALL PRIVILEGES ON DATABASE analytics_prod TO ROLE PUBLIC;

GRANT USAGE ON WAREHOUSE compute_wh TO ROLE PUBLIC;

-- 3. External stage with embedded AWS credentials
CREATE OR REPLACE STAGE raw_data_stage
    URL = 's3://company-data-lake/raw/'
    CREDENTIALS = (
        AWS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
        AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    )
    FILE_FORMAT = (TYPE = PARQUET);

-- 4. Network policy allowing all IPs
CREATE OR REPLACE NETWORK POLICY open_access_policy
    ALLOWED_IP_LIST = ('0.0.0.0/0')
    COMMENT = 'Temporary policy for debugging';

ALTER ACCOUNT SET NETWORK_POLICY = open_access_policy;

-- 5. Disabling data retention (makes Time Travel impossible)
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 0;

-- 6. Creating a share with no restrictions
CREATE SHARE unrestricted_share;
GRANT USAGE ON DATABASE analytics_prod TO SHARE unrestricted_share;
GRANT USAGE ON SCHEMA analytics_prod.public TO SHARE unrestricted_share;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics_prod.public TO SHARE unrestricted_share;
GRANT SELECT ON ALL VIEWS IN SCHEMA analytics_prod.public TO SHARE unrestricted_share;

-- 7. Service account with ACCOUNTADMIN
GRANT ROLE ACCOUNTADMIN TO USER svc_etl_loader;

-- 8. Stored procedure with caller's rights accessing sensitive data without validation
CREATE OR REPLACE PROCEDURE get_user_data(user_email STRING)
RETURNS TABLE()
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
    -- No input validation, no audit logging, caller's rights = runs as whoever calls it
    RETURN TABLE(
        SELECT * FROM hr.employees WHERE email = :user_email
    );
END;
