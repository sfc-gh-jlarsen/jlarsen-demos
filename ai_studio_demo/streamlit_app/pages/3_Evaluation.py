# Evaluation page for AI Function Studio Demo
# Co-authored with CoCo
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Evaluation", page_icon="📊", layout="wide")

session = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")).session()

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
    v1_scores = [float(v1[f].iloc[0]) for f in fields]
    v2_scores = [float(v2[f].iloc[0]) for f in fields]

    # --- Plotly: Grouped Bar + Radar Chart ---
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'xy'}, {'type': 'polar'}]],
        subplot_titles=('Field-Level Accuracy', 'Performance Profile'),
        column_widths=[0.55, 0.45]
    )

    fig.add_trace(
        go.Bar(name='V1 (Baseline)', x=labels, y=v1_scores,
               marker_color='#FF6B6B', text=[f'{s:.0%}' for s in v1_scores],
               textposition='outside'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(name='V2 (Improved)', x=labels, y=v2_scores,
               marker_color='#4ECDC4', text=[f'{s:.0%}' for s in v2_scores],
               textposition='outside'),
        row=1, col=1
    )

    # Radar chart
    radar_fields = labels + [labels[0]]
    v1_radar = v1_scores + [v1_scores[0]]
    v2_radar = v2_scores + [v2_scores[0]]

    fig.add_trace(
        go.Scatterpolar(r=v1_radar, theta=radar_fields, fill='toself',
                        name='V1 (Baseline)', line_color='#FF6B6B',
                        fillcolor='rgba(255,107,107,0.2)'),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatterpolar(r=v2_radar, theta=radar_fields, fill='toself',
                        name='V2 (Improved)', line_color='#4ECDC4',
                        fillcolor='rgba(78,205,196,0.2)'),
        row=1, col=2
    )

    fig.update_layout(
        title_text='V1 vs V2 Evaluation Comparison',
        height=450,
        template='plotly_white',
        showlegend=True,
        legend=dict(x=0.35, y=-0.15, orientation='h')
    )
    fig.update_yaxes(range=[0, 1.15], tickformat='.0%', row=1, col=1)
    fig.update_polars(radialaxis=dict(range=[0, 1], tickformat='.0%'))
    fig.update_layout(barmode='group')

    st.plotly_chart(fig, use_container_width=True)

    # --- Raw Scores Table ---
    st.markdown("### Raw Scores")
    scores = pd.DataFrame({
        "Field": labels,
        "V1 (baseline)": v1_scores,
        "V2 (improved)": v2_scores,
    })
    scores["Delta"] = scores["V2 (improved)"] - scores["V1 (baseline)"]
    st.dataframe(scores, use_container_width=True, hide_index=True)

    # --- Plotly: Weighted Score Breakdown ---
    st.markdown("---")
    st.subheader("Weighted Score Breakdown: Business-Impact View")
    st.markdown("""
Not all fields are equally important. A misclassified **priority** (which drives SLA timers 
and escalation) is far more costly than a misclassified segment. Weights reflect business impact:

| Field | Weight | Rationale |
|-------|--------|-----------|
| Priority | 0.4 | Drives SLA escalation and response times |
| Division | 0.3 | Routes to correct engineering team |
| Issue Type | 0.2 | Determines playbook / resolution path |
| SLA Flag | 0.1 | Binary derivative of priority + segment |
""")

    weight_labels = ['Priority (x0.4)', 'Division (x0.3)', 'Issue Type (x0.2)', 'SLA Flag (x0.1)']
    acc_cols = ['PRIORITY_ACC', 'DIVISION_ACC', 'ISSUE_TYPE_ACC', 'SLA_FLAG_ACC']
    weight_vals = [0.4, 0.3, 0.2, 0.1]

    v1_contribs = [float(v1[c].iloc[0]) * w for c, w in zip(acc_cols, weight_vals)]
    v2_contribs = [float(v2[c].iloc[0]) * w for c, w in zip(acc_cols, weight_vals)]
    v1_total = sum(v1_contribs)
    v2_total = sum(v2_contribs)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name='V1 (Baseline)', x=weight_labels, y=v1_contribs,
        marker_color='#FF6B6B', text=[f'{c:.3f}' for c in v1_contribs],
        textposition='outside'
    ))
    fig2.add_trace(go.Bar(
        name='V2 (Improved)', x=weight_labels, y=v2_contribs,
        marker_color='#4ECDC4', text=[f'{c:.3f}' for c in v2_contribs],
        textposition='outside'
    ))

    fig2.add_annotation(
        x=0.5, y=1.08, xref='paper', yref='paper',
        text=f'<b>Weighted Total — V1: {v1_total:.3f} | V2: {v2_total:.3f} | Improvement: +{v2_total - v1_total:.3f}</b>',
        showarrow=False, font=dict(size=13)
    )

    fig2.update_layout(
        yaxis_title='Weighted Contribution to Score',
        yaxis=dict(range=[0, 0.48]),
        barmode='group',
        template='plotly_white',
        height=420,
        legend=dict(x=0.01, y=0.95)
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    ### Key Insight
    
    **Issue Type accuracy jumps from ~8% to ~90%+** when enum constraints are added to the 
    `response_format` schema. The model can no longer paraphrase — it must select from the 
    allowed values at the token generation level.
    
    Priority — the highest-weighted field at 0.4 — is where V2 shows its biggest 
    business-impact improvement. The `response_format` enum fix directly addressed 
    the most impactful field.
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
