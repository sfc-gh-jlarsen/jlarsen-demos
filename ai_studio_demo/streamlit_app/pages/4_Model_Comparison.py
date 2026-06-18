# Model Comparison page for AI Function Studio Demo
# Co-authored with CoCo
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Model Comparison", page_icon="⚖️", layout="wide")

session = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")).session()

st.header("Model Comparison & RBAC")

try:
    session.sql("SELECT 1 FROM AI_STUDIO_DEMO.PUBLIC.MODEL_COMPARISON_RESULTS LIMIT 1").collect()
except Exception:
    st.warning("Please run **Notebook 4 (Model Comparison & RBAC)** first to materialize model comparison results.")
    st.stop()


@st.cache_data(ttl=300)
def get_scorecard():
    return session.sql("""
        SELECT
          model_name,
          COUNT(*) AS n_tests,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:priority::VARCHAR = predicted:priority::VARCHAR, 1.0, 0.0)), 3) AS priority_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:division::VARCHAR = predicted:division::VARCHAR, 1.0, 0.0)), 3) AS division_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:issue_type::VARCHAR = predicted:issue_type::VARCHAR, 1.0, 0.0)), 3) AS issue_type_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:customer_segment::VARCHAR = predicted:customer_segment::VARCHAR, 1.0, 0.0)), 3) AS segment_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:sla_flag::BOOLEAN = predicted:sla_flag::BOOLEAN, 1.0, 0.0)), 3) AS sla_flag_acc,
          ROUND(
            AVG(IFF(EXPECTED_OUTPUT:priority::VARCHAR = predicted:priority::VARCHAR, 1.0, 0.0)) * 0.4 +
            AVG(IFF(EXPECTED_OUTPUT:division::VARCHAR = predicted:division::VARCHAR, 1.0, 0.0)) * 0.3 +
            AVG(IFF(EXPECTED_OUTPUT:issue_type::VARCHAR = predicted:issue_type::VARCHAR, 1.0, 0.0)) * 0.2 +
            AVG(IFF(EXPECTED_OUTPUT:sla_flag::BOOLEAN = predicted:sla_flag::BOOLEAN, 1.0, 0.0)) * 0.1
          , 3) AS weighted_composite
        FROM AI_STUDIO_DEMO.PUBLIC.MODEL_COMPARISON_RESULTS
        GROUP BY model_name
        ORDER BY weighted_composite DESC
    """).to_pandas()


@st.cache_data(ttl=300)
def get_p1_misses():
    return session.sql("""
        SELECT model_name, TEST_ID,
          EXPECTED_OUTPUT:priority::VARCHAR AS expected,
          predicted:priority::VARCHAR AS predicted
        FROM AI_STUDIO_DEMO.PUBLIC.MODEL_COMPARISON_RESULTS
        WHERE EXPECTED_OUTPUT:priority::VARCHAR = 'P1-Critical'
          AND predicted:priority::VARCHAR != 'P1-Critical'
        ORDER BY model_name, TEST_ID
    """).to_pandas()


st.subheader("Model Scorecard")
st.markdown("6 models tested with identical prompts. Ranked by weighted composite score.")

with st.expander("How model functions are created"):
    st.code("""-- Same prompt, different model parameter (param 2)
CALL SNOWFLAKE.CORTEX.CREATE_AI_FUNCTION(
    'AI_STUDIO_DEMO.PUBLIC.CLASSIFY_TICKET_GPT5_MINI',
    'openai-gpt-5-mini',   -- <-- only this changes
    $$...same system prompt...$$,
    $$Classify this ticket: {TICKET_TEXT}$$,
    PARSE_JSON('[{"name":"TICKET_TEXT","sql_type":"VARCHAR"}]'),
    PARSE_JSON('[...same outputs...]'),
    'Model comparison - openai-gpt-5-mini',
    NULL, NULL
);""", language="sql")

scorecard = get_scorecard()

cost_map = {
    "openai-gpt-5-mini": "$",
    "llama3.3-70b": "$",
    "mistral-large2": "$$",
    "claude-sonnet-4-6": "$$$",
    "openai-gpt-5": "$$$",
    "claude-opus-4-6": "$$$$",
}
scorecard["COST_TIER"] = scorecard["MODEL_NAME"].map(cost_map).fillna("?")

display_cols = ["MODEL_NAME", "COST_TIER", "WEIGHTED_COMPOSITE", "PRIORITY_ACC", "DIVISION_ACC", "ISSUE_TYPE_ACC", "SEGMENT_ACC", "SLA_FLAG_ACC"]
st.dataframe(
    scorecard[display_cols].rename(columns={
        "MODEL_NAME": "Model",
        "COST_TIER": "Cost",
        "WEIGHTED_COMPOSITE": "Composite",
        "PRIORITY_ACC": "Priority",
        "DIVISION_ACC": "Division",
        "ISSUE_TYPE_ACC": "Issue Type",
        "SEGMENT_ACC": "Segment",
        "SLA_FLAG_ACC": "SLA Flag",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.subheader("Field-Level Accuracy by Model")

chart_fields = ["PRIORITY_ACC", "DIVISION_ACC", "ISSUE_TYPE_ACC", "SEGMENT_ACC", "SLA_FLAG_ACC"]
chart_labels = ["Priority", "Division", "Issue Type", "Segment", "SLA Flag"]

chart_rows = []
for _, row in scorecard.iterrows():
    for field, label in zip(chart_fields, chart_labels):
        chart_rows.append({"Model": row["MODEL_NAME"], "Field": label, "Accuracy": float(row[field])})

chart_df = pd.DataFrame(chart_rows)
pivot = chart_df.pivot(index="Field", columns="Model", values="Accuracy")
st.bar_chart(pivot, use_container_width=True)

st.markdown("---")
st.subheader("P1 Safety Deep-Dive")
st.markdown("""
**Zero tolerance for P1 misclassification.** A missed P1 means a production line stays down 
or a safety incident goes unescalated. Which models get P1 tickets wrong?
""")

p1_misses = get_p1_misses()
if p1_misses.empty:
    st.success("All models correctly identified all P1-Critical tickets.")
else:
    st.error(f"**{len(p1_misses)} P1 misclassification(s) detected:**")
    st.dataframe(p1_misses, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Cost / Quality Tradeoff")

cost_numeric = {
    "openai-gpt-5-mini": 1,
    "llama3.3-70b": 1,
    "mistral-large2": 2,
    "claude-sonnet-4-6": 3,
    "openai-gpt-5": 3,
    "claude-opus-4-6": 4,
}
scorecard["COST_NUMERIC"] = scorecard["MODEL_NAME"].map(cost_numeric).fillna(2)

st.scatter_chart(
    scorecard,
    x="COST_NUMERIC",
    y="WEIGHTED_COMPOSITE",
    color="MODEL_NAME",
    size=80,
    use_container_width=True,
)
st.caption("X-axis: relative cost tier (1=budget, 4=high-end). Y-axis: weighted composite accuracy.")

st.markdown("""
### Recommendation

| Scenario | Model Choice | Why |
|----------|-------------|-----|
| High volume, cost sensitive | Cheapest model above 0.85 composite | Minimizes spend |
| Safety-critical (P1 matters most) | Model with 100% P1 recall | No missed escalations |
| Balanced production use | Mid-range model | Best cost/quality sweet spot |
| Tiered approach | Budget for triage + premium for P1/P2 re-check | Optimizes both cost and safety |
""")

st.markdown("---")
st.subheader("RBAC Summary")
st.markdown("""
Two approaches for securing AI functions (both demonstrated in Notebook 4):

| Approach | Best For |
|----------|----------|
| **Account Roles** (`SUPPORT_TICKET_ANALYST`) | Small teams, single-database, quick setup |
| **Database Roles** (`AI_FUNC_EXECUTOR` -> `SUPPORT_AI_CONSUMER_ROLE`) | Enterprise governance, multi-env (dev/prod), portable with clones |

Database roles separate *what access exists* (database role) from *who gets it* (account role). 
They travel with `CLONE` operations, making them ideal for dev/staging/prod consistency.
""")
