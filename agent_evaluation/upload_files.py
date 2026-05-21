import os
import snowflake.connector

conn = snowflake.connector.connect(
    connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "default")
)
cur = conn.cursor()

warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

cur.execute("USE ROLE SUPPLY_CHAIN_EVAL_ROLE")
cur.execute("USE SCHEMA AGENT_EVALUATION_DEMO.SUPPLY_CHAIN")
cur.execute(f"USE WAREHOUSE {warehouse}")

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

files = [
    "SALES_ORDERS.csv",
    "ORDER_LINE_ITEMS.csv",
    "ORDER_FULFILLMENT.csv",
    "ORDER_NOTES.csv",
    "EVALS_TABLE.csv",
]

for f in files:
    path = os.path.join(data_dir, f)
    print(f"Uploading {f}...")
    cur.execute(f"PUT file://{path} @DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    print(f"  Done: {cur.fetchall()}")

cur.execute("LS @DATA_STAGE")
for row in cur.fetchall():
    print(f"  {row[0]}  ({row[1]} bytes)")

yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supply_chain_eval_config.yaml")
print(f"\nUploading eval config YAML...")
cur.execute("CREATE OR REPLACE STAGE EVAL_CONFIG_STAGE DIRECTORY = (ENABLE = TRUE) COMMENT = 'Eval config stage'")
cur.execute(f"PUT file://{yaml_path} @EVAL_CONFIG_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
print(f"  Done: {cur.fetchall()}")

cur.execute("LS @EVAL_CONFIG_STAGE")
for row in cur.fetchall():
    print(f"  {row[0]}  ({row[1]} bytes)")

cur.close()
conn.close()
print("\nAll files uploaded successfully.")
