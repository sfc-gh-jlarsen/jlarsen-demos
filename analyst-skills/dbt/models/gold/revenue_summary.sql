{{
    config(
        schema='GOLD',
        materialized='view'
    )
}}

WITH sap_revenue AS (
    SELECT
        ol.customer_number,
        cm.customer_name,
        cm.country_name,
        cm.industry_sector_name,
        ol.currency,
        ol.company_code,
        DATE_TRUNC('month', ol.order_date)          AS revenue_month,
        COUNT(DISTINCT ol.order_number)              AS order_count,
        SUM(ol.line_total)                           AS sap_order_revenue,
        SUM(ol.total_weight)                         AS total_weight_shipped
    FROM {{ ref('order_lines_enriched') }} ol
    LEFT JOIN {{ ref('customer_master') }} cm
        ON ol.customer_number = cm.customer_number
    GROUP BY ALL
),

sfdc_revenue AS (
    SELECT
        opp.sap_customer_number                      AS customer_number,
        opp.account_name                             AS customer_name,
        opp.billing_country                          AS country_name,
        opp.industry,
        DATE_TRUNC('month', opp.close_date)          AS revenue_month,
        COUNT(*)                                     AS deal_count,
        SUM(opp.opportunity_amount)                  AS sfdc_closed_revenue
    FROM {{ ref('opportunity_enriched') }} opp
    WHERE opp.stage_category = 'WON'
      AND opp.sap_customer_number IS NOT NULL
    GROUP BY ALL
)

SELECT
    COALESCE(s.customer_number, f.customer_number)   AS customer_number,
    COALESCE(s.customer_name, f.customer_name)       AS customer_name,
    COALESCE(s.country_name, f.country_name)         AS country_name,
    COALESCE(s.industry_sector_name, f.industry)     AS industry,
    COALESCE(s.revenue_month, f.revenue_month)       AS revenue_month,
    s.currency                                       AS sap_currency,
    COALESCE(s.order_count, 0)                       AS sap_order_count,
    COALESCE(s.sap_order_revenue, 0)                 AS sap_order_revenue,
    COALESCE(s.total_weight_shipped, 0)              AS total_weight_shipped,
    COALESCE(f.deal_count, 0)                        AS sfdc_deal_count,
    COALESCE(f.sfdc_closed_revenue, 0)               AS sfdc_closed_revenue,
    COALESCE(s.sap_order_revenue, 0) - COALESCE(f.sfdc_closed_revenue, 0) AS revenue_variance,
    CASE
        WHEN s.sap_order_revenue IS NOT NULL AND f.sfdc_closed_revenue IS NOT NULL THEN 'Both Systems'
        WHEN s.sap_order_revenue IS NOT NULL THEN 'SAP Only'
        ELSE 'SFDC Only'
    END                                              AS data_source

FROM sap_revenue s

FULL OUTER JOIN sfdc_revenue f
    ON s.customer_number = f.customer_number
    AND s.revenue_month = f.revenue_month
