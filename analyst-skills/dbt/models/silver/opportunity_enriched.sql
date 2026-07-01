{{
    config(
        schema='SILVER',
        materialized='table'
    )
}}

SELECT
    opp.ID                              AS opportunity_id,
    opp.NAME                            AS opportunity_name,
    opp.AMOUNT                          AS opportunity_amount,
    opp.STAGE_NAME                      AS stage,
    CASE
        WHEN opp.STAGE_NAME = 'Closed Won' THEN 'WON'
        WHEN opp.STAGE_NAME = 'Closed Lost' THEN 'LOST'
        WHEN opp.STAGE_NAME IN ('Negotiation', 'Proposal') THEN 'LATE_STAGE'
        ELSE 'EARLY_STAGE'
    END                                 AS stage_category,
    opp.CLOSE_DATE                      AS close_date,
    opp.TYPE                            AS opportunity_type,
    opp.LEAD_SOURCE                     AS lead_source,
    opp.CREATED_DATE                    AS created_date,
    DATEDIFF('day', opp.CREATED_DATE, opp.CLOSE_DATE) AS days_to_close,
    acct.ID                             AS account_id,
    acct.NAME                           AS account_name,
    acct.SAP_ACCOUNT_ID__C              AS sap_customer_number,
    acct.INDUSTRY                       AS industry,
    acct.BILLINGCOUNTRY                 AS billing_country,
    acct.ANNUAL_REVENUE                 AS annual_revenue,
    acct.OWNER_NAME                     AS account_owner,
    cont.FIRST_NAME || ' ' || cont.LAST_NAME AS primary_contact_name,
    cont.EMAIL                          AS primary_contact_email,
    cont.TITLE                          AS primary_contact_title

FROM {{ source('salesforce', 'SFDC_OPPORTUNITY') }} opp

INNER JOIN {{ source('salesforce', 'SFDC_ACCOUNT') }} acct
    ON opp.ACCOUNT_ID = acct.ID

LEFT JOIN (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY ACCOUNT_ID ORDER BY ID) AS rn
    FROM {{ source('salesforce', 'SFDC_CONTACT') }}
) cont
    ON cont.ACCOUNT_ID = acct.ID
    AND cont.rn = 1
