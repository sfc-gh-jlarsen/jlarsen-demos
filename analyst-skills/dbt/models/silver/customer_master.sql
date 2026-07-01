{{
    config(
        schema='SILVER',
        materialized='table'
    )
}}

SELECT
    kna1.KUNNR                          AS customer_number,
    kna1.NAME1                          AS customer_name,
    kna1.NAME2                          AS customer_name_2,
    kna1.STRAS                          AS street_address,
    kna1.ORT01                          AS city,
    kna1.PSTLZ                          AS postal_code,
    kna1.LAND1                          AS country_code,
    t005t.LANDX                         AS country_name,
    kna1.BRSCH                          AS industry_sector_code,
    CASE kna1.BRSCH
        WHEN 'MACH' THEN 'Machinery'
        WHEN 'META' THEN 'Metals'
        WHEN 'AUTO' THEN 'Automotive'
        WHEN 'ELEC' THEN 'Electronics'
        WHEN 'CHEM' THEN 'Chemicals'
        WHEN 'TECH' THEN 'Technology'
        ELSE kna1.BRSCH
    END                                 AS industry_sector_name,
    kna1.KTOKD                          AS account_group,
    CASE kna1.KTOKD
        WHEN 'ZDOM' THEN 'Domestic'
        WHEN 'ZINT' THEN 'International'
        ELSE 'Other'
    END                                 AS customer_type,
    t001.BUKRS                          AS company_code,
    t001.BUTXT                          AS company_name,
    t001.WAERS                          AS company_currency,
    sfdc.ID                             AS salesforce_account_id,
    sfdc.NAME                           AS salesforce_account_name,
    sfdc.INDUSTRY                       AS salesforce_industry,
    sfdc.ANNUAL_REVENUE                 AS salesforce_annual_revenue,
    sfdc.OWNER_NAME                     AS salesforce_owner,
    sfdc.CREATED_DATE                   AS salesforce_created_date,
    CASE
        WHEN sfdc.ID IS NOT NULL THEN TRUE
        ELSE FALSE
    END                                 AS is_linked_to_salesforce

FROM {{ source('sap', 'SAP_KNA1') }} kna1

LEFT JOIN {{ source('sap', 'SAP_T005T') }} t005t
    ON kna1.LAND1 = t005t.LAND1
    AND t005t.SPRAS = 'E'

LEFT JOIN {{ source('sap', 'SAP_T001') }} t001
    ON t001.LAND1 = kna1.LAND1

LEFT JOIN {{ source('salesforce', 'SFDC_ACCOUNT') }} sfdc
    ON sfdc.SAP_ACCOUNT_ID__C = kna1.KUNNR
