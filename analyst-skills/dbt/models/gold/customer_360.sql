{{
    config(
        schema='GOLD',
        materialized='view'
    )
}}

WITH order_summary AS (
    SELECT
        customer_number,
        COUNT(DISTINCT order_number) AS total_orders,
        SUM(line_total)              AS total_order_value,
        MIN(order_date)              AS first_order_date,
        MAX(order_date)              AS last_order_date,
        COUNT(DISTINCT material_number) AS unique_materials_ordered
    FROM {{ ref('order_lines_enriched') }}
    GROUP BY customer_number
),

opportunity_summary AS (
    SELECT
        sap_customer_number,
        COUNT(*)                                                            AS total_opportunities,
        SUM(CASE WHEN stage_category = 'WON' THEN opportunity_amount ELSE 0 END) AS won_revenue,
        SUM(CASE WHEN stage_category IN ('LATE_STAGE', 'EARLY_STAGE') THEN opportunity_amount ELSE 0 END) AS pipeline_value,
        SUM(CASE WHEN stage_category = 'WON' THEN 1 ELSE 0 END)           AS won_deals,
        AVG(CASE WHEN stage_category = 'WON' THEN days_to_close END)       AS avg_days_to_close
    FROM {{ ref('opportunity_enriched') }}
    WHERE sap_customer_number IS NOT NULL
    GROUP BY sap_customer_number
)

SELECT
    cm.customer_number,
    cm.customer_name,
    cm.country_name,
    cm.city,
    cm.industry_sector_name,
    cm.customer_type,
    cm.company_name,
    cm.company_currency,
    cm.is_linked_to_salesforce,
    cm.salesforce_account_name,
    cm.salesforce_owner,
    cm.salesforce_annual_revenue,
    COALESCE(os.total_orders, 0)               AS total_sap_orders,
    COALESCE(os.total_order_value, 0)          AS total_sap_order_value,
    os.first_order_date                        AS sap_first_order,
    os.last_order_date                         AS sap_last_order,
    COALESCE(os.unique_materials_ordered, 0)   AS unique_materials,
    COALESCE(ops.total_opportunities, 0)       AS sfdc_total_opportunities,
    COALESCE(ops.won_revenue, 0)               AS sfdc_won_revenue,
    COALESCE(ops.pipeline_value, 0)            AS sfdc_pipeline_value,
    COALESCE(ops.won_deals, 0)                 AS sfdc_won_deals,
    ops.avg_days_to_close                      AS sfdc_avg_days_to_close,
    CASE
        WHEN os.total_orders > 0 AND ops.won_deals > 0 THEN 'Active - Both Systems'
        WHEN os.total_orders > 0 THEN 'Active - SAP Only'
        WHEN ops.won_deals > 0 THEN 'Active - SFDC Only'
        ELSE 'Inactive'
    END                                        AS engagement_status

FROM {{ ref('customer_master') }} cm

LEFT JOIN order_summary os
    ON cm.customer_number = os.customer_number

LEFT JOIN opportunity_summary ops
    ON cm.customer_number = ops.sap_customer_number
