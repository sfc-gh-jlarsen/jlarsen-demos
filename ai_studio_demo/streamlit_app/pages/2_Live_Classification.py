# Live Classification page for AI Function Studio Demo
# Co-authored with CoCo
import streamlit as st
import json
import os

st.set_page_config(page_title="Live Classification", page_icon="🎯", layout="wide")

session = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")).session()

st.header("Live Ticket Classification")

st.markdown("""
Paste any support ticket text below and the AI function will classify it in real-time.
This calls `CLASSIFY_SUPPORT_TICKET_V2()` which uses `claude-sonnet-4-6` with enum-constrained 
structured output.
""")

with st.expander("How was this function created?"):
    st.code("""CALL SNOWFLAKE.CORTEX.CREATE_AI_FUNCTION(
    'AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2',
    'claude-sonnet-4-6',
    $$You are an enterprise support ticket classifier.
    CRITICAL: Select values EXACTLY from allowed enums...$$,
    $$Classify the following enterprise support ticket:
    {TICKET_TEXT}$$,
    PARSE_JSON('[{"name":"TICKET_TEXT","sql_type":"VARCHAR"}]'),
    PARSE_JSON('[{"name":"division","json_type":"string",...},
                {"name":"priority","json_type":"string",...},
                ...]'),
    'Classify enterprise B2B support tickets',
    NULL,  -- SQL_BODY (NULL = Direct mode)
    NULL   -- STAGE_NAME (no file inputs)
);""", language="sql")

try:
    session.sql("DESCRIBE FUNCTION AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2(VARCHAR)").collect()
except Exception:
    st.warning("Please run **Notebook 2 (AI Function Creation)** first to create the classification function.")
    st.stop()

sample_ticket = (
    "Subject: URGENT - XT-400 structural bond failure on automotive trim assembly\n\n"
    "Our Tier 1 line in Monterrey has been down since 6am. The XT-400 tape is "
    "delaminating from the PP substrate on the 2026 Ranger door trim after "
    "48hrs in the humidity chamber. We ran 3 lots (batches 2026-03-441 through "
    "443) and all failed. This is blocking 2,200 units/day. We need your "
    "application engineering team on-site or on a call within 4 hours. Our plant "
    "manager is looping in the OEM's VP of purchasing if we don't have a path forward today."
)

ticket_text = st.text_area(
    "Ticket Text",
    value=sample_ticket,
    height=200,
    placeholder="Paste a support ticket here...",
)

if st.button("Classify Ticket", type="primary"):
    if not ticket_text.strip():
        st.error("Please enter ticket text.")
    else:
        with st.spinner("Classifying..."):
            escaped = ticket_text.replace("'", "''")
            result = session.sql(
                f"SELECT AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2('{escaped}') AS c"
            ).to_pandas()

            classification = result["C"].iloc[0]
            if classification is None:
                st.error("Classification returned empty. The model may not be available.")
                st.stop()

            if isinstance(classification, str):
                c = json.loads(classification)
            else:
                c = classification

        priority = c.get("priority", "Unknown")
        priority_colors = {
            "P1-Critical": "red",
            "P2-High": "orange",
            "P3-Standard": "blue",
            "P4-Low": "gray",
        }
        color = priority_colors.get(priority, "gray")

        st.markdown(f"### Result: :{color}[{priority}]")

        col1, col2, col3 = st.columns(3)
        col1.metric("Division", c.get("division", "—"))
        col2.metric("Issue Type", c.get("issue_type", "—"))
        col3.metric("Routing Queue", c.get("routing_queue", "—"))

        col4, col5, col6 = st.columns(3)
        col4.metric("Customer Segment", c.get("customer_segment", "—"))
        col5.metric("SLA Flag", str(c.get("sla_flag", False)))
        col6.metric("Response Template", c.get("suggested_response_template", "—"))

        indicators = c.get("escalation_indicators", [])
        if indicators:
            st.markdown("**Escalation Indicators:** " + ", ".join(f"`{i}`" for i in indicators))
        else:
            st.markdown("**Escalation Indicators:** None detected")

        st.markdown(f"**Priority Reasoning:** {c.get('priority_reasoning', '—')}")

        with st.expander("Raw JSON Output"):
            st.json(c)

st.markdown("---")
st.subheader("Batch Classification")
st.markdown("Classify all sample tickets and materialize results into `ROUTED_TICKETS`.")

st.code("""-- Batch classify and materialize (call once, query forever)
INSERT INTO ROUTED_TICKETS (TICKET_ID, TICKET_TEXT, CLASSIFICATION)
SELECT TICKET_ID, TICKET_TEXT, CLASSIFY_SUPPORT_TICKET_V2(TICKET_TEXT)
FROM SUPPORT_TICKETS
WHERE RECEIVED_AT >= DATEADD('hour', -24, CURRENT_TIMESTAMP());

-- Then query materialized results at zero AI cost
SELECT CLASSIFICATION:priority::VARCHAR AS priority,
       CLASSIFICATION:routing_queue::VARCHAR AS queue
FROM ROUTED_TICKETS;""", language="sql")

if st.button("Classify All Sample Tickets"):
    with st.spinner("Running classification on all 15 tickets..."):
        session.sql("""
            INSERT INTO AI_STUDIO_DEMO.PUBLIC.ROUTED_TICKETS (TICKET_ID, TICKET_TEXT, CLASSIFICATION)
            SELECT TICKET_ID, TICKET_TEXT, AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2(TICKET_TEXT)
            FROM AI_STUDIO_DEMO.PUBLIC.SUPPORT_TICKETS
        """).collect()
    st.success("All tickets classified and stored in ROUTED_TICKETS.")

    results = session.sql("""
        SELECT 
            CLASSIFICATION:priority::VARCHAR AS priority,
            COUNT(*) AS cnt
        FROM AI_STUDIO_DEMO.PUBLIC.ROUTED_TICKETS
        GROUP BY 1 ORDER BY 1
    """).to_pandas()
    st.bar_chart(results.set_index("PRIORITY"))
