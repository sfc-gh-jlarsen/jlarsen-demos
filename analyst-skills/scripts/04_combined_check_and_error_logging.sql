--------------------------------------------------------------------
-- DEMO: CHECK Constraints + Error Logging -- Better Together
-- Power User Skill Demo
--------------------------------------------------------------------
USE DATABASE POWER_USER_SKILL_DEMO;
USE SCHEMA FEATURE_DEMO;

--------------------------------------------------------------------
-- STEP 1: Create a table with BOTH features
--------------------------------------------------------------------
CREATE OR REPLACE TABLE SHIPMENTS (
    shipment_id     INT NOT NULL,
    customer_name   VARCHAR(50) NOT NULL,
    weight_kg       NUMBER(8,2)     CONSTRAINT chk_weight CHECK (weight_kg > 0),
    ship_date       DATE NOT NULL,
    priority        VARCHAR(10)     CONSTRAINT chk_priority CHECK (priority IN ('LOW','MEDIUM','HIGH'))
) ERROR_LOGGING = TRUE;

--------------------------------------------------------------------
-- STEP 2: Insert a mix -- good rows land, bad rows are captured
--------------------------------------------------------------------
INSERT INTO SHIPMENTS VALUES
    (1, 'Apex Manufacturing',     120.50, '2026-04-28', 'HIGH'),
    (2, 'Northern Steel Corp',    -5.00,  '2026-04-28', 'MEDIUM'),
    (3, NULL,                      45.00, '2026-04-28', 'LOW'),
    (4, 'Precision Parts GmbH',   80.00,  '2026-04-28', 'URGENT'),
    (5, 'Global Motors Ltd',      200.00, '2026-04-28', 'HIGH');

-- 3 rows inserted (1, 4... wait, 4 fails CHECK). Let's see:
SELECT * FROM SHIPMENTS ORDER BY shipment_id;

--------------------------------------------------------------------
-- STEP 3: Error table shows CHECK + NOT NULL failures together
--------------------------------------------------------------------
SELECT
    error_metadata:error_message::STRING  AS error_message,
    error_metadata:error_source::STRING   AS failed_column,
    error_data:SHIPMENT_ID               AS original_id,
    error_data:CUSTOMER_NAME             AS original_name,
    error_data:WEIGHT_KG                 AS original_weight,
    error_data:PRIORITY                  AS original_priority
FROM ERROR_TABLE(SHIPMENTS);

--------------------------------------------------------------------
-- STEP 4: Recover what we can, fix what we can't
--------------------------------------------------------------------
INSERT INTO SHIPMENTS
SELECT
    error_data:SHIPMENT_ID::INT,
    COALESCE(error_data:CUSTOMER_NAME::STRING, 'UNKNOWN'),
    ABS(error_data:WEIGHT_KG::NUMBER(8,2)),
    error_data:SHIP_DATE::DATE,
    CASE WHEN error_data:PRIORITY::STRING NOT IN ('LOW','MEDIUM','HIGH')
         THEN 'MEDIUM' ELSE error_data:PRIORITY::STRING END
FROM ERROR_TABLE(SHIPMENTS)
WHERE error_data:SHIP_DATE IS NOT NULL;

SELECT * FROM SHIPMENTS ORDER BY shipment_id;

--------------------------------------------------------------------
-- That's it. CHECK enforces the rules, Error Logging catches the
-- failures gracefully. No rows lost, full recovery possible.
--------------------------------------------------------------------
