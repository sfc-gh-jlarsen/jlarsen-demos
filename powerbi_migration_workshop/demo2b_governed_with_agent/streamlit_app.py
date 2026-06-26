# Governed Plant Dashboard powered by Semantic View
# Co-authored with CoCo
"""
Demo 2b: Governed Plant Dashboard with Semantic View
=====================================================
Multi-page Streamlit app backed by a Semantic View for governed metrics.

Runtime: Container (Deployed)
Persona: Plant Manager
"""

import streamlit as st

# --- Page Config ---
st.set_page_config(page_title="Plant Performance Dashboard", layout="wide")

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
