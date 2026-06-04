"""
=============================================================================
  Test Harness: Validate all agent update approaches
=============================================================================
  Reads config from .env (same as the Streamlit app).
  Run with:  uv run python test_all_approaches.py

  Tests:
    1. Verify spec structure (orchestration is under instructions)
    2. SQL approach: DESCRIBE -> modify -> ALTER via connector
    3. REST API approach: GET -> modify -> PUT
    4. Agent run: verify PIN behavior end-to-end
=============================================================================
"""

import json
import os
import sys

from dotenv import load_dotenv
import snowflake.connector
import requests

load_dotenv()

# -- Configuration from .env --
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
    '\n\nIMPORTANT - PIN VERIFICATION REQUIREMENT:\n'
    'When a user asks about their OWN information (e.g., "what is my access level", '
    '"show my profile", "what groups am I in"), you MUST ask them to provide their '
    '4-digit PIN before revealing any personal information. Do NOT proceed without '
    'PIN verification for self-lookup requests.\n\n'
    'For lookups about OTHER users (e.g., "find Alice Johnson", '
    '"who is in Engineering"), no PIN is required.'
)


# ==============================================================================
# Helpers
# ==============================================================================

def connect():
    """Connect using the configured connection from connections.toml."""
    return snowflake.connector.connect(connection_name=CONNECTION_NAME)


def get_spec_from_cursor(cur) -> dict:
    """Extract agent_spec from a DESCRIBE AGENT result using column name lookup."""
    row = cur.fetchone()
    col_names = [col[0].lower() for col in cur.description]
    spec_idx = col_names.index("agent_spec")
    return json.loads(row[spec_idx])


def get_rest_url(conn) -> str:
    """Get the correct REST API base URL using the account locator."""
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_ACCOUNT()")
    locator = cur.fetchone()[0]
    cur.close()
    return f"https://{locator.lower()}.snowflakecomputing.com"


def get_rest_headers(conn) -> dict:
    """Get REST API auth headers."""
    return {
        "Content-Type": "application/json",
        "Authorization": f'Snowflake Token="{conn.rest.token}"',
    }


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_pass(msg):
    print(f"  PASS: {msg}")


def print_fail(msg):
    print(f"  FAIL: {msg}")


# ==============================================================================
# TEST 1: Verify spec structure
# ==============================================================================
def test_1_verify_structure():
    print_section("TEST 1: Verify Agent Spec Structure")

    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(f"DESCRIBE AGENT {FQN}")
        spec = get_spec_from_cursor(cur)

        print(f"  Top-level keys: {list(spec.keys())}")
        print(f"  instructions keys: {list(spec.get('instructions', {}).keys())}")
        print()

        assert "instructions" in spec, "No 'instructions' key in spec!"
        assert "orchestration" in spec["instructions"], "'orchestration' not under 'instructions'!"
        assert "tools" in spec, "No 'tools' key in spec!"
        assert "tool_resources" in spec, "No 'tool_resources' key in spec!"

        print_pass("'orchestration' IS nested under 'instructions'")
        print_pass(f"Spec has {len(spec['tools'])} tool(s)")
        print_pass(f"Model: {spec.get('models', {}).get('orchestration', 'N/A')}")
        return True
    except AssertionError as e:
        print_fail(str(e))
        return False
    finally:
        cur.close()
        conn.close()


# ==============================================================================
# TEST 2: SQL-based update (DESCRIBE -> modify -> ALTER)
# ==============================================================================
def test_2_sql_update():
    print_section("TEST 2: SQL-Based Update (snowflake-connector-python)")

    conn = connect()
    cur = conn.cursor()
    try:
        # Step 1: Read
        print("  Step 1: DESCRIBE AGENT...")
        cur.execute(f"DESCRIBE AGENT {FQN}")
        current_spec = get_spec_from_cursor(cur)
        print(f"         orchestration[0:80] = \"{current_spec['instructions']['orchestration'][:80]}...\"")

        # Step 2: Reset to baseline
        print("  Step 2: Reset to baseline...")
        current_spec["instructions"]["orchestration"] = BASELINE_ORCHESTRATION
        spec_json = json.dumps(current_spec)
        cur.execute(f"ALTER AGENT {FQN} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$")
        print_pass("Reset")

        # Step 3: Re-read + append PIN
        print("  Step 3: Re-read and append PIN...")
        cur.execute(f"DESCRIBE AGENT {FQN}")
        current_spec = get_spec_from_cursor(cur)
        current_spec["instructions"]["orchestration"] += PIN_INSTRUCTION
        spec_json = json.dumps(current_spec)
        cur.execute(f"ALTER AGENT {FQN} MODIFY LIVE VERSION SET SPECIFICATION = $$ {spec_json} $$")
        print_pass("ALTER AGENT with PIN")

        # Step 4: Verify
        print("  Step 4: Verify...")
        cur.execute(f"DESCRIBE AGENT {FQN}")
        final_spec = get_spec_from_cursor(cur)

        checks = {
            "PIN in orchestration": "PIN VERIFICATION" in final_spec["instructions"]["orchestration"],
            "Tools preserved": len(final_spec.get("tools", [])) > 0,
            "Model preserved": "orchestration" in final_spec.get("models", {}),
            "Response preserved": "response" in final_spec.get("instructions", {}),
        }

        all_pass = True
        for check, result in checks.items():
            if result:
                print_pass(check)
            else:
                print_fail(check)
                all_pass = False

        assert all_pass, "Some checks failed!"
        return True

    except (AssertionError, Exception) as e:
        print_fail(str(e))
        return False
    finally:
        cur.close()
        conn.close()


# ==============================================================================
# TEST 3: REST API update (GET -> modify -> PUT)
# ==============================================================================
def test_3_rest_api_update():
    print_section("TEST 3: REST API Update (GET / PUT)")

    conn = connect()
    try:
        base_url = get_rest_url(conn)
        headers = get_rest_headers(conn)
        agent_url = f"{base_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}"

        # Step 1: GET
        print(f"  Step 1: GET {agent_url.split('.com')[1]}")
        resp = requests.get(agent_url, headers=headers)
        assert resp.status_code == 200, f"GET returned {resp.status_code}: {resp.text[:100]}"
        current_spec = json.loads(resp.json()["agent_spec"])
        print_pass(f"GET 200 - spec has {len(current_spec.get('tools', []))} tools")

        # Step 2: Reset via PUT
        print("  Step 2: PUT reset to baseline...")
        current_spec["instructions"]["orchestration"] = BASELINE_ORCHESTRATION
        resp = requests.put(agent_url, headers=headers, json=current_spec)
        assert resp.status_code == 200, f"PUT reset returned {resp.status_code}: {resp.text[:100]}"
        print_pass("PUT 200 - reset")

        # Step 3: GET + modify + PUT
        print("  Step 3: GET -> append PIN -> PUT...")
        resp = requests.get(agent_url, headers=headers)
        resp.raise_for_status()
        current_spec = json.loads(resp.json()["agent_spec"])
        current_spec["instructions"]["orchestration"] += PIN_INSTRUCTION
        resp = requests.put(agent_url, headers=headers, json=current_spec)
        assert resp.status_code == 200, f"PUT with PIN returned {resp.status_code}: {resp.text[:100]}"
        print_pass("PUT 200 - PIN added")

        # Step 4: Verify via GET
        print("  Step 4: Verify via GET...")
        resp = requests.get(agent_url, headers=headers)
        resp.raise_for_status()
        final_spec = json.loads(resp.json()["agent_spec"])

        assert "PIN VERIFICATION" in final_spec["instructions"]["orchestration"], "PIN not found!"
        assert len(final_spec.get("tools", [])) > 0, "Tools were lost!"
        print_pass("PIN present + tools preserved")
        return True

    except (AssertionError, Exception) as e:
        print_fail(str(e))
        return False
    finally:
        conn.close()


# ==============================================================================
# TEST 4: Agent run - verify PIN gating behavior
# ==============================================================================
def test_4_run_agent():
    print_section("TEST 4: Run Agent - Verify PIN Behavior")

    conn = connect()
    try:
        base_url = get_rest_url(conn)
        headers = get_rest_headers(conn)
        headers["Accept"] = "application/json"
        run_url = f"{base_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT_NAME}:run"

        all_pass = True

        # Test A: Self-lookup (should ask for PIN)
        print("  Test A: Self-lookup - 'What is my access level?'")
        body = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": "What is my access level?"}]}],
            "stream": False,
        }
        resp = requests.post(run_url, headers=headers, json=body)
        assert resp.status_code == 200, f"Agent run returned {resp.status_code}: {resp.text[:200]}"

        text = ""
        for item in resp.json().get("content", []):
            if item.get("type") == "text":
                text = item.get("text", "")
                break

        print(f"         Response: {text[:200]}")
        if "pin" in text.lower():
            print_pass("Agent asked for PIN on self-lookup")
        else:
            print_fail("Agent did NOT ask for PIN (non-deterministic, may retry)")
            all_pass = False

        # Test B: Other-user lookup (should NOT ask for PIN)
        print("\n  Test B: Other-user lookup - 'Find Alice Johnson'")
        body = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Find Alice Johnson"}]}],
            "stream": False,
        }
        resp = requests.post(run_url, headers=headers, json=body)
        assert resp.status_code == 200, f"Agent run returned {resp.status_code}: {resp.text[:200]}"

        text = ""
        for item in resp.json().get("content", []):
            if item.get("type") == "text":
                text = item.get("text", "")
                break

        print(f"         Response: {text[:200]}")
        # Check for PIN *verification request* (not just the word "pin" which appears in "UPIN")
        asks_for_pin = "4-digit" in text.lower() or "provide your pin" in text.lower() or "verify your" in text.lower()
        if not asks_for_pin:
            print_pass("Agent did NOT ask for PIN on other-user lookup")
        else:
            print_fail("Agent incorrectly asked for PIN on other-user lookup")
            all_pass = False

        return all_pass

    except (AssertionError, Exception) as e:
        print_fail(str(e))
        return False
    finally:
        conn.close()


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  Cortex Agent Update - Test Harness")
    print(f"  Connection: {CONNECTION_NAME}")
    print(f"  Agent:      {FQN}")
    print("=" * 70)

    results = {}
    results["1_structure"] = test_1_verify_structure()
    results["2_sql_update"] = test_2_sql_update()
    results["3_rest_api"] = test_3_rest_api_update()
    results["4_agent_run"] = test_4_run_agent()

    # Summary
    print_section("SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\n  {passed}/{total} tests passed", end="")
    if failed:
        print(f", {failed} failed")
        sys.exit(1)
    else:
        print()
        sys.exit(0)
