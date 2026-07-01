-- models/marts/fct_revenue.sql
-- Issues: materialized as view (expensive agg), cartesian join risk, no unique test on grain

{{ config(materialized='view') }}

SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    p.product_name,
    p.category,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS line_total,
    d.discount_pct,
    (oi.quantity * oi.unit_price) * (1 - COALESCE(d.discount_pct, 0)) AS net_revenue
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_order_items') }} oi
    ON o.order_id = oi.order_id
JOIN {{ ref('stg_products') }} p
    ON oi.product_id = p.product_id
LEFT JOIN {{ ref('stg_discounts') }} d
    ON o.order_id = d.order_id
    -- Missing: AND oi.product_id = d.product_id
    -- This causes row duplication if a discount applies to multiple products
