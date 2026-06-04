"""
=============================================================================
  Cortex Agent - Update Orchestration Instructions via Python
=============================================================================

  This script demonstrates how to programmatically update a Cortex Agent's
  orchestration instructions WITHOUT overwriting other fields.

  The key pattern:
    1. DESCRIBE AGENT to get the current spec (JSON string in agent_spec column)
    2. Parse the JSON, modify the field(s) you want
    3. ALTER AGENT with the FULL merged spec

  Two approaches shown:
    - Option A: Using snowflake-connector-python (SQL-based)
    - Option B: Using the REST API directly (HTTP PUT)

  IMPORTANT NOTE ON QUOTING:
    When using the Python connector, use $$ delimiters around the JSON spec.
    The single-quote approach ('...') requires escaping and can break with
    complex JSON containing quotes. $$ is cleanest.
=============================================================================
"""

import json
import snowflake.connector


# -- Configuration --
CONNECTION_NAME = "default"  # From ~/.snowflake/connections.toml
DATABASE = "USER_LOOKUP_DEMO"
SCHEMA = "AGENT_UPDATE_DEMO"
AGENT_NAME = "USER_LOOKUP_AGENT"
FQN = f"{DATABASE}.{SCHEMA}.{AGENT_NAME}"


# ==============================================================================
# OPTION A: Using snowflake-connector-python (recommended for most use cases)
# ==============================================================================

def update_agent_instructions_via_sql():
    """
    Pattern: DESCRIBE -> parse -> modify -> ALTER with full spec.
    This is the safest approach and avoids overwriting any fields.
    """

    # Connect using connections.toml
    conn = snowflake.connector.connect(connection_name=CONNECTION_NAME)
    cur = conn.cursor()

    try:
        # STEP 1: Get the current agent spec
        cur.execute(f"DESCRIBE AGENT {FQN}")
        row = cur.fetchone()

        # Find agent_spec column by name via cursor.description
        # (don't hardcode index - column positions can change across versions)
        col_names = [col[0].lower() for col in cur.description]
        spec_idx = col_names.index("agent_spec")
        current_spec = json.loads(row[spec_idx])

        print("=== CURRENT SPEC STRUCTURE ===")
        print(f"Top-level keys: {list(current_spec.keys())}")
        print(f"Instructions keys: {list(current_spec.get('instructions', {}).keys())}")
        print()
        print("=== CURRENT ORCHESTRATION INSTRUCTIONS ===")
        print(current_spec.get("instructions", {}).get("orchestration", ""))
        print()

        # STEP 2: Modify ONLY the orchestration instructions
        # Append the new PIN requirement to the existing instructions
        existing_orchestration = current_spec.get("instructions", {}).get("orchestration", "")

        new_pin_instruction = '\n\nIMPORTANT - PIN VERIFICATION REQUIREMENT:\nWhen a user asks about their OWN information (e.g., "what is my access level", "show my profile", "what groups am I in"), you MUST ask them to provide their 4-digit PIN before revealing any personal information. Do NOT proceed without PIN verification for self-lookup requests.\n\nFor lookups about OTHER users (e.g., "find Alice Johnson", "who is in Engineering"), no PIN is required.'

        # Only add if not already present
        if "PIN VERIFICATION" not in existing_orchestration:
            current_spec["instructions"]["orchestration"] = existing_orchestration + new_pin_instruction
        else:
            print("PIN requirement already present - skipping modification.")
            return

        # STEP 3: ALTER AGENT with the FULL updated spec
        # Use $$ delimiter - cleanest approach for JSON with embedded quotes
        spec_json = json.dumps(current_spec)
        alter_sql = f"ALTER AGENT {FQN} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$"

        print("=== APPLYING UPDATED SPEC ===")
        cur.execute(alter_sql)
        print("Agent updated successfully!")
        print()

        # STEP 4: Verify
        cur.execute(f"DESCRIBE AGENT {FQN}")
        row = cur.fetchone()
        col_names = [col[0].lower() for col in cur.description]
        spec_idx = col_names.index("agent_spec")
        updated_spec = json.loads(row[spec_idx])
        print("=== UPDATED ORCHESTRATION INSTRUCTIONS ===")
        print(updated_spec.get("instructions", {}).get("orchestration", ""))
        print()
        print("=== VERIFICATION ===")
        print(f"  PIN present: {'PIN VERIFICATION' in updated_spec['instructions']['orchestration']}")
        print(f"  Tools preserved: {len(updated_spec.get('tools', []))} tools")
        print(f"  Model preserved: {updated_spec.get('models', {}).get('orchestration', 'N/A')}")

    finally:
        cur.close()
        conn.close()


# ==============================================================================
# OPTION B: Using the REST API directly (for external apps, CI/CD pipelines)
# ==============================================================================

def update_agent_instructions_via_rest_api():
    """
    Pattern: GET agent -> modify spec -> PUT agent with full spec.
    Uses the Cortex Agents REST API.

    Endpoints:
      GET  /api/v2/databases/{db}/schemas/{schema}/agents/{name}   -> Describe
      PUT  /api/v2/databases/{db}/schemas/{schema}/agents/{name}   -> Update
    """
    import requests

    # Connect to get a session token for REST API auth
    conn = snowflake.connector.connect(connection_name=CONNECTION_NAME)

    # Get the REST session token from the connector
    token = conn.rest.token
    account_url = f"https://{conn.account}.snowflakecomputing.com"
    agent_url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Snowflake Token="{token}"',
    }

    # STEP 1: GET the current agent configuration
    print("=== STEP 1: GET current agent spec ===")
    resp = requests.get(agent_url, headers=headers)
    resp.raise_for_status()
    agent_data = resp.json()

    # The agent_spec is a JSON string in the response
    current_spec = json.loads(agent_data["agent_spec"])
    print(f"Current orchestration: {current_spec['instructions']['orchestration'][:80]}...")
    print()

    # STEP 2: Modify the orchestration instructions
    existing_orchestration = current_spec["instructions"]["orchestration"]
    new_pin_instruction = '\n\nIMPORTANT - PIN VERIFICATION REQUIREMENT:\nWhen a user asks about their OWN information (e.g., "what is my access level", "show my profile", "what groups am I in"), you MUST ask them to provide their 4-digit PIN before revealing any personal information. Do NOT proceed without PIN verification for self-lookup requests.\n\nFor lookups about OTHER users (e.g., "find Alice Johnson", "who is in Engineering"), no PIN is required.'

    if "PIN VERIFICATION" not in existing_orchestration:
        current_spec["instructions"]["orchestration"] = existing_orchestration + new_pin_instruction
    else:
        print("PIN already present - skipping.")
        conn.close()
        return

    # STEP 3: PUT the full updated spec back
    # NOTE: The PUT body IS the full spec (not wrapped in agent_spec key)
    print("=== STEP 3: PUT updated spec ===")
    resp = requests.put(agent_url, headers=headers, json=current_spec)
    resp.raise_for_status()
    print(f"PUT status: {resp.status_code} - Success!")
    print()

    # STEP 4: Verify
    print("=== STEP 4: Verify ===")
    resp = requests.get(agent_url, headers=headers)
    resp.raise_for_status()
    updated_data = resp.json()
    updated_spec = json.loads(updated_data["agent_spec"])
    print(f"PIN present: {'PIN VERIFICATION' in updated_spec['instructions']['orchestration']}")
    print(f"Tools preserved: {len(updated_spec.get('tools', []))}")

    conn.close()


# ==============================================================================
# HELPER: Generic reusable function for any agent update
# ==============================================================================

def safe_update_agent_instructions(
    connection_name: str,
    database: str,
    schema: str,
    agent_name: str,
    instruction_updates: dict,
    append: bool = False
):
    """
    Safely update agent instructions without overwriting other fields.

    Args:
        connection_name: Connection name from connections.toml
        database: Database name
        schema: Schema name
        agent_name: Agent name
        instruction_updates: Dict of instruction fields to update
            e.g., {"orchestration": "new instructions", "response": "new response"}
        append: If True, append to existing instructions. If False, replace.

    Example:
        safe_update_agent_instructions(
            "default", "MY_DB", "MY_SCHEMA", "MY_AGENT",
            {"orchestration": "\\nNew requirement: always ask for PIN."},
            append=True
        )
    """
    fqn = f"{database}.{schema}.{agent_name}"
    conn = snowflake.connector.connect(connection_name=connection_name)
    cur = conn.cursor()

    try:
        # Get current spec
        cur.execute(f"DESCRIBE AGENT {fqn}")
        row = cur.fetchone()
        col_names = [col[0].lower() for col in cur.description]
        spec_idx = col_names.index("agent_spec")
        current_spec = json.loads(row[spec_idx])

        # Ensure instructions dict exists
        if "instructions" not in current_spec:
            current_spec["instructions"] = {}

        # Apply updates
        for key, value in instruction_updates.items():
            if append and key in current_spec["instructions"]:
                current_spec["instructions"][key] += value
            else:
                current_spec["instructions"][key] = value

        # Apply the full spec using $$ quoting
        spec_json = json.dumps(current_spec)
        alter_sql = f"ALTER AGENT {fqn} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$"
        cur.execute(alter_sql)
        print(f"Agent {fqn} updated successfully.")
        return current_spec

    finally:
        cur.close()
        conn.close()


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  Cortex Agent - Update Instructions Demo")
    print("  Pattern: DESCRIBE -> Modify -> ALTER (full spec replacement)")
    print("=" * 70)
    print()

    # Run Option A (SQL-based, recommended)
    print("Running Option A: SQL-based update via snowflake-connector-python")
    print("-" * 70)
    update_agent_instructions_via_sql()

    # Uncomment to run Option B (REST API)
    # print("\nRunning Option B: REST API update")
    # print("-" * 70)
    # update_agent_instructions_via_rest_api()
