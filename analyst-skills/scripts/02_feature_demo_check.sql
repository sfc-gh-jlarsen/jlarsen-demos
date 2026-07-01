--------------------------------------------------------------------
-- DEMO: CHECK Constraints on Columns
-- Power User Skill Demo
--
-- This script walks through Snowflake CHECK constraints step by step.
-- Run each numbered section one at a time.
--------------------------------------------------------------------

USE DATABASE POWER_USER_SKILL_DEMO;
USE SCHEMA FEATURE_DEMO;

--------------------------------------------------------------------
-- STEP 1: Create a table with inline CHECK constraints
--------------------------------------------------------------------

CREATE OR REPLACE TABLE PRODUCTS (
    product_id      INT,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(50),
    unit_price      NUMBER(10,2)    CONSTRAINT chk_positive_price CHECK (unit_price > 0),
    weight_kg       NUMBER(8,2)     CONSTRAINT chk_positive_weight CHECK (weight_kg >= 0),
    status          VARCHAR(20)     CONSTRAINT chk_valid_status CHECK (status IN ('ACTIVE', 'DISCONTINUED', 'DRAFT'))
);

--------------------------------------------------------------------
-- STEP 2: Insert valid data -- this succeeds
--------------------------------------------------------------------

INSERT INTO PRODUCTS VALUES
    (1, 'Hydraulic Cylinder HCA-200', 'Hydraulics', 1500.00, 12.50, 'ACTIVE'),
    (2, 'Precision Ball Bearing PBB-50', 'Bearings', 25.00, 0.25, 'ACTIVE'),
    (3, 'Electric Motor EM-1500', 'Motors', 2750.00, 25.00, 'ACTIVE'),
    (4, 'Legacy Pump LP-100', 'Pumps', 890.00, 8.00, 'DISCONTINUED'),
    (5, 'Prototype Valve PV-X', 'Valves', 350.00, 3.20, 'DRAFT');

SELECT * FROM PRODUCTS;

--------------------------------------------------------------------
-- STEP 3: Try inserting a negative price -- FAILS
--------------------------------------------------------------------

-- This will fail: unit_price must be > 0
INSERT INTO PRODUCTS VALUES
    (6, 'Bad Price Item', 'Test', -50.00, 1.00, 'ACTIVE');

--------------------------------------------------------------------
-- STEP 4: Try inserting an invalid status -- FAILS
--------------------------------------------------------------------

-- This will fail: status must be in ('ACTIVE', 'DISCONTINUED', 'DRAFT')
INSERT INTO PRODUCTS VALUES
    (7, 'Invalid Status Item', 'Test', 100.00, 1.00, 'DELETED');

--------------------------------------------------------------------
-- STEP 5: Try inserting a negative weight -- FAILS
--------------------------------------------------------------------

-- This will fail: weight_kg must be >= 0
INSERT INTO PRODUCTS VALUES
    (8, 'Negative Weight Item', 'Test', 100.00, -5.00, 'ACTIVE');

--------------------------------------------------------------------
-- STEP 6: NULL values pass CHECK constraints (only fails on FALSE)
--------------------------------------------------------------------

-- This SUCCEEDS: NULL evaluates to unknown, not FALSE
INSERT INTO PRODUCTS VALUES
    (9, 'Null Price Item', 'Test', NULL, NULL, NULL);

SELECT * FROM PRODUCTS WHERE product_id = 9;

--------------------------------------------------------------------
-- STEP 7: Create a table with out-of-line (multi-column) CHECK
--------------------------------------------------------------------

CREATE OR REPLACE TABLE INVENTORY (
    product_id          INT NOT NULL,
    warehouse_code      VARCHAR(10) NOT NULL,
    quantity_on_hand    INT,
    reorder_point       INT,
    max_quantity        INT,
    CONSTRAINT chk_positive_qty     CHECK (quantity_on_hand >= 0),
    CONSTRAINT chk_reorder_logic    CHECK (reorder_point < max_quantity),
    CONSTRAINT chk_max_limit        CHECK (max_quantity <= 100000)
);

INSERT INTO INVENTORY VALUES
    (1, 'WH-EAST', 150, 50, 500),
    (2, 'WH-EAST', 2000, 500, 5000),
    (3, 'WH-WEST', 800, 200, 2000);

--------------------------------------------------------------------
-- STEP 8: Multi-column constraint violation
--------------------------------------------------------------------

-- This FAILS: reorder_point (600) must be less than max_quantity (500)
INSERT INTO INVENTORY VALUES
    (4, 'WH-WEST', 100, 600, 500);

--------------------------------------------------------------------
-- STEP 9: UPDATE also enforces CHECK constraints
--------------------------------------------------------------------

-- This FAILS: can't set quantity negative
UPDATE INVENTORY SET quantity_on_hand = -10 WHERE product_id = 1;

--------------------------------------------------------------------
-- STEP 10: View CHECK constraints in the information schema
--------------------------------------------------------------------

SELECT
    CONSTRAINT_TABLE,
    CONSTRAINT_NAME,
    CHECK_CLAUSE
FROM POWER_USER_SKILL_DEMO.INFORMATION_SCHEMA.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'FEATURE_DEMO'
ORDER BY CONSTRAINT_TABLE, CONSTRAINT_NAME;

--------------------------------------------------------------------
-- STEP 11: Add a CHECK constraint to an existing table
--------------------------------------------------------------------

ALTER TABLE PRODUCTS
    ADD CONSTRAINT chk_name_length CHECK (LENGTH(product_name) >= 3);

-- Verify it appears
SELECT CONSTRAINT_NAME, CHECK_CLAUSE
FROM POWER_USER_SKILL_DEMO.INFORMATION_SCHEMA.CHECK_CONSTRAINTS
WHERE CONSTRAINT_TABLE = 'PRODUCTS';

-- This now FAILS: product name is too short
INSERT INTO PRODUCTS VALUES (10, 'AB', 'Test', 100.00, 1.00, 'ACTIVE');

--------------------------------------------------------------------
-- STEP 12: Drop a CHECK constraint
--------------------------------------------------------------------

ALTER TABLE PRODUCTS DROP CONSTRAINT chk_name_length;

-- Now the short name works
INSERT INTO PRODUCTS VALUES (10, 'AB', 'Test', 100.00, 1.00, 'ACTIVE');
SELECT * FROM PRODUCTS WHERE product_id = 10;

--------------------------------------------------------------------
-- STEP 13: CTAS also enforces CHECK constraints
--------------------------------------------------------------------

CREATE OR REPLACE TABLE HIGH_VALUE_PRODUCTS (
    product_id INT,
    product_name VARCHAR(100),
    unit_price NUMBER(10,2),
    CONSTRAINT chk_high_value CHECK (unit_price > 500)
) AS
SELECT product_id, product_name, unit_price
FROM PRODUCTS
WHERE unit_price > 500;

SELECT * FROM HIGH_VALUE_PRODUCTS;

--------------------------------------------------------------------
-- KEY TAKEAWAYS:
-- 1. CHECK constraints enforce business rules at the table level
-- 2. They work on INSERT, UPDATE, MERGE, and CTAS
-- 3. NULL values pass (only FALSE triggers a violation)
-- 4. Constraints are named for documentation and easy management
-- 5. View them via INFORMATION_SCHEMA.CHECK_CONSTRAINTS
-- 6. IMPORTANT: NOT supported with COPY INTO, Snowpipe, or streaming
--------------------------------------------------------------------
