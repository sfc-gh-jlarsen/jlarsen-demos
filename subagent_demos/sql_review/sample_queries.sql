-- Sample queries with intentional correctness issues.
-- Use the prompt in PROMPT.md to have a CoCo subagent find and explain each bug.

-- 1. NULL comparison (= instead of IS)
SELECT order_id, customer_id, total_amount
FROM orders
WHERE discount_code = NULL;

-- 2. Integer division losing precision
SELECT
    warehouse_name,
    total_credits_used / total_queries AS avg_cost_per_query
FROM warehouse_metering_history
WHERE total_queries > 0;

-- 3. LEFT JOIN nullified by WHERE clause
SELECT
    c.customer_name,
    o.order_id,
    o.order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2024-01-01';

-- 4. UNION deduplicating when you want all rows
SELECT product_id, quantity, 'returns' AS source
FROM product_returns
UNION
SELECT product_id, quantity, 'exchanges' AS source
FROM product_exchanges;

-- 5. FLATTEN without LATERAL join losing outer rows
SELECT
    r.request_id,
    f.value:name::STRING AS tag_name
FROM api_requests r,
    LATERAL FLATTEN(input => r.tags) f
WHERE r.created_at >= CURRENT_DATE - 30;
-- Problem: requests with NULL or empty tags array are silently dropped

-- 6. GROUP BY with wrong granularity
SELECT
    DATE_TRUNC('month', order_date) AS order_month,
    customer_id,
    SUM(total_amount) AS monthly_total
FROM orders
GROUP BY order_month;
-- Missing customer_id in GROUP BY — Snowflake will error, but intent is unclear

-- 7. QUALIFY without understanding window scope
SELECT
    employee_id,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees
QUALIFY dept_rank <= 3
ORDER BY department, salary DESC;
-- This is actually correct — included as a control case.
-- A good reviewer should confirm this is fine rather than flag everything.

-- 8. Cartesian risk from missing join condition
SELECT
    d.date_key,
    p.product_name,
    COALESCE(s.total_sales, 0) AS total_sales
FROM dim_date d
CROSS JOIN dim_product p
LEFT JOIN fact_sales s
    ON s.sale_date = d.date_key;
-- Missing: AND s.product_id = p.product_id
