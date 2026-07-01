--------------------------------------------------------------------
-- DEMO: DML Error Logging
-- Power User Skill Demo
--
-- This script walks through Snowflake's Error Logging feature.
-- When enabled, valid rows land in the table and invalid rows
-- are captured in an error table for review and recovery.
-- Run each numbered section one at a time.
--------------------------------------------------------------------

USE DATABASE POWER_USER_SKILL_DEMO;
USE SCHEMA FEATURE_DEMO;

--------------------------------------------------------------------
-- STEP 1: Create a table WITH error logging enabled
--------------------------------------------------------------------

CREATE OR REPLACE TABLE ORDERS (
    order_id        INT NOT NULL,
    customer_name   VARCHAR(50) NOT NULL,
    order_date      DATE NOT NULL,
    total_amount    NUMBER(10,2),
    quantity        INT,
    status          VARCHAR(20)
) ERROR_LOGGING = TRUE;

--------------------------------------------------------------------
-- STEP 2: Confirm error logging is on via GET_DDL
--------------------------------------------------------------------

SELECT GET_DDL('TABLE', 'POWER_USER_SKILL_DEMO.FEATURE_DEMO.ORDERS');

--------------------------------------------------------------------
-- STEP 3: Insert a mix of valid and invalid rows
--------------------------------------------------------------------

-- Without error logging, this entire INSERT would FAIL.
-- With error logging, valid rows land, invalid rows go to the error table.

INSERT INTO ORDERS VALUES
    (1, 'Apex Manufacturing', '2026-04-01', 12500.00, 10, 'SHIPPED'),
    (2, NULL, '2026-04-02', 8700.00, 5, 'PENDING'),
    (3, 'Precision Parts GmbH', '2026-04-03', 'not_a_number', 20, 'SHIPPED'),
    (4, 'Global Motors Ltd', '2026-04-04', 55000.00, 100, 'SHIPPED'),
    (5, 'Northern Steel Corp', 'bad_date', 9500.00, 15, 'PENDING'),
    (6, 'Atlas Engineering', '2026-04-06', 18200.00, 25, 'DELIVERED');

--------------------------------------------------------------------
-- STEP 4: Check the table -- only valid rows landed
--------------------------------------------------------------------

SELECT * FROM ORDERS ORDER BY order_id;

--------------------------------------------------------------------
-- STEP 5: Query the error table to see what failed and WHY
--------------------------------------------------------------------

SELECT
    timestamp,
    error_code,
    error_metadata:error_message::STRING    AS error_message,
    error_metadata:error_source::STRING     AS error_column,
    error_data
FROM ERROR_TABLE(ORDERS)
ORDER BY timestamp;

--------------------------------------------------------------------
-- STEP 6: Examine error_data to see the original payload
--------------------------------------------------------------------

SELECT
    error_metadata:error_message::STRING    AS what_went_wrong,
    error_metadata:error_source::STRING     AS which_column,
    error_data:ORDER_ID                     AS original_order_id,
    error_data:CUSTOMER_NAME                AS original_customer_name,
    error_data:TOTAL_AMOUNT                 AS original_total_amount,
    error_data:ORDER_DATE                   AS original_order_date
FROM ERROR_TABLE(ORDERS);

--------------------------------------------------------------------
-- STEP 7: Error recovery -- fix and reinsert bad rows
--------------------------------------------------------------------

INSERT INTO ORDERS (order_id, customer_name, order_date, total_amount, quantity, status)
SELECT
    error_data:ORDER_ID::INT,
    COALESCE(error_data:CUSTOMER_NAME::STRING, 'UNKNOWN'),
    TRY_TO_DATE(error_data:ORDER_DATE::STRING),
    TRY_CAST(error_data:TOTAL_AMOUNT::STRING AS NUMBER(10,2)),
    error_data:QUANTITY::INT,
    error_data:STATUS::STRING
FROM ERROR_TABLE(ORDERS)
WHERE TRY_TO_DATE(error_data:ORDER_DATE::STRING) IS NOT NULL
  AND TRY_CAST(error_data:TOTAL_AMOUNT::STRING AS NUMBER(10,2)) IS NOT NULL;

-- Check: recovered rows should now be in the table
SELECT * FROM ORDERS ORDER BY order_id;

--------------------------------------------------------------------
-- STEP 8: Truncate the error table after recovery
--------------------------------------------------------------------

TRUNCATE ERROR_TABLE(ORDERS);

SELECT COUNT(*) AS remaining_errors FROM ERROR_TABLE(ORDERS);

--------------------------------------------------------------------
-- STEP 9: Error logging works with UPDATE too
--------------------------------------------------------------------

-- First add some rows
INSERT INTO ORDERS VALUES
    (10, 'Summit Materials', '2026-04-10', 6400.00, 8, 'PENDING');

-- This UPDATE will fail for the division-by-zero row
-- but other rows would succeed
UPDATE ORDERS
    SET total_amount = total_amount / (quantity - 8)
    WHERE order_id = 10;

-- Check error table for the UPDATE error
SELECT
    error_metadata:error_message::STRING AS error_message,
    error_data
FROM ERROR_TABLE(ORDERS);

--------------------------------------------------------------------
-- STEP 10: MERGE with error logging
--------------------------------------------------------------------

TRUNCATE ERROR_TABLE(ORDERS);

CREATE OR REPLACE TEMPORARY TABLE ORDERS_STAGING (
    order_id        INT,
    customer_name   VARCHAR(50),
    order_date      DATE,
    total_amount    NUMBER(10,2),
    quantity        INT,
    status          VARCHAR(20)
);

INSERT INTO ORDERS_STAGING VALUES
    (1, 'Apex Manufacturing', '2026-04-01', 13000.00, 10, 'DELIVERED'),
    (20, 'MidWest Fabrication', '2026-04-20', 9200.00, 12, 'SHIPPED'),
    (21, NULL, '2026-04-21', 5500.00, 5, 'PENDING');

MERGE INTO ORDERS tgt
USING ORDERS_STAGING src
    ON tgt.order_id = src.order_id
WHEN MATCHED THEN
    UPDATE SET
        tgt.total_amount = src.total_amount,
        tgt.status = src.status
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_name, order_date, total_amount, quantity, status)
    VALUES (src.order_id, src.customer_name, src.order_date, src.total_amount, src.quantity, src.status);

-- Valid rows merged, invalid row (NULL customer_name) captured
SELECT * FROM ORDERS ORDER BY order_id;

SELECT
    error_metadata:error_message::STRING AS error_message,
    error_data
FROM ERROR_TABLE(ORDERS);

--------------------------------------------------------------------
-- STEP 11: Turn error logging OFF and see the difference
--------------------------------------------------------------------

ALTER TABLE ORDERS SET ERROR_LOGGING = FALSE;

-- Now the same mixed insert FAILS entirely
INSERT INTO ORDERS VALUES
    (30, 'Test Company', '2026-04-30', 1000.00, 5, 'SHIPPED'),
    (31, NULL, '2026-04-30', 2000.00, 10, 'PENDING');

-- Neither row 30 nor row 31 landed
SELECT * FROM ORDERS WHERE order_id IN (30, 31);

-- Turn it back on
ALTER TABLE ORDERS SET ERROR_LOGGING = TRUE;

--------------------------------------------------------------------
-- KEY TAKEAWAYS:
-- 1. ERROR_LOGGING = TRUE is a table property (CREATE TABLE or ALTER TABLE)
-- 2. Valid rows land in the table, invalid rows captured in ERROR_TABLE()
-- 3. error_metadata tells you WHAT went wrong (message, column, error code)
-- 4. error_data gives you the ORIGINAL payload for recovery
-- 5. Works with INSERT, UPDATE, and MERGE
-- 6. TRUNCATE ERROR_TABLE() to clean up after recovery
-- 7. NOT supported with COPY INTO, Snowpipe, or multi-table INSERT
-- 8. Minimal perf impact when no errors; some overhead when errors occur
--------------------------------------------------------------------
