{{
    config(
        schema='SILVER',
        materialized='table'
    )
}}

SELECT
    vbak.VBELN                          AS order_number,
    vbap.POSNR                          AS item_number,
    vbak.ERDAT                          AS order_date,
    vbak.KUNNR                          AS customer_number,
    vbak.AUART                          AS order_type,
    vbak.BUKRS                          AS company_code,
    vbak.VKORG                          AS sales_org,
    vbap.MATNR                          AS material_number,
    mara.MAKTX                          AS material_description,
    mara.MTART                          AS material_type,
    CASE mara.MTART
        WHEN 'FERT' THEN 'Finished Goods'
        WHEN 'ROH'  THEN 'Raw Material'
        WHEN 'HALB' THEN 'Semi-Finished'
        ELSE mara.MTART
    END                                 AS material_type_name,
    mara.MATKL                          AS material_group,
    vbap.KWMENG                         AS order_quantity,
    mara.MEINS                          AS unit_of_measure,
    vbap.NETPR                          AS unit_price,
    vbak.WAERK                          AS currency,
    vbap.KWMENG * vbap.NETPR           AS line_total,
    vbak.NETWR                          AS order_net_value,
    vbap.WERKS                          AS plant,
    vbap.LGORT                          AS storage_location,
    mara.BRGEW                          AS gross_weight_per_unit,
    mara.GEWEI                          AS weight_unit,
    vbap.KWMENG * mara.BRGEW           AS total_weight

FROM {{ source('sap', 'SAP_VBAK') }} vbak

INNER JOIN {{ source('sap', 'SAP_VBAP') }} vbap
    ON vbak.VBELN = vbap.VBELN

LEFT JOIN {{ source('sap', 'SAP_MARA') }} mara
    ON vbap.MATNR = mara.MATNR
