"""
Demo 4: SPCS Operations Guide
==============================
Multi-tab reference app addressing IT/Ops concerns about running Streamlit at scale.
Covers architecture, scaling, monitoring, external access, and runtime comparison.

Runtime: Container (Workspace or Deployed)
Persona: IT / Platform team
"""

import streamlit as st

st.set_page_config(page_title="SPCS Operations Guide", layout="wide")
st.title("SPCS Operations Guide — Running Streamlit at Scale")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Architecture",
    "Scaling & Warm Pools",
    "Monitoring & Logging",
    "External Access (EAI)",
    "Container vs Warehouse",
])

# ========== Tab 1: Architecture ==========
with tab1:
    st.subheader("SPCS Architecture")
    st.code("""
┌─────────────────────────────────────────────────────────────┐
│                     COMPUTE POOL                            │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│  │  Node 1  │   │  Node 2  │   │  Node 3  │  (auto-scale)│
│  │          │   │          │   │          │              │
│  │ ┌──────┐ │   │ ┌──────┐ │   │ ┌──────┐ │              │
│  │ │ Inst │ │   │ │ Inst │ │   │ │ Inst │ │              │
│  │ │  1   │ │   │ │  2   │ │   │ │  3   │ │              │
│  │ └──────┘ │   │ └──────┘ │   │ └──────┘ │              │
│  └──────────┘   └──────────┘   └──────────┘              │
│         │              │              │                     │
│         └──────────────┼──────────────┘                     │
│                        ▼                                    │
│              ┌─────────────────┐                           │
│              │  Load Balancer  │                           │
│              │  (Snowflake-    │                           │
│              │   managed)      │                           │
│              └────────┬────────┘                           │
│                       ▼                                    │
│              End Users (via Snowsight or URL)              │
└─────────────────────────────────────────────────────────────┘
    """, language=None)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("""
        **Compute Pool**
        Your VM fleet — like an auto-scaling group.
        Choose instance family for CPU/memory sizing.
        """)
    with col2:
        st.info("""
        **Nodes**
        Individual VMs within the pool.
        MIN/MAX_NODES controls fleet size.
        """)
    with col3:
        st.info("""
        **Service Instances**
        Replicas of your container (horizontal scale).
        MIN/MAX_INSTANCES per service.
        """)

    st.subheader("Instance Family Reference")
    st.dataframe(
        {
            "Family": ["CPU_X64_XS", "CPU_X64_S", "CPU_X64_M", "CPU_X64_L"],
            "vCPUs": [1, 3, 6, 12],
            "Memory (GB)": [6, 13, 28, 56],
            "Credits/hr": ["~0.5", "~1.0", "~2.0", "~4.0"],
            "Best For": [
                "Dev/test, simple apps",
                "Standard dashboards",
                "Data processing apps",
                "ML inference",
            ],
        },
        use_container_width=True,
        hide_index=True,
    )

# ========== Tab 2: Scaling & Warm Pools ==========
with tab2:
    st.subheader("Compute Pool Configuration")
    st.code("""
CREATE COMPUTE POOL plant_dashboard_pool
  MIN_NODES = 1          -- Always warm (eliminates cold start)
  MAX_NODES = 3          -- Scale out for peak load
  INSTANCE_FAMILY = CPU_X64_S
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 3600;  -- Suspend after 1hr idle

CREATE SERVICE plant_dashboard_service
  IN COMPUTE POOL plant_dashboard_pool
  MIN_INSTANCES = 1      -- Always have 1 replica ready
  MAX_INSTANCES = 5;     -- Scale replicas for concurrent users
    """, language="sql")

    col1, col2 = st.columns(2)
    with col1:
        st.success("**Warm Pools** (GA Feb 2025) — Pre-provisioned nodes eliminate cold start latency.")
    with col2:
        st.success("**Auto-Scaling Policies** (GA May 2026) — Configurable MIN/MAX with automatic scale-out.")

    st.divider()
    st.subheader("Cost Estimator")

    c1, c2, c3 = st.columns(3)
    with c1:
        family = st.selectbox("Instance Family", ["CPU_X64_XS", "CPU_X64_S", "CPU_X64_M", "CPU_X64_L"])
    with c2:
        nodes = st.slider("Nodes", 1, 5, 1)
    with c3:
        hours_per_day = st.slider("Hours/day active", 1, 24, 10)

    credit_rates = {"CPU_X64_XS": 0.5, "CPU_X64_S": 1.0, "CPU_X64_M": 2.0, "CPU_X64_L": 4.0}
    rate = credit_rates[family]
    daily_credits = rate * nodes * hours_per_day
    monthly_credits = daily_credits * 22  # business days

    st.metric("Estimated Monthly Credits", f"{monthly_credits:,.0f}")
    st.caption(f"Based on {hours_per_day}hr/day × {nodes} node(s) × {rate} credits/hr × 22 business days")

# ========== Tab 3: Monitoring & Logging ==========
with tab3:
    st.subheader("Essential Monitoring Queries")

    st.markdown("**Check Service Status**")
    st.code("""
SELECT SYSTEM$GET_SERVICE_STATUS('plant_dashboard_service');
    """, language="sql")

    st.markdown("**View Container Logs**")
    st.code("""
CALL SYSTEM$GET_SERVICE_LOGS(
  'plant_dashboard_service',  -- service name
  '0',                        -- instance index
  'streamlit',                -- container name
  50                          -- last N lines
);
    """, language="sql")

    st.markdown("**Query Event Table for Errors**")
    st.code("""
SELECT TIMESTAMP, RECORD['severity_text'] AS severity,
       VALUE AS message
FROM my_event_table
WHERE RESOURCE_ATTRIBUTES['snow.service.name'] = 'PLANT_DASHBOARD_SERVICE'
  AND RECORD['severity_text'] IN ('ERROR', 'WARN')
ORDER BY TIMESTAMP DESC
LIMIT 20;
    """, language="sql")

    st.markdown("**SPCS Billing Check**")
    st.code("""
SELECT START_TIME, END_TIME, CREDITS_USED, SERVICE_TYPE
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE SERVICE_TYPE = 'SNOWPARK_CONTAINER_SERVICES'
ORDER BY START_TIME DESC
LIMIT 20;
    """, language="sql")

    st.divider()
    st.subheader("Best Practices")
    st.warning("""
    - Set up an Event Table early — it's your primary observability channel
    - Use structured JSON logging (`import logging` with JSON formatter)
    - Monitor restart counts — frequent restarts indicate OOM or crashes
    - Set resource limits slightly above requests for burst headroom
    - Use `DESCRIBE SERVICE` to check current health and endpoint status
    """)

# ========== Tab 4: External Access (EAI) ==========
with tab4:
    st.subheader("When You Need External Access")
    st.markdown("""
    By default, SPCS containers have **NO outbound internet access**. This is a security feature.

    You need an External Access Integration (EAI) when your app:
    - Calls external APIs (weather data, LLM endpoints, etc.)
    - Loads JavaScript/CSS from CDNs
    - Sends email notifications
    - Connects to external databases
    """)

    st.subheader("Setup Pattern")
    st.code("""
-- Step 1: Network rule (what can be reached)
CREATE OR REPLACE NETWORK RULE api_access_rule
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('api.example.com:443', 'cdn.jsdelivr.net:443');

-- Step 2: Secret (if authentication needed)
CREATE OR REPLACE SECRET api_key
  TYPE = GENERIC_STRING
  SECRET_STRING = 'your-api-key-here';

-- Step 3: External Access Integration (ties it together)
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION api_access_eai
  ALLOWED_NETWORK_RULES = (api_access_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (api_key)
  ENABLED = TRUE;

-- Step 4: Reference in your service spec
-- spec.yaml → containers.env: SECRET_API_KEY from secret api_key
-- service creation: EXTERNAL_ACCESS_INTEGRATIONS = (api_access_eai)
    """, language="sql")

    st.divider()
    st.error("""
    **Common Gotcha:** If your Streamlit app uses custom components that load JS from a CDN,
    you must add that CDN domain to your network rule. Otherwise you'll get silent failures
    in the browser with no server-side errors.
    """)

# ========== Tab 5: Container vs Warehouse Runtime ==========
with tab5:
    st.subheader("Runtime Comparison")
    st.dataframe(
        {
            "Aspect": [
                "Cold start",
                "Python packages",
                "Cost model",
                "GPU support",
                "Outbound networking",
                "Caller's Rights",
                "Max memory",
                "Concurrent users",
            ],
            "Warehouse Runtime": [
                "Seconds",
                "Anaconda channel only",
                "Per-second (warehouse credits)",
                "No",
                "No outbound",
                "No (READ SESSION workaround)",
                "Limited by warehouse",
                "1 per warehouse",
            ],
            "Container Runtime (SPCS)": [
                "Minutes (use warm pools!)",
                "Anything (Docker/pip)",
                "Per-node-hour",
                "Yes (GPU instance families)",
                "EAI for outbound",
                "Yes (GA Jun 2026)",
                "Up to 56 GB (CPU_X64_L)",
                "Auto-scaled horizontally",
            ],
        },
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.info("""
    **Active migration (Q2 FY27):** Warehouse-runtime SiS apps are being migrated to container runtime.
    All new apps should target container runtime.
    """)

    st.subheader("Recommendation")
    st.success("""
    **Start with container runtime for all new apps.**

    - Use `CPU_X64_XS` for dev/test, `CPU_X64_S` for production dashboards
    - Set MIN_NODES=1 with warm pool for instant access
    - Auto-suspend after business hours to control costs
    - Warehouse runtime remains viable for simple, single-user apps during transition
    """)
