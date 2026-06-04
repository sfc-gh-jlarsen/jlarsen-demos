"""
=============================================================================
  Cortex Agent Update Walkthrough - Streamlit App
=============================================================================
  Interactive demo showing how to safely update Cortex Agent orchestration
  instructions without overwriting other fields.

  Run locally:
    streamlit run app.py
=============================================================================
"""

import streamlit as st
import json
import os
import snowflake.connector
import requests
from dotenv import load_dotenv

load_dotenv()

# -- Configuration (from .env) --
CONNECTION_NAME = os.getenv("SNOWFLAKE_CONNECTION_NAME", "default")
DATABASE = os.getenv("SNOWFLAKE_DATABASE", "USER_LOOKUP_DEMO")
SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "AGENT_UPDATE_DEMO")
AGENT_NAME = os.getenv("SNOWFLAKE_AGENT_NAME", "USER_LOOKUP_AGENT")
FQN = f"{DATABASE}.{SCHEMA}.{AGENT_NAME}"

BASELINE_ORCHESTRATION = (
    "You are a user directory assistant. Help users find information about "
    "employees in the directory. Use the search tool to look up users by name."
)

PIN_INSTRUCTION = (
    "\n\nIMPORTANT - PIN VERIFICATION REQUIREMENT:\n"
    'When a user asks about their OWN information (e.g., "what is my access level", '
    '"show my profile", "what groups am I in"), you MUST ask them to provide their '
    "4-digit PIN before revealing any personal information. Do NOT proceed without "
    "PIN verification for self-lookup requests.\n\n"
    'For lookups about OTHER users (e.g., "find Alice Johnson", '
    '"who is in Engineering"), no PIN is required.'
)


# ==============================================================================
# Connection helpers
# ==============================================================================

@st.cache_resource
def get_connection():
    """Get a Snowflake connection using connections.toml."""
    return snowflake.connector.connect(connection_name=CONNECTION_NAME)


def get_cursor():
    """Get a cursor from the cached connection."""
    conn = get_connection()
    return conn.cursor()


def run_sql(sql: str):
    """Execute SQL and return results."""
    cur = get_cursor()
    cur.execute(sql)
    return cur.fetchall(), cur.description


def get_agent_spec() -> dict | None:
    """Get the current agent spec as a parsed dict."""
    try:
        rows, desc = run_sql(f"DESCRIBE AGENT {FQN}")
        if rows:
            # Find agent_spec column by name (position may vary)
            col_names = [col[0].lower() for col in desc]
            spec_idx = col_names.index("agent_spec")
            return json.loads(rows[0][spec_idx])
    except Exception as e:
        st.error(f"Error describing agent: {e}")
    return None


def get_rest_headers():
    """Get REST API headers from the active connection."""
    conn = get_connection()
    token = conn.rest.token
    # Use account locator for the URL (org-account names with underscores
    # are not valid hostnames and cause SSL cert mismatch errors)
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_ACCOUNT()")
    locator = cur.fetchone()[0]
    cur.close()
    account_url = f"https://{locator.lower()}.snowflakecomputing.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Snowflake Token="{token}"',
    }
    return headers, account_url


# ==============================================================================
# Page Config
# ==============================================================================

st.set_page_config(
    page_title="Cortex Agent Update Walkthrough",
    page_icon="🔧",
    layout="wide",
)

st.title("Cortex Agent - Updating Orchestration Instructions")
st.markdown("""
**Problem:** `ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION` completely replaces the entire spec.
If you only include the field you want to change, all other fields are **removed**.

**Solution:** Use the **read-modify-write** pattern:
1. `DESCRIBE AGENT` to get the current full spec
2. Parse & modify the field(s) you want
3. `ALTER AGENT` with the **complete** updated spec
""")

st.divider()

# ==============================================================================
# Sidebar - Agent Status Monitor
# ==============================================================================

with st.sidebar:
    st.header("Agent Config Monitor")

    if st.button("Refresh Status", use_container_width=True):
        st.cache_resource.clear()

    spec = get_agent_spec()
    if spec:
        st.success("Agent exists")

        # Model
        model = spec.get("models", {}).get("orchestration", "N/A")
        st.metric("Model", model)

        # Tools count
        tools = spec.get("tools", [])
        st.metric("Tools", len(tools))

        # PIN status
        orchestration = spec.get("instructions", {}).get("orchestration", "")
        has_pin = "PIN VERIFICATION" in orchestration
        if has_pin:
            st.metric("PIN Requirement", "Active", delta="Enabled")
        else:
            st.metric("PIN Requirement", "Not Set", delta="Disabled", delta_color="off")

        # Spec structure
        with st.expander("Full Spec JSON"):
            st.json(spec)
    else:
        st.warning("Agent not found - run Step 1 to create it")


# ==============================================================================
# TABS
# ==============================================================================

tab_sql, tab_python, tab_rest, tab_test = st.tabs([
    "1. SQL Approach",
    "2. Python Connector",
    "3. REST API",
    "4. Test Agent"
])


# ==============================================================================
# TAB 1: SQL Approach
# ==============================================================================

with tab_sql:
    st.header("SQL Approach: ALTER AGENT via SQL")
    st.markdown("""
    This is the most common approach. You run SQL statements directly
    (via Snowsight, SnowSQL, or the Python connector).
    """)

    # --- Step 1: Create Agent ---
    st.subheader("Step 1: Create the Agent (baseline)")

    create_sql = f"""CREATE OR REPLACE AGENT {FQN}
COMMENT = 'Demo agent for user directory lookups'
FROM SPECIFICATION
$$
models:
  orchestration: auto

instructions:
  orchestration: "{BASELINE_ORCHESTRATION}"
  response: "Be concise. Format results in a clear, readable manner."

tools:
  - tool_spec:
      type: "cortex_search"
      name: "search_users"
      description: "Search the employee directory by name to find user details."

tool_resources:
  search_users:
    name: "{DATABASE}.{SCHEMA}.USER_SEARCH"
    id_column: "UPIN"
    title_column: "DISPLAY_NAME"
    max_results: 5
$$;"""

    st.code(create_sql, language="sql")

    if st.button("Run: Create Agent", key="create_agent"):
        with st.spinner("Creating agent..."):
            try:
                run_sql(create_sql)
                st.success("Agent created successfully!")
                st.cache_resource.clear()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # --- Step 2: Describe ---
    st.subheader("Step 2: DESCRIBE AGENT (read current spec)")
    describe_sql = f"DESCRIBE AGENT {FQN};"
    st.code(describe_sql, language="sql")

    if st.button("Run: Describe Agent", key="describe_agent"):
        spec = get_agent_spec()
        if spec:
            st.json(spec)
            st.info(f"**Key point:** `instructions.orchestration` = `{spec['instructions']['orchestration'][:80]}...`")

    st.divider()

    # --- Step 3: ALTER with PIN ---
    st.subheader("Step 3: ALTER AGENT - Add PIN Requirement")
    st.warning("""
    **Important:** The spec below includes ALL fields (models, tools, tool_resources).
    If you omit any of them, they will be **deleted** from the agent.
    """)

    alter_sql = f"""ALTER AGENT {FQN}
  MODIFY LIVE VERSION SET SPECIFICATION =
  $$
  models:
    orchestration: auto

  instructions:
    orchestration: |
      {BASELINE_ORCHESTRATION}

      IMPORTANT - PIN VERIFICATION REQUIREMENT:
      When a user asks about their OWN information (e.g., "what is my access level",
      "show my profile", "what groups am I in"), you MUST ask them to provide their
      4-digit PIN before revealing any personal information. Do NOT proceed without
      PIN verification for self-lookup requests.

      For lookups about OTHER users (e.g., "find Alice Johnson", "who is in
      Engineering"), no PIN is required.
    response: "Be concise. Format results in a clear, readable manner."

  tools:
    - tool_spec:
        type: "cortex_search"
        name: "search_users"
        description: "Search the employee directory by name to find user details."

  tool_resources:
    search_users:
      name: "{DATABASE}.{SCHEMA}.USER_SEARCH"
      id_column: "UPIN"
      title_column: "DISPLAY_NAME"
      max_results: 5
  $$;"""

    st.code(alter_sql, language="sql")

    if st.button("Run: ALTER AGENT (add PIN)", key="alter_agent"):
        with st.spinner("Altering agent..."):
            try:
                run_sql(alter_sql)
                st.success("Agent updated! PIN requirement added.")
                st.cache_resource.clear()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # --- Step 4: Verify ---
    st.subheader("Step 4: Verify the Update")

    if st.button("Run: Verify Spec", key="verify_spec"):
        spec = get_agent_spec()
        if spec:
            orchestration = spec.get("instructions", {}).get("orchestration", "")
            col1, col2, col3 = st.columns(3)
            col1.metric("PIN Present", "Yes" if "PIN VERIFICATION" in orchestration else "No")
            col2.metric("Tools Count", len(spec.get("tools", [])))
            col3.metric("Model", spec.get("models", {}).get("orchestration", "N/A"))

            if "PIN VERIFICATION" in orchestration:
                st.success("PIN requirement verified in orchestration instructions!")
            else:
                st.error("PIN requirement NOT found - something went wrong.")

            with st.expander("Full Updated Spec"):
                st.json(spec)


# ==============================================================================
# TAB 2: Python Connector
# ==============================================================================

with tab_python:
    st.header("Python Approach: snowflake-connector-python")
    st.markdown("""
    This approach uses the Python connector to programmatically read, modify,
    and write the agent spec. Best for automation and CI/CD pipelines.

    Click the buttons below to step through the pattern. The **Variable Explorer**
    on the right shows you the state of each variable as it changes.
    """)

    python_code = '''import json
import snowflake.connector

# Connect
conn = snowflake.connector.connect(connection_name="default")
cur = conn.cursor()

# STEP 1: Read current spec
cur.execute("DESCRIBE AGENT USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT")
row = cur.fetchone()

# Find agent_spec column by name (don't rely on column index - it can change)
col_names = [col[0].lower() for col in cur.description]
spec_idx = col_names.index("agent_spec")
current_spec = json.loads(row[spec_idx])

# STEP 2: Modify orchestration instructions (append PIN requirement)
existing = current_spec["instructions"]["orchestration"]
pin_requirement = """\\n\\nIMPORTANT - PIN VERIFICATION REQUIREMENT:
When a user asks about their OWN information, you MUST ask them to
provide their 4-digit PIN before revealing any personal information."""

if "PIN VERIFICATION" not in existing:
    current_spec["instructions"]["orchestration"] = existing + pin_requirement

# STEP 3: ALTER with full spec (using $$ delimiters)
spec_json = json.dumps(current_spec)
fqn = "USER_LOOKUP_DEMO.AGENT_UPDATE_DEMO.USER_LOOKUP_AGENT"
alter_sql = f"ALTER AGENT {fqn} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$"
cur.execute(alter_sql)
print("Agent updated successfully!")

cur.close()
conn.close()'''

    st.code(python_code, language="python")

    st.divider()
    st.subheader("Interactive Step-Through")

    # Initialize session state for the variable explorer
    if "py_vars" not in st.session_state:
        st.session_state.py_vars = {}
    if "py_step" not in st.session_state:
        st.session_state.py_step = 0
    if "py_log" not in st.session_state:
        st.session_state.py_log = []

    # Layout: buttons on left, variable explorer on right
    col_actions, col_vars = st.columns([1, 1])

    with col_actions:
        st.markdown("**Actions**")

        if st.button("Step 1: DESCRIBE AGENT (read spec)", key="py_step1"):
            spec = get_agent_spec()
            if spec:
                st.session_state.py_step = 1
                st.session_state.py_vars = {
                    "current_spec": spec,
                    "current_spec['instructions']['orchestration']": spec["instructions"]["orchestration"],
                    "current_spec['models']": spec.get("models", {}),
                    "current_spec['tools']": spec.get("tools", []),
                    "len(current_spec['tools'])": len(spec.get("tools", [])),
                }
                st.session_state.py_log = [
                    ">>> cur.execute('DESCRIBE AGENT ...')",
                    ">>> col_names = [col[0].lower() for col in cur.description]",
                    ">>> spec_idx = col_names.index('agent_spec')",
                    ">>> current_spec = json.loads(row[spec_idx])",
                ]
                st.success("Read current spec into `current_spec`")

        if st.button("Step 2: Modify orchestration (append PIN)", key="py_step2"):
            if st.session_state.py_step < 1:
                st.warning("Run Step 1 first.")
            else:
                spec = st.session_state.py_vars.get("current_spec", {})
                existing = spec.get("instructions", {}).get("orchestration", "")
                if "PIN VERIFICATION" not in existing:
                    spec["instructions"]["orchestration"] = existing + PIN_INSTRUCTION
                    st.session_state.py_step = 2
                    st.session_state.py_vars["current_spec"] = spec
                    st.session_state.py_vars["current_spec['instructions']['orchestration']"] = spec["instructions"]["orchestration"]
                    st.session_state.py_vars["pin_added"] = True
                    st.session_state.py_log.append(">>> existing = current_spec['instructions']['orchestration']")
                    st.session_state.py_log.append(">>> current_spec['instructions']['orchestration'] = existing + pin_requirement")
                    st.success("Appended PIN requirement to orchestration")
                else:
                    st.session_state.py_vars["pin_added"] = False
                    st.info("PIN already present in orchestration - no change.")

        if st.button("Step 3: ALTER AGENT (write full spec)", key="py_step3"):
            if st.session_state.py_step < 2:
                st.warning("Run Steps 1 and 2 first.")
            else:
                spec = st.session_state.py_vars.get("current_spec", {})
                spec_json = json.dumps(spec)
                try:
                    run_sql(f"ALTER AGENT {FQN} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$")
                    st.session_state.py_step = 3
                    st.session_state.py_vars["spec_json"] = spec_json[:200] + "..."
                    st.session_state.py_vars["alter_result"] = "SUCCESS"
                    st.session_state.py_log.append(">>> spec_json = json.dumps(current_spec)")
                    st.session_state.py_log.append(">>> cur.execute(f'ALTER AGENT ... SET SPECIFICATION = $$ {spec_json} $$')")
                    st.session_state.py_log.append("# Agent updated successfully!")
                    st.success("Agent updated with full spec!")
                    st.cache_resource.clear()
                except Exception as e:
                    st.session_state.py_vars["alter_result"] = f"ERROR: {e}"
                    st.error(f"Error: {e}")

        st.divider()

        if st.button("Reset to Baseline (remove PIN)", key="py_reset"):
            with st.spinner("Resetting..."):
                spec = get_agent_spec()
                if spec:
                    spec["instructions"]["orchestration"] = BASELINE_ORCHESTRATION
                    spec_json = json.dumps(spec)
                    run_sql(f"ALTER AGENT {FQN} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$")
                    st.session_state.py_step = 0
                    st.session_state.py_vars = {"reset": True, "orchestration": BASELINE_ORCHESTRATION}
                    st.session_state.py_log = ["# Reset to baseline - PIN removed"]
                    st.success("Reset to baseline (no PIN)")
                    st.cache_resource.clear()

    with col_vars:
        st.markdown("**Variable Explorer**")

        # Step indicator
        step_labels = ["Not started", "1: Read spec", "2: Modified spec", "3: Written to agent"]
        current_step = st.session_state.py_step
        st.progress(current_step / 3 if current_step <= 3 else 1.0, text=f"Step: {step_labels[min(current_step, 3)]}")

        # Show variables
        if st.session_state.py_vars:
            for var_name, var_value in st.session_state.py_vars.items():
                if var_name == "current_spec":
                    with st.expander(f"`{var_name}` (dict, {len(var_value)} keys)", expanded=False):
                        st.json(var_value)
                elif var_name == "current_spec['instructions']['orchestration']":
                    with st.expander(f"`{var_name}`", expanded=True):
                        orchestration_val = var_value
                        # Highlight the PIN section if present
                        if "PIN VERIFICATION" in orchestration_val:
                            parts = orchestration_val.split("IMPORTANT - PIN VERIFICATION")
                            st.text(parts[0])
                            st.markdown(":green[**IMPORTANT - PIN VERIFICATION" + parts[1] + "**]")
                        else:
                            st.text(orchestration_val)
                elif var_name == "current_spec['tools']":
                    with st.expander(f"`{var_name}` (list, {len(var_value)} items)", expanded=False):
                        st.json(var_value)
                elif var_name == "spec_json":
                    with st.expander(f"`{var_name}` (str, truncated)", expanded=False):
                        st.code(var_value, language="json")
                else:
                    st.markdown(f"`{var_name}` = `{var_value}`")
        else:
            st.caption("No variables yet. Click Step 1 to begin.")

        # Execution log
        if st.session_state.py_log:
            st.divider()
            st.markdown("**Execution Log**")
            st.code("\n".join(st.session_state.py_log), language="python")


# ==============================================================================
# TAB 3: REST API
# ==============================================================================

with tab_rest:
    st.header("REST API Approach")
    st.markdown("""
    Use the Cortex Agents REST API for external applications, Postman, or
    any HTTP client. The endpoints:

    | Method | Endpoint | Purpose |
    |--------|----------|---------|
    | `GET` | `/api/v2/databases/{db}/schemas/{schema}/agents/{name}` | Describe |
    | `PUT` | `/api/v2/databases/{db}/schemas/{schema}/agents/{name}` | Update |
    | `POST` | `/api/v2/databases/{db}/schemas/{schema}/agents/{name}:run` | Run |
    """)

    # GET example
    st.subheader("GET - Describe Agent")
    curl_get = f"""curl -X GET \\
  "https://<account>.snowflakecomputing.com/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}" \\
  -H 'Authorization: Snowflake Token="<token>"' \\
  -H "Content-Type: application/json"
"""
    st.code(curl_get, language="bash")

    if st.button("Run: GET Agent (REST)", key="rest_get"):
        with st.spinner("Calling REST API..."):
            try:
                headers, account_url = get_rest_headers()
                url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"
                resp = requests.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                spec = json.loads(data["agent_spec"])
                st.success(f"GET returned {resp.status_code}")
                st.json(spec)
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # PUT example
    st.subheader("PUT - Update Agent (full spec replacement)")
    curl_put = f"""curl -X PUT \\
  "https://<account>.snowflakecomputing.com/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}" \\
  -H 'Authorization: Snowflake Token="<token>"' \\
  -H "Content-Type: application/json" \\
  -d '<FULL_SPEC_JSON>'
"""
    st.code(curl_put, language="bash")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("PUT: Reset to Baseline", key="rest_reset"):
            with st.spinner("PUT reset..."):
                try:
                    headers, account_url = get_rest_headers()
                    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"

                    # GET current
                    resp = requests.get(url, headers=headers)
                    resp.raise_for_status()
                    spec = json.loads(resp.json()["agent_spec"])

                    # Modify
                    spec["instructions"]["orchestration"] = BASELINE_ORCHESTRATION

                    # PUT back
                    resp = requests.put(url, headers=headers, json=spec)
                    resp.raise_for_status()
                    st.success(f"PUT returned {resp.status_code} - Reset complete!")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("PUT: Add PIN Requirement", key="rest_add_pin"):
            with st.spinner("GET -> modify -> PUT..."):
                try:
                    headers, account_url = get_rest_headers()
                    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"

                    # GET
                    resp = requests.get(url, headers=headers)
                    resp.raise_for_status()
                    spec = json.loads(resp.json()["agent_spec"])
                    st.write(f"**GET** returned spec with {len(spec.get('tools',[]))} tools")

                    # Modify
                    existing = spec["instructions"]["orchestration"]
                    if "PIN VERIFICATION" not in existing:
                        spec["instructions"]["orchestration"] = existing + PIN_INSTRUCTION
                        st.write("**Modified** orchestration (appended PIN)")

                        # PUT
                        resp = requests.put(url, headers=headers, json=spec)
                        resp.raise_for_status()
                        st.success(f"**PUT** returned {resp.status_code} - PIN added!")
                        st.cache_resource.clear()
                    else:
                        st.info("PIN already present.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ==============================================================================
# TAB 4: Test Agent
# ==============================================================================

with tab_test:
    st.header("Test the Agent")
    st.markdown("""
    Send messages to the agent to verify the PIN behavior works correctly.
    - **Self-lookup** (e.g., "What is my access level?") should trigger PIN requirement
    - **Other-user lookup** (e.g., "Find Alice Johnson") should NOT require PIN
    """)

    # Quick test buttons
    st.subheader("Quick Tests")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Self-lookup (should ask for PIN)**")
        if st.button("Ask: 'What is my access level?'", key="test_self"):
            with st.spinner("Running agent..."):
                try:
                    headers, account_url = get_rest_headers()
                    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}:run"
                    headers["Accept"] = "application/json"
                    body = {
                        "messages": [{"role": "user", "content": [{"type": "text", "text": "What is my access level?"}]}],
                        "stream": False,
                    }
                    resp = requests.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("content", []):
                        if item.get("type") == "text":
                            text = item["text"]
                            st.markdown(f"> {text}")
                            if "pin" in text.lower():
                                st.success("Agent correctly asked for PIN!")
                            else:
                                st.warning("Agent did not ask for PIN (may vary by run)")
                            break
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.markdown("**Other-user lookup (should NOT ask for PIN)**")
        if st.button("Ask: 'Find Alice Johnson'", key="test_other"):
            with st.spinner("Running agent..."):
                try:
                    headers, account_url = get_rest_headers()
                    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}:run"
                    headers["Accept"] = "application/json"
                    body = {
                        "messages": [{"role": "user", "content": [{"type": "text", "text": "Find Alice Johnson"}]}],
                        "stream": False,
                    }
                    resp = requests.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    for item in data.get("content", []):
                        if item.get("type") == "text":
                            text = item["text"]
                            st.markdown(f"> {text}")
                            if "pin" not in text.lower():
                                st.success("Agent correctly did NOT ask for PIN!")
                            break
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # Custom question
    st.subheader("Custom Question")
    user_question = st.text_input("Ask the agent anything:", placeholder="e.g., Who is in Engineering?")
    if st.button("Send", key="test_custom") and user_question:
        with st.spinner("Running agent..."):
            try:
                headers, account_url = get_rest_headers()
                url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}:run"
                headers["Accept"] = "application/json"
                body = {
                    "messages": [{"role": "user", "content": [{"type": "text", "text": user_question}]}],
                    "stream": False,
                }
                resp = requests.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("content", []):
                    if item.get("type") == "text":
                        st.markdown(f"> {item['text']}")
                        break
                with st.expander("Full Response"):
                    st.json(data)
            except Exception as e:
                st.error(f"Error: {e}")
