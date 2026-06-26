-- ============================================================
-- 03: Load Synthetic Data
-- Run data/synthetic_data.py locally then upload, OR use these
-- INSERT statements for a quick setup.
-- ============================================================
-- NOTE: For a full load, use the Python script:
--   python data/synthetic_data.py  (generates CSVs)
--   PUT file://data/*.csv @MFG_SCHEDULING_REPORTING.RAW.DATA_STAGE;
--   COPY INTO ...
--
-- Below is a representative sample for demo purposes.

USE DATABASE MFG_SCHEDULING_REPORTING;

-- Sample user-plant assignments for caller's rights demo
INSERT INTO ADMIN.USER_PLANT_ASSIGNMENTS VALUES
    ('detroit_pm@company.com', 'DET01'),
    ('austin_pm@company.com', 'AUS02'),
    ('monterrey_pm@company.com', 'MTY03'),
    ('regional_vp@company.com', 'DET01'),
    ('regional_vp@company.com', 'AUS02'),
    ('regional_vp@company.com', 'MTY03');

-- Sample production metrics (one day, one line — repeat pattern for full load)
INSERT INTO RAW.DAILY_PRODUCTION_METRICS VALUES
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'CNC Machining Bay A', 'Hydraulic Valve Assembly HV-200', 'Day (6AM-2PM)', 0.88, 0.91, 0.95, 152, 168, 8, 35),
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'Assembly Line 1 North', 'Precision Gear Set PG-450', 'Day (6AM-2PM)', 0.92, 0.89, 0.93, 140, 155, 6, 22),
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'Weld Cell 3', 'Electric Motor Housing EMH-100', 'Swing (2PM-10PM)', 0.85, 0.90, 0.91, 128, 145, 10, 48),
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'Paint & Coat Booth B', 'Control Panel Assembly CPA-75', 'Swing (2PM-10PM)', 0.90, 0.88, 0.96, 160, 172, 5, 28),
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'Final Assembly South', 'Brake Rotor BR-300X', 'Night (10PM-6AM)', 0.87, 0.92, 0.89, 135, 158, 12, 42),
    ('2026-06-23', 'DET01', 'Detroit Manufacturing Center', 'Pack & Ship Dock 1', 'Transmission Shaft TS-500', 'Night (10PM-6AM)', 0.94, 0.93, 0.97, 175, 182, 3, 15);

-- Sample work orders
INSERT INTO RAW.WORK_ORDERS VALUES
    ('WO-2026-1000', 'Hydraulic Valve Assembly HV-200', 'CNC Machining Bay A', 200, '2026-06-30', 'Scheduled', 'Available', 'DET01'),
    ('WO-2026-1001', 'Precision Gear Set PG-450', 'Assembly Line 1 North', 150, '2026-06-28', 'In Progress', 'Available', 'DET01'),
    ('WO-2026-1002', 'Electric Motor Housing EMH-100', 'Weld Cell 3', 100, '2026-06-27', 'Material Hold', 'Shortage', 'DET01'),
    ('WO-2026-1003', 'Control Panel Assembly CPA-75', 'Paint & Coat Booth B', 75, '2026-07-01', 'Scheduled', 'Available', 'DET01'),
    ('WO-2026-1004', 'Brake Rotor BR-300X', 'Final Assembly South', 300, '2026-06-29', 'At Risk', 'Partial', 'DET01');

-- Sample issues
INSERT INTO RAW.ISSUES VALUES
    ('ISS-2000', 'CNC Machining Bay A', 'Machine Breakdown', 'Spindle motor overheating on CNC-04, thermal shutdown triggered', 'High', 'Open', '2026-06-23 08:30:00', NULL, 'DET01'),
    ('ISS-2001', 'Weld Cell 3', 'Quality Hold', 'Dimensional variance exceeding 0.05mm tolerance on gear batch PG-450-B12', 'High', 'Open', '2026-06-22 14:15:00', NULL, 'DET01'),
    ('ISS-2002', 'Assembly Line 1 North', 'Material Delay', 'Supplier delayed shipment of Alloy Steel Billet 4140', 'Medium', 'Open', '2026-06-23 06:00:00', NULL, 'DET01'),
    ('ISS-2003', 'Pack & Ship Dock 1', 'Staffing Gap', 'Night shift 2 operators short, overtime approved', 'Medium', 'Open', '2026-06-22 22:00:00', NULL, 'DET01');
