import csv
import random
import json
import os
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CUSTOMERS = [
    "Acme Industrial", "Globex Corporation", "Initech Systems", "Umbrella Logistics",
    "Stark Manufacturing", "Wayne Enterprises", "Cyberdyne Supply Co", "Oscorp Industries",
    "Weyland Distribution", "Soylent Goods", "Tyrell Freight", "Aperture Materials",
    "Massive Dynamic", "Hooli Inc", "Pied Piper Logistics", "Dunder Mifflin Supply",
    "Sterling Cooper Fulfillment", "Prestige Worldwide", "Vandelay Industries",
    "Bluth Company", "TechNova Solutions", "Pacific Rim Traders", "NorthStar Fabrication",
    "Cascade Components", "Summit Supply Group"
]

REGIONS = ["Northeast", "Southeast", "Midwest", "West", "International"]
STATUSES = ["completed", "shipped", "processing", "cancelled", "backordered"]
PRIORITIES = ["standard", "expedited", "rush"]
CHANNELS = ["web", "phone", "EDI", "marketplace"]
SALES_REPS = ["james.wilson", "maria.garcia", "chen.wei", "priya.patel", "alex.thompson"]

PRODUCTS = {
    "Electronics": [
        ("Industrial Sensor Module", 145.00), ("Control Board Assembly", 289.50),
        ("Power Supply Unit 500W", 112.00), ("LCD Display Panel 15in", 198.75),
        ("Cable Harness Kit", 45.50), ("Servo Motor Assembly", 325.00),
    ],
    "Industrial": [
        ("Hydraulic Pump HP-200", 875.00), ("Conveyor Belt Segment 10ft", 420.00),
        ("Steel Mounting Bracket Set", 67.50), ("Pneumatic Valve Assembly", 195.00),
        ("Industrial Filter Cartridge", 38.25), ("Safety Relay Module", 155.00),
    ],
    "Office Supplies": [
        ("Thermal Printer Paper 6pk", 24.99), ("Ergonomic Chair Model X", 449.00),
        ("Standing Desk Converter", 299.00), ("Filing Cabinet 4-Drawer", 189.50),
        ("Whiteboard 48x36", 79.00), ("Label Maker Pro", 64.50),
    ],
    "Raw Materials": [
        ("Aluminum Sheet 4x8 0.125in", 185.00), ("Copper Wire Spool 500ft", 312.00),
        ("ABS Plastic Pellets 50lb", 95.00), ("Stainless Steel Rod 1in 6ft", 78.50),
        ("Nylon Fastener Assortment", 42.00), ("Silicone Gasket Material", 56.75),
    ],
    "Packaging": [
        ("Corrugated Box 24x18x12 50pk", 89.00), ("Bubble Wrap Roll 250ft", 34.50),
        ("Pallet Stretch Wrap 4pk", 62.00), ("Custom Branded Tape 36 rolls", 48.75),
        ("Foam Insert Custom Cut", 15.50), ("Poly Mailer Bags 100pk", 29.99),
    ],
}

WAREHOUSES = ["Chicago-IL", "Dallas-TX", "Portland-OR", "Atlanta-GA", "Reno-NV"]
CARRIERS = ["FedEx", "UPS", "USPS", "DHL", "FreightLine"]

NOTE_TEMPLATES = {
    "issue": [
        "Shipment delayed due to {reason}. Customer notified. Expected resolution by {date}.",
        "Quality issue reported on {product}. {count} units affected. RMA initiated.",
        "Backorder on {product} from supplier. Lead time extended by {days} days.",
        "Carrier reported damaged package during transit via {carrier}. Replacement being processed.",
        "Customer complaint: {product} received does not match specifications. Investigating with warehouse {warehouse}.",
        "Inventory discrepancy found at {warehouse}. Physical count {count} vs system shows {count2}.",
        "Temperature-sensitive shipment delayed at {warehouse} due to equipment failure.",
        "Customs hold on international shipment. Missing documentation for {product}.",
    ],
    "resolution": [
        "Issue resolved. Replacement shipment sent via {carrier} with expedited delivery.",
        "Credit issued to customer for ${amount}. Quality investigation completed - root cause: {reason}.",
        "Backorder fulfilled. All {count} units shipped from {warehouse} on {date}.",
        "RMA processed successfully. Refurbished units returned to inventory.",
        "Customer accepted partial shipment. Remaining {count} units scheduled for {date}.",
        "Escalation closed. Vendor agreed to {count}% discount on next order as compensation.",
    ],
    "feedback": [
        "Customer praised fast turnaround on rush order. Shipped within {count} hours of placement.",
        "Positive feedback on packaging quality. Zero damage reported across {count} shipments this quarter.",
        "Customer requested recurring order schedule for {product}. Setting up auto-replenishment.",
        "Sales rep {rep} noted customer interest in volume discount program for Q{quarter} orders.",
        "Customer survey score: {score}/10. Comment: '{comment}'",
    ],
    "update": [
        "Order status changed from {status1} to {status2}. Warehouse {warehouse} confirmed pick completion.",
        "Shipping label generated. Tracking number {tracking} via {carrier}.",
        "Partial shipment dispatched: {count} of {total} line items. Remainder ships {date}.",
        "Priority upgraded from standard to {priority} per customer request. Additional fee: ${amount}.",
        "Delivery confirmed at customer dock. Signed by {person} at {time}.",
    ],
    "escalation": [
        "ESCALATED: Order {days} days past due. Customer threatening to switch vendors. Immediate attention required.",
        "ESCALATED: Third quality issue this quarter from {warehouse}. Pattern suggests systemic problem with {product} line.",
        "ESCALATED: High-value customer {customer} requesting executive review of fulfillment SLA violations.",
        "ESCALATED: Carrier {carrier} has lost shipment. Insurance claim filed. Value: ${amount}.",
        "ESCALATED: Critical supply shortage on {product}. {count} orders affected across {region} region.",
    ],
}

FEEDBACK_COMMENTS = [
    "Great service, always reliable", "Shipping was slower than expected",
    "Product quality is excellent", "Need better tracking updates",
    "Pricing is competitive", "Would like more flexible delivery windows",
    "Warehouse staff are very helpful", "Packaging could be improved",
]

DELAY_REASONS = [
    "severe weather in Midwest region", "port congestion at Long Beach",
    "supplier production delays", "carrier capacity constraints",
    "warehouse staffing shortage", "customs clearance delays",
    "quality inspection hold", "inventory allocation conflict",
]


def generate_sales_orders(n=50):
    orders = []
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    delta = (end - start).days

    for i in range(1, n + 1):
        order_date = start + timedelta(days=random.randint(0, delta))
        ship_offset = random.randint(1, 14)
        requested_ship = order_date + timedelta(days=ship_offset)

        status_weights = [0.45, 0.20, 0.15, 0.10, 0.10]
        status = random.choices(STATUSES, weights=status_weights, k=1)[0]

        orders.append({
            "order_id": i,
            "customer_name": random.choice(CUSTOMERS),
            "region": random.choice(REGIONS),
            "order_date": order_date.strftime("%Y-%m-%d"),
            "requested_ship_date": requested_ship.strftime("%Y-%m-%d"),
            "status": status,
            "priority": random.choices(PRIORITIES, weights=[0.5, 0.35, 0.15], k=1)[0],
            "channel": random.choice(CHANNELS),
            "sales_rep": random.choice(SALES_REPS),
        })
    return orders


def generate_line_items(orders, avg_per_order=4):
    items = []
    lid = 1
    for order in orders:
        n_items = random.randint(1, 7)
        for _ in range(n_items):
            category = random.choice(list(PRODUCTS.keys()))
            product_name, base_price = random.choice(PRODUCTS[category])
            qty = random.randint(1, 50)
            discount = random.choice([0, 0, 0, 5, 10, 15, 20])
            unit_price = round(base_price * random.uniform(0.9, 1.1), 2)
            total = round(qty * unit_price * (1 - discount / 100), 2)
            items.append({
                "line_item_id": lid,
                "order_id": order["order_id"],
                "product_name": product_name,
                "category": category,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_pct": discount,
                "total_amount": total,
            })
            lid += 1
    return items


def generate_fulfillment(orders):
    records = []
    fid = 1
    for order in orders:
        if order["status"] == "cancelled":
            continue
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
        req_ship = datetime.strptime(order["requested_ship_date"], "%Y-%m-%d")

        if order["status"] in ("completed", "shipped"):
            actual_days = random.randint(1, 10)
            ship_date = order_date + timedelta(days=actual_days)
            on_time = ship_date <= req_ship
        elif order["status"] == "backordered":
            actual_days = random.randint(10, 25)
            ship_date = order_date + timedelta(days=actual_days)
            on_time = False
        else:
            actual_days = random.randint(1, 5)
            ship_date = order_date + timedelta(days=actual_days)
            on_time = ship_date <= req_ship

        shipping_cost = round(random.uniform(15.0, 350.0), 2)
        if order["priority"] == "rush":
            shipping_cost = round(shipping_cost * 1.8, 2)
        elif order["priority"] == "expedited":
            shipping_cost = round(shipping_cost * 1.3, 2)

        records.append({
            "fulfillment_id": fid,
            "order_id": order["order_id"],
            "ship_date": ship_date.strftime("%Y-%m-%d"),
            "warehouse": random.choice(WAREHOUSES),
            "on_time": on_time,
            "days_to_ship": actual_days,
            "shipping_cost": shipping_cost,
            "carrier": random.choice(CARRIERS),
        })
        fid += 1
    return records


def _fill_template(template, orders, line_items):
    order = random.choice(orders)
    product = random.choice(line_items)["product_name"]
    replacements = {
        "{reason}": random.choice(DELAY_REASONS),
        "{date}": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))).strftime("%Y-%m-%d"),
        "{product}": product,
        "{count}": str(random.randint(2, 50)),
        "{count2}": str(random.randint(2, 50)),
        "{days}": str(random.randint(3, 21)),
        "{carrier}": random.choice(CARRIERS),
        "{warehouse}": random.choice(WAREHOUSES),
        "{amount}": str(round(random.uniform(50, 5000), 2)),
        "{rep}": random.choice(SALES_REPS),
        "{quarter}": str(random.randint(1, 4)),
        "{score}": str(random.randint(5, 10)),
        "{comment}": random.choice(FEEDBACK_COMMENTS),
        "{status1}": random.choice(STATUSES),
        "{status2}": random.choice(STATUSES),
        "{tracking}": f"1Z{random.randint(100000000, 999999999)}",
        "{total}": str(random.randint(3, 10)),
        "{priority}": random.choice(["expedited", "rush"]),
        "{person}": random.choice(["J. Smith", "R. Johnson", "M. Williams", "K. Brown"]),
        "{time}": f"{random.randint(8, 17)}:{random.randint(0, 59):02d}",
        "{customer}": order["customer_name"],
        "{region}": random.choice(REGIONS),
    }
    result = template
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def generate_order_notes(orders, line_items, n=75):
    notes = []
    note_types = list(NOTE_TEMPLATES.keys())
    type_weights = [0.25, 0.20, 0.20, 0.20, 0.15]

    for nid in range(1, n + 1):
        order = random.choice(orders)
        note_type = random.choices(note_types, weights=type_weights, k=1)[0]
        template = random.choice(NOTE_TEMPLATES[note_type])
        content = _fill_template(template, orders, line_items)
        notes.append({
            "note_id": nid,
            "order_id": order["order_id"],
            "note_type": note_type,
            "note_content": content,
        })
    return notes


def generate_evals_table():
    rows = [
        {
            "INPUT_QUERY": "What is the total revenue by region?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The query should return total revenue (sum of line item amounts) grouped by region. The agent should use the semantic view to aggregate total_amount across all orders by the region dimension."
            })
        },
        {
            "INPUT_QUERY": "Which warehouse has the best on-time delivery rate?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should query fulfillment data to calculate the on-time delivery percentage for each warehouse and identify the one with the highest rate. This is a quantitative question using structured fulfillment metrics."
            })
        },
        {
            "INPUT_QUERY": "What shipping delays or issues have been reported recently?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "The agent should search order notes for delay-related content including issues, escalations, and carrier problems. Results should include specific details about delays such as weather, customs, carrier issues, and affected orders."
            })
        },
        {
            "INPUT_QUERY": "Generate a report for order 5",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"},
                    {"tool_name": "generate_order_report"}
                ],
                "ground_truth_output": "The agent should first look up order 5 details using query_order_metrics to confirm the order exists, then call generate_order_report with order_id=5 to create a comprehensive HTML report. The response should mention the report was generated and provide key highlights."
            })
        },
        {
            "INPUT_QUERY": "What are the top 5 customers by total order value?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should query the semantic view to sum total_amount by customer_name, order descending, and limit to top 5. This is a pure quantitative ranking question."
            })
        },
        {
            "INPUT_QUERY": "What customer feedback have we received about packaging quality?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "The agent should search order notes for feedback related to packaging quality. Results should include positive and negative comments about packaging from customer feedback and issue notes."
            })
        },
        {
            "INPUT_QUERY": "How does FedEx compare to UPS in terms of shipping cost and delivery performance?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should query fulfillment data to compare FedEx and UPS on average shipping cost, on-time delivery rate, and average days to ship. This is a quantitative comparison between two carriers."
            })
        },
        {
            "INPUT_QUERY": "Are there any escalated issues that need immediate attention?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "The agent should search order notes for escalation-type entries. Results should surface urgent issues like overdue orders, repeated quality problems, high-value customer complaints, and lost shipments."
            })
        },
        {
            "INPUT_QUERY": "What is the average days to ship by priority level?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should calculate the average days_to_ship grouped by order priority (standard, expedited, rush). Rush orders should generally have fewer days to ship than standard orders."
            })
        },
        {
            "INPUT_QUERY": "Generate a comprehensive report for the order placed by Stark Manufacturing",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"},
                    {"tool_name": "generate_order_report"}
                ],
                "ground_truth_output": "The agent should first use query_order_metrics to find the order_id for Stark Manufacturing, then call generate_order_report with that order_id. The response should confirm the report was generated and provide key details from the order."
            })
        },
        {
            "INPUT_QUERY": "What quality issues have been reported with Electronics products?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "The agent should search order notes for quality-related issues mentioning electronics products. Results should include RMA details, specification mismatches, and resolution outcomes."
            })
        },
        {
            "INPUT_QUERY": "Show me monthly revenue trends for 2024",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should query the semantic view to aggregate total revenue by month across 2024 and present a time-series view of revenue trends. This is a temporal quantitative analysis."
            })
        },
        {
            "INPUT_QUERY": "What are the most common reasons for order delays and how have they been resolved?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "The agent should search order notes for both issue and resolution entries related to delays. The response should identify common delay reasons (weather, supplier delays, carrier issues) and summarize resolution patterns."
            })
        },
        {
            "INPUT_QUERY": "Which product category generates the most revenue and what is the breakdown by channel?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"}
                ],
                "ground_truth_output": "The agent should query total revenue by product category and channel using the semantic view. Results should show a cross-tabulation of category vs channel with revenue amounts."
            })
        },
        {
            "INPUT_QUERY": "What can you help me with?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [],
                "ground_truth_output": "The agent should describe its capabilities without making any tool calls. It can help with: querying order metrics and performance data (revenue, shipping, fulfillment), searching order notes for qualitative insights (issues, feedback, escalations), and generating comprehensive order reports."
            })
        },
        {
            "INPUT_QUERY": "What is the current stock price of Snowflake?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [],
                "ground_truth_output": "The agent should NOT make any tool calls. It should explain that it does not have access to stock market data. Its capabilities are limited to supply chain order analytics, order notes, and report generation."
            })
        },
        {
            "INPUT_QUERY": "What was the total number of orders by sales channel and what feedback do customers have about the web channel?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"},
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "This is a multi-tool question. The agent should first use query_order_metrics to get order counts by channel, then use search_order_notes to find feedback about the web ordering channel. The response should combine quantitative order counts with qualitative customer feedback."
            })
        },
        {
            "INPUT_QUERY": "How many backordered orders do we have and what are the specific issues causing them?",
            "GROUND_TRUTH_DATA": json.dumps({
                "ground_truth_invocations": [
                    {"tool_name": "query_order_metrics"},
                    {"tool_name": "search_order_notes"}
                ],
                "ground_truth_output": "Multi-tool question. The agent should query for count of orders with backordered status using query_order_metrics, then search order notes for backorder-related issues and delays. The response should combine the count with specific issue details."
            })
        },
    ]
    return rows


def write_csv(filepath, rows, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_evals_csv(filepath, rows):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["INPUT_QUERY", "GROUND_TRUTH_DATA"], quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("Generating supply chain data...")

    orders = generate_sales_orders(50)
    print(f"  SALES_ORDERS: {len(orders)} rows")
    write_csv(
        os.path.join(OUTPUT_DIR, "SALES_ORDERS.csv"),
        orders,
        ["order_id", "customer_name", "region", "order_date", "requested_ship_date", "status", "priority", "channel", "sales_rep"],
    )

    line_items = generate_line_items(orders)
    print(f"  ORDER_LINE_ITEMS: {len(line_items)} rows")
    write_csv(
        os.path.join(OUTPUT_DIR, "ORDER_LINE_ITEMS.csv"),
        line_items,
        ["line_item_id", "order_id", "product_name", "category", "quantity", "unit_price", "discount_pct", "total_amount"],
    )

    fulfillment = generate_fulfillment(orders)
    print(f"  ORDER_FULFILLMENT: {len(fulfillment)} rows")
    write_csv(
        os.path.join(OUTPUT_DIR, "ORDER_FULFILLMENT.csv"),
        fulfillment,
        ["fulfillment_id", "order_id", "ship_date", "warehouse", "on_time", "days_to_ship", "shipping_cost", "carrier"],
    )

    notes = generate_order_notes(orders, line_items, 75)
    print(f"  ORDER_NOTES: {len(notes)} rows")
    write_csv(
        os.path.join(OUTPUT_DIR, "ORDER_NOTES.csv"),
        notes,
        ["note_id", "order_id", "note_type", "note_content"],
    )

    evals = generate_evals_table()
    print(f"  EVALS_TABLE: {len(evals)} rows")
    write_evals_csv(os.path.join(OUTPUT_DIR, "EVALS_TABLE.csv"), evals)

    print(f"\nAll CSVs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
