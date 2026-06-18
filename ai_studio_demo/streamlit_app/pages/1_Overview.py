import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Overview", page_icon="📋", layout="wide")

session = get_active_session()

st.header("Overview & Demo Progress")

st.markdown("""
## Business Context

A global industrial manufacturer receives **~15,000 enterprise support tickets per month** across 
multiple divisions. Tickets arrive via email, portal, and EDI with varying urgency levels.

| Metric | Current State | Target with AI |
|--------|--------------|----------------|
| Time-to-route | ~6 hours (manual) | <30 seconds |
| Misroute rate | ~18% | <5% |
| FTEs for routing | 3 | 0 (automated) |
| Cost per misroute | ~$400 | Avoided |

---
## Demo Progress
""")

try:
    demo_state = session.sql("""
        SELECT NOTEBOOK_ID, COMPLETED_AT 
        FROM AI_STUDIO_DEMO.PUBLIC.DEMO_STATE 
        ORDER BY COMPLETED_AT
    """).to_pandas()

    notebooks = {
        "setup": "1. Setup & Sample Data",
        "function_creation": "2. AI Function Creation",
        "evaluation": "3. Evaluation & Iteration",
        "model_comparison": "4. Model Comparison & RBAC",
    }

    completed_ids = set(demo_state["NOTEBOOK_ID"].tolist()) if not demo_state.empty else set()

    cols = st.columns(4)
    for i, (nb_id, nb_title) in enumerate(notebooks.items()):
        with cols[i]:
            if nb_id in completed_ids:
                ts = demo_state[demo_state["NOTEBOOK_ID"] == nb_id]["COMPLETED_AT"].iloc[0]
                st.success(f"**{nb_title}**\n\nCompleted: {ts}")
            else:
                st.warning(f"**{nb_title}**\n\nNot yet run")

except Exception:
    st.info("Run **Notebook 1 (Setup)** to initialize the demo environment.")
    st.stop()

st.markdown("---")
st.subheader("Sample Data Summary")

try:
    ticket_count = session.sql("SELECT COUNT(*) AS cnt FROM AI_STUDIO_DEMO.PUBLIC.SUPPORT_TICKETS").to_pandas()
    routed_count = session.sql("SELECT COUNT(*) AS cnt FROM AI_STUDIO_DEMO.PUBLIC.ROUTED_TICKETS").to_pandas()

    col1, col2 = st.columns(2)
    col1.metric("Support Tickets Loaded", int(ticket_count["CNT"].iloc[0]))
    col2.metric("Tickets Classified", int(routed_count["CNT"].iloc[0]))

    st.dataframe(
        session.sql("""
            SELECT TICKET_ID, CUSTOMER_NAME, CUSTOMER_ACCOUNT_TIER, 
                   LEFT(TICKET_TEXT, 100) AS PREVIEW
            FROM AI_STUDIO_DEMO.PUBLIC.SUPPORT_TICKETS
            ORDER BY TICKET_ID
        """).to_pandas(),
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Could not query sample data: {e}")
