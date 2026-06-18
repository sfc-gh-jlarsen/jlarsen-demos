-- AI Studio Demo: Full Reset
-- Drops the entire database and all contained objects.
-- Run this to start fresh before re-running the notebooks.

DROP DATABASE IF EXISTS AI_STUDIO_DEMO;

-- Drop account-level roles created by Notebook 4
DROP ROLE IF EXISTS SUPPORT_TICKET_ADMIN;
DROP ROLE IF EXISTS SUPPORT_TICKET_ANALYST;
DROP ROLE IF EXISTS SUPPORT_AI_CONSUMER_ROLE;
