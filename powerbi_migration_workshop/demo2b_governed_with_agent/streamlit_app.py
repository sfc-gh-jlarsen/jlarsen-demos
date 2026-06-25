"""
Demo 2b: Governed Plant Dashboard with Semantic View + Cortex Agent Sidebar
===========================================================================
Multi-page Streamlit app backed by a Semantic View for governed metrics.
Includes a Cortex Agent chat sidebar for natural language Q&A.

Runtime: Container (Deployed)
Persona: Plant Manager
"""

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.synthetic_data import (
    get_changeover_history,
    get_delivery_data,
    get_issues,
    get_line_utilization,
    get_oee_data,
    get_on_time_delivery_trend,
)

# --- Page Config ---
st.set_page_config(page_title="Plant Performance Dashboard", layout="wide")

# --- Cortex Agent Sidebar ---
AGENT_NAME = "MFG_SCHEDULING_REPORTING.ANALYTICS.PRODUCTION_ANALYST"
SEMANTIC_VIEW = "MFG_SCHEDULING_REPORTING.ANALYTICS.MANUFACTURING_OPERATIONS"


def _get_agent_response(question: str):
    """Send a question to the Cortex Agent and return the response text."""
    try:
        from snowflake.core import Root
        from snowflake.snowpark.context import get_active_session

        session = get_active_session()
        root = Root(session)
        agent = root.databases["MFG_SCHEDULING_REPORTING"].schemas["ANALYTICS"].cortex_agents[
            "PRODUCTION_ANALYST"
        ]

        response = agent.complete(
            model="claude-3.5-sonnet",
            tools=[
                {
                    "type": "cortex_analyst_tool",
                    "tool_spec": {"semantic_view": SEMANTIC_VIEW},
                }
            ],
            messages=[{"role": "user", "content": question}],
        )

        # Extract text from response
        for item in response.messages:
            if item.get("role") == "assistant":
                for block in item.get("content", []):
                    if block.get("type") == "text":
                        return block["text"]
        return "No response generated."
    except Exception as e:
        return f"Agent unavailable — ensure the agent is deployed.\n\nError: {e}"


with st.sidebar:
    st.markdown("#### Ask AI About Production")
    st.caption(f"Powered by Cortex Agent → Semantic View: `manufacturing_operations`")

    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []

    # Sample questions as buttons
    sample_questions = [
        "What's driving the OEE drop this week?",
        "Which line has the most unplanned downtime?",
        "Compare this week's throughput to the 4-week average",
    ]
    for q in sample_questions:
        if st.button(q, key=f"sample_{q[:20]}"):
            st.session_state.agent_messages.append({"role": "user", "content": q})
            with st.spinner("Querying..."):
                answer = _get_agent_response(q)
            st.session_state.agent_messages.append({"role": "assistant", "content": answer})

    # Chat input
    user_input = st.chat_input("Ask a production question...")
    if user_input:
        st.session_state.agent_messages.append({"role": "user", "content": user_input})
        with st.spinner("Querying..."):
            answer = _get_agent_response(user_input)
        st.session_state.agent_messages.append({"role": "assistant", "content": answer})

    # Display message history
    for msg in st.session_state.agent_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Navigation ---
page = st.navigation([
    st.Page("pages/plant_overview.py", title="Plant Overview", icon="🏭", default=True),
    st.Page("pages/drill_down.py", title="Drill Down", icon="🔍"),
])

st.markdown(
    "<small>📐 Powered by Semantic View: <code>manufacturing_operations</code></small>",
    unsafe_allow_html=True,
)
page.run()
