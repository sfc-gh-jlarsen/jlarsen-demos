import streamlit as st

st.set_page_config(
    page_title="AI Function Studio Demo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AI Function Studio Demo")
st.subheader("Enterprise Support Ticket Classification")

st.markdown("""
This app walks through the end-to-end workflow for building, evaluating, and
optimizing a custom AI function using Snowflake's Cortex AI Function Studio.

**Use the sidebar to navigate between demo sections:**

| Page | What It Shows |
|------|--------------|
| **Overview** | Business context, demo progress tracker |
| **Live Classification** | Classify tickets in real-time with the AI function |
| **Evaluation** | V1 vs V2 accuracy comparison, custom metrics |
| **Model Comparison** | 6-model scorecard, cost/quality analysis, RBAC |

---

*Run the demo notebooks (1-4) to populate data, then explore results here.*
""")
