import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Evaluation", page_icon="📊", layout="wide")

session = get_active_session()

st.header("Evaluation & Iteration")

st.markdown("""
This page compares **V1** (no enum enforcement) vs **V2** (response_format enum constraints) 
on the same 12-row labeled test set.

> LLMs are probabilistic. Scores will vary +/- 5-10% between runs. Focus on directional 
> improvement, not absolute numbers.
""")

try:
    session.sql("SELECT 1 FROM AI_STUDIO_DEMO.PUBLIC.EVALUATION_TEST_DATA LIMIT 1").collect()
except Exception:
    st.warning("Please run **Notebook 3 (Evaluation & Iteration)** first to create the test data.")
    st.stop()


@st.cache_data(ttl=300)
def get_v1_accuracy():
    return session.sql("""
        SELECT
          ROUND(AVG(IFF(EXPECTED_OUTPUT:priority::VARCHAR = c:priority::VARCHAR, 1.0, 0.0)), 3) AS priority_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:division::VARCHAR = c:division::VARCHAR, 1.0, 0.0)), 3) AS division_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:issue_type::VARCHAR = c:issue_type::VARCHAR, 1.0, 0.0)), 3) AS issue_type_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:customer_segment::VARCHAR = c:customer_segment::VARCHAR, 1.0, 0.0)), 3) AS segment_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:sla_flag::BOOLEAN = c:sla_flag::BOOLEAN, 1.0, 0.0)), 3) AS sla_flag_acc
        FROM AI_STUDIO_DEMO.PUBLIC.EVALUATION_TEST_DATA t,
        LATERAL (SELECT AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET(t.TICKET_TEXT) AS c)
    """).to_pandas()


@st.cache_data(ttl=300)
def get_v2_accuracy():
    return session.sql("""
        SELECT
          ROUND(AVG(IFF(EXPECTED_OUTPUT:priority::VARCHAR = c:priority::VARCHAR, 1.0, 0.0)), 3) AS priority_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:division::VARCHAR = c:division::VARCHAR, 1.0, 0.0)), 3) AS division_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:issue_type::VARCHAR = c:issue_type::VARCHAR, 1.0, 0.0)), 3) AS issue_type_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:customer_segment::VARCHAR = c:customer_segment::VARCHAR, 1.0, 0.0)), 3) AS segment_acc,
          ROUND(AVG(IFF(EXPECTED_OUTPUT:sla_flag::BOOLEAN = c:sla_flag::BOOLEAN, 1.0, 0.0)), 3) AS sla_flag_acc
        FROM AI_STUDIO_DEMO.PUBLIC.EVALUATION_TEST_DATA t,
        LATERAL (SELECT AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2(t.TICKET_TEXT) AS c)
    """).to_pandas()


st.subheader("V1 vs V2 Accuracy Comparison")

st.markdown("""
Click below to run both versions against the test set. This takes ~60-90 seconds 
(12 rows x 2 models = 24 AI_COMPLETE calls).
""")

if st.button("Run Evaluation", type="primary"):
    with st.spinner("Evaluating V1 (12 tickets)..."):
        v1 = get_v1_accuracy()
    with st.spinner("Evaluating V2 (12 tickets)..."):
        v2 = get_v2_accuracy()

    fields = ["PRIORITY_ACC", "DIVISION_ACC", "ISSUE_TYPE_ACC", "SEGMENT_ACC", "SLA_FLAG_ACC"]
    labels = ["Priority", "Division", "Issue Type", "Segment", "SLA Flag"]

    chart_data = pd.DataFrame({
        "Field": labels + labels,
        "Accuracy": [float(v1[f].iloc[0]) for f in fields] + [float(v2[f].iloc[0]) for f in fields],
        "Version": ["V1 (baseline)"] * 5 + ["V2 (enum-constrained)"] * 5,
    })

    st.bar_chart(
        chart_data.pivot(index="Field", columns="Version", values="Accuracy"),
        use_container_width=True,
    )

    st.markdown("### Raw Scores")
    scores = pd.DataFrame({
        "Field": labels,
        "V1 (baseline)": [float(v1[f].iloc[0]) for f in fields],
        "V2 (improved)": [float(v2[f].iloc[0]) for f in fields],
    })
    scores["Delta"] = scores["V2 (improved)"] - scores["V1 (baseline)"]
    st.dataframe(scores, use_container_width=True)

    st.markdown("""
    ### Key Insight
    
    **Issue Type accuracy jumps from ~8% to ~90%+** when enum constraints are added to the 
    `response_format` schema. The model can no longer paraphrase — it must select from the 
    allowed values at the token generation level.
    
    Other fields show natural variance (+/- 5-10%) which is expected with probabilistic models 
    on a 12-row test set.
    """)

st.markdown("---")
st.subheader("Formal Evaluation via Stored Procedure")

st.markdown("AI Function Studio provides `SNOWFLAKE.CORTEX.EVALUATE_AI_FUNCTION()` for tracked, reproducible evaluation:")

st.code("""-- Evaluate V2 with LLM Judge metric
CALL SNOWFLAKE.CORTEX.EVALUATE_AI_FUNCTION(
    'AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2',  -- function
    'AI_STUDIO_DEMO.PUBLIC.EVALUATION_TEST_DATA',        -- test table
    ARRAY_CONSTRUCT('TICKET_TEXT'),                       -- input columns
    'EXPECTED_OUTPUT',                                    -- label column
    'llm_judge',                                         -- metric
    'claude-sonnet-4-6',                                 -- model
    NULL, NULL,                                          -- sample_size, experiment_name
    PARSE_JSON('{"task_description": "Classify tickets..."}'),
    500, NULL, NULL                                      -- max_length, custom_udf, run_id
);""", language="sql")

st.markdown("---")
st.subheader("Custom Metric: Weighted Field Accuracy")
st.markdown("""
The `WEIGHTED_FIELD_ACCURACY` UDF scores each prediction with business-aligned weights:
- Priority: **40%** (safety-critical)
- Division: **30%** (routing correctness)
- Issue Type: **20%** (categorization)
- SLA Flag: **10%** (service level)
""")

try:
    session.sql("DESCRIBE FUNCTION AI_STUDIO_DEMO.PUBLIC.WEIGHTED_FIELD_ACCURACY(VARCHAR, VARCHAR)").collect()
    st.code("""-- Custom metric UDF for multi-field evaluation
SELECT WEIGHTED_FIELD_ACCURACY(
  '{"priority":"P1-Critical","division":"Safety & Industrial","issue_type":"Product Defect / Failure","sla_flag":true}',
  '{"priority":"P2-High","division":"Safety & Industrial","issue_type":"Product Defect / Failure","sla_flag":false}'
);
-- Returns: {"score": 0.5, "feedback": "Priority: FAIL | Division: PASS | Issue Type: PASS | SLA Flag: FAIL"}

-- Use with EVALUATE_AI_FUNCTION:
CALL SNOWFLAKE.CORTEX.EVALUATE_AI_FUNCTION(
    'AI_STUDIO_DEMO.PUBLIC.CLASSIFY_SUPPORT_TICKET_V2',
    'AI_STUDIO_DEMO.PUBLIC.EVALUATION_TEST_DATA',
    ARRAY_CONSTRUCT('TICKET_TEXT'), 'EXPECTED_OUTPUT',
    'custom', 'claude-sonnet-4-6',
    NULL, NULL, NULL, 500,
    'AI_STUDIO_DEMO.PUBLIC.WEIGHTED_FIELD_ACCURACY',  -- custom metric UDF
    NULL
);""", language="sql")
except Exception:
    st.info("Custom metric UDF not yet created. Run Notebook 3 to create `WEIGHTED_FIELD_ACCURACY`.")
