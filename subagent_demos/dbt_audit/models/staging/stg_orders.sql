-- models/staging/stg_orders.sql
-- Anti-pattern: SELECT * in a staging model

{{ config(materialized='view') }}

SELECT *
FROM {{ source('raw', 'orders') }}
