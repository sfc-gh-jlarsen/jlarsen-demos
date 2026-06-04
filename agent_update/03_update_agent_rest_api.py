"""
=============================================================================
  Cortex Agent - REST API Examples (curl-equivalent in Python requests)
=============================================================================

  This file shows the REST API approach using Python's `requests` library,
  structured as curl-equivalent examples that are easy to translate to any
  language or tool (Postman, etc.).

  API Endpoints:
    GET  /api/v2/databases/{db}/schemas/{schema}/agents/{name}   -> Describe
    PUT  /api/v2/databases/{db}/schemas/{schema}/agents/{name}   -> Update
    POST /api/v2/databases/{db}/schemas/{schema}/agents/{name}:run -> Run

  Authentication:
    - Key-pair auth (recommended for automation)
    - OAuth token
    - Session token from connector (shown here for demo)
=============================================================================
"""

import json
import requests
import snowflake.connector


# -- Configuration --
CONNECTION_NAME = "default"  # From ~/.snowflake/connections.toml
DATABASE = "USER_LOOKUP_DEMO"
SCHEMA = "AGENT_UPDATE_DEMO"
AGENT_NAME = "USER_LOOKUP_AGENT"


def get_connection_and_headers():
    """Connect and return (conn, headers, account_url)."""
    conn = snowflake.connector.connect(connection_name=CONNECTION_NAME)
    token = conn.rest.token
    account_url = f"https://{conn.account}.snowflakecomputing.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Snowflake Token="{token}"',
    }
    return conn, headers, account_url


# ==============================================================================
# 1. DESCRIBE AGENT (GET)
# ==============================================================================
# curl equivalent:
#   curl -X GET \
#     "https://<account>.snowflakecomputing.com/api/v2/databases/USER_LOOKUP_DEMO/schemas/AGENT_UPDATE_DEMO/agents/USER_LOOKUP_AGENT" \
#     -H "Authorization: Snowflake Token=\"<token>\"" \
#     -H "Content-Type: application/json"

def describe_agent(headers, account_url) -> dict:
    """GET the current agent configuration."""
    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


# ==============================================================================
# 2. UPDATE AGENT (PUT) - Full spec replacement
# ==============================================================================
# curl equivalent:
#   curl -X PUT \
#     "https://<account>.snowflakecomputing.com/api/v2/databases/USER_LOOKUP_DEMO/schemas/AGENT_UPDATE_DEMO/agents/USER_LOOKUP_AGENT" \
#     -H "Authorization: Snowflake Token=\"<token>\"" \
#     -H "Content-Type: application/json" \
#     -d '{
#       "models": {"orchestration": "auto"},
#       "instructions": {
#         "orchestration": "You are a user directory assistant...\n\nIMPORTANT - PIN VERIFICATION...",
#         "response": "Be concise. Format results in a clear, readable manner."
#       },
#       "tools": [...],
#       "tool_resources": {...}
#     }'

def update_agent(headers, account_url, updated_spec: dict):
    """PUT the full updated agent spec."""
    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"
    resp = requests.put(url, headers=headers, json=updated_spec)
    resp.raise_for_status()
    return resp.status_code


# ==============================================================================
# 3. RUN AGENT (POST :run) - Test the agent after update
# ==============================================================================
# curl equivalent:
#   curl -X POST \
#     "https://<account>.snowflakecomputing.com/api/v2/databases/USER_LOOKUP_DEMO/schemas/AGENT_UPDATE_DEMO/agents/USER_LOOKUP_AGENT:run" \
#     -H "Authorization: Snowflake Token=\"<token>\"" \
#     -H "Content-Type: application/json" \
#     -H "Accept: application/json" \
#     -d '{
#       "messages": [{"role": "user", "content": [{"type": "text", "text": "What is my access level?"}]}],
#       "stream": false
#     }'

def run_agent(headers, account_url, question: str) -> dict:
    """Run the agent with a question (non-streaming)."""
    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}:run"
    headers_with_accept = {**headers, "Accept": "application/json"}

    body = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}]
            }
        ],
        "stream": False
    }

    resp = requests.post(url, headers=headers_with_accept, json=body)
    resp.raise_for_status()
    return resp.json()


# ==============================================================================
# FULL WORKFLOW: Read -> Modify -> Write -> Verify
# ==============================================================================

def full_update_workflow():
    """
    Complete workflow demonstrating the safe update pattern via REST API.
    """
    print("=" * 70)
    print("  REST API: Safe Agent Instruction Update Workflow")
    print("=" * 70)

    conn, headers, account_url = get_connection_and_headers()

    try:
        # STEP 1: GET current spec
        print("\n--- STEP 1: GET current agent spec ---")
        agent_data = describe_agent(headers, account_url)
        current_spec = json.loads(agent_data["agent_spec"])
        print(f"Agent: {agent_data['name']}")
        print(f"Spec keys: {list(current_spec.keys())}")
        print(f"Current orchestration (first 100 chars):")
        print(f"  {current_spec['instructions']['orchestration'][:100]}...")

        # STEP 2: Modify the spec in memory
        print("\n--- STEP 2: Modify orchestration instructions ---")
        existing = current_spec["instructions"]["orchestration"]

        pin_requirement = '\n\nIMPORTANT - PIN VERIFICATION REQUIREMENT:\nWhen a user asks about their OWN information (e.g., "what is my access level", "show my profile", "what groups am I in"), you MUST ask them to provide their 4-digit PIN before revealing any personal information. Do NOT proceed without PIN verification for self-lookup requests.\n\nFor lookups about OTHER users (e.g., "find Alice Johnson", "who is in Engineering"), no PIN is required.'

        if "PIN VERIFICATION" not in existing:
            current_spec["instructions"]["orchestration"] = existing + pin_requirement
            print("  Added PIN verification requirement.")
        else:
            print("  PIN requirement already present - no changes needed.")

        # STEP 3: PUT the full spec back
        print("\n--- STEP 3: PUT updated spec ---")
        status = update_agent(headers, account_url, current_spec)
        print(f"  PUT returned: {status} (Success)")

        # STEP 4: Test with the agent
        print("\n--- STEP 4: Test - Self-lookup (should trigger PIN) ---")
        response = run_agent(headers, account_url, "What is my access level?")
        for item in response.get("content", []):
            if item.get("type") == "text":
                print(f"  Agent: {item.get('text', '')[:400]}")
                break

        print("\n--- STEP 5: Test - Other-user lookup (should NOT require PIN) ---")
        response = run_agent(headers, account_url, "Find Alice Johnson")
        for item in response.get("content", []):
            if item.get("type") == "text":
                print(f"  Agent: {item.get('text', '')[:400]}")
                break

    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("  DONE - Agent updated and verified via REST API")
    print("=" * 70)


if __name__ == "__main__":
    full_update_workflow()
