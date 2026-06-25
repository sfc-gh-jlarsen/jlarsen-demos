# Demo 2a: From SQL to Dashboard in Snowsight

## The Story

> "I've been running these queries in a worksheet to monitor plant performance. Now I need a dashboard I can share with my team — with charts, KPIs, drill-down. In the old world, I'd export to PowerBI Desktop and start building. Watch how fast this happens in Snowflake."

---

## Step 1: Run These Queries in a Worksheet

Copy these into a Snowsight SQL worksheet to show the data is already here:

```sql
-- OEE by production line (last week)
SELECT LINE_NAME,
       ROUND(AVG(AVAILABILITY_PCT * PERFORMANCE_PCT * QUALITY_PCT) * 100, 1) AS oee_pct,
       SUM(GOOD_UNITS_PRODUCED) AS throughput,
       SUM(DOWNTIME_MINUTES) AS total_downtime_min
FROM MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS
WHERE PLANT_ID = 'DET01'
  AND PRODUCTION_DATE >= DATEADD(week, -1, CURRENT_DATE())
GROUP BY LINE_NAME
ORDER BY oee_pct;

-- At-risk deliveries
SELECT WO_ID, PRODUCT_NAME, PROMISE_DATE, RISK_REASON
FROM MFG_SCHEDULING_REPORTING.RAW.DELIVERIES
WHERE PLANT_ID = 'DET01' AND ON_TIME = FALSE;

-- Open issues
SELECT ISSUE_ID, PRODUCTION_LINE, ISSUE_TYPE, SEVERITY, CREATED_AT
FROM MFG_SCHEDULING_REPORTING.RAW.ISSUES
WHERE PLANT_ID = 'DET01' AND STATUS = 'Open'
ORDER BY CREATED_AT DESC;
```

**Talking point:** "Great — I have the data. I can see CNC Machining is underperforming. But I need a visual, I need to filter interactively, I need to share this with my team. In the past, this is where I'd open PowerBI Desktop..."

---

## Step 2: Create the Dashboard with AI

Open a new **Streamlit in Snowflake** app (container runtime) and paste this prompt into the AI assistant:

### Prompt 1: Initial Dashboard

```
Build me a plant performance dashboard for manufacturing using data in MFG_SCHEDULING_REPORTING.RAW.DAILY_PRODUCTION_METRICS (columns: PRODUCTION_DATE, PLANT_ID, PLANT_NAME, LINE_NAME, PRODUCT_NAME, SHIFT_NAME, AVAILABILITY_PCT, PERFORMANCE_PCT, QUALITY_PCT, GOOD_UNITS_PRODUCED, TOTAL_UNITS_PRODUCED, SCRAPPED_UNITS, DOWNTIME_MINUTES).

Also use MFG_SCHEDULING_REPORTING.RAW.DELIVERIES (WO_ID, PRODUCT_NAME, PROMISE_DATE, ESTIMATED_SHIP, ON_TIME, RISK_REASON, PLANT_ID) and MFG_SCHEDULING_REPORTING.RAW.ISSUES (ISSUE_ID, PRODUCTION_LINE, ISSUE_TYPE, DESCRIPTION, SEVERITY, STATUS, CREATED_AT, RESOLVED_AT, PLANT_ID).

Requirements:
- Filter to PLANT_ID = 'DET01'
- KPI row: OEE (Availability x Performance x Quality), On-Time Delivery %, daily throughput, active issue count — all with week-over-week deltas
- OEE trend line chart (8 weeks) with 85% target line
- OEE breakdown bar chart (Availability, Performance, Quality separately)
- On-Time Delivery trend with 95% target line
- At-risk orders table
- Production line utilization horizontal bar chart (color: green >80%, yellow 60-80%, red <60%)
- Use plotly for charts
- Use bind parameters for PLANT_ID (don't put values directly in SQL strings)
- Use st.connection("snowflake") to connect
```

**Deploy it.** Show the team the URL.

---

## Step 3: Iterate — Add Drill-Down

After deploying, come back and paste this follow-up prompt:

### Prompt 2: Add Drill-Down Page

```
Add a second page called "Drill Down" using st.sidebar.radio for navigation. When the user selects a production line:
- Show daily production (GOOD_UNITS_PRODUCED) as a bar chart vs a 150-unit target line for the last 14 days
- Show an issue log table filtered to that line (last 7 days)
- Add a caption at the bottom: "Note: OEE formula is hardcoded (Availability x Performance x Quality). Different plants may define this differently — Semantic Views solve this."

Use bind parameters. Keep the same connection and config pattern from the existing code.
```

**Redeploy.** Show the drill-down working.

---

## Key Demo Points

1. **SQL to dashboard in minutes** — no PowerBI Desktop, no .pbix file, no publish cycle
2. **AI builds 80% of the app** — you describe what you want, it generates the code
3. **Iterate in place** — add features with another prompt, redeploy instantly
4. **It's deployed the moment you hit "Deploy"** — anyone with the role can access the URL
5. **Transition to Demo 2b:** "This works great. But notice the OEE formula is hardcoded in SQL. What if Austin defines OEE differently? That's where Semantic Views come in..."
