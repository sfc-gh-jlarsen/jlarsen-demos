-- Deploy script for cost monitoring feature
-- Ticket: DATA-1234

-- Drop old table (breaking change — consumers may depend on this)
DROP TABLE IF EXISTS monitoring.cost_alerts;

CREATE TABLE monitoring.cost_alerts (
    alert_id NUMBER AUTOINCREMENT,
    warehouse_name VARCHAR(256),
    detected_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    credits_used FLOAT,
    average_credits FLOAT,
    multiplier FLOAT,
    alert_sent BOOLEAN DEFAULT FALSE
);

-- Grant to the service account
GRANT SELECT, INSERT ON monitoring.cost_alerts TO ROLE monitor_role;

-- Create task to run every 6 hours
CREATE OR REPLACE TASK monitoring.check_cost_spikes
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 */6 * * * America/Denver'
AS
    CALL monitoring.detect_and_alert();
