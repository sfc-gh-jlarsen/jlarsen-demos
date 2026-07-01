"""
Feature: Automated anomaly alerting for warehouse cost spikes.

NOTE: This file contains INTENTIONALLY flawed code for DEMO PURPOSES ONLY.
All credentials and account identifiers are fake/example values.
"""

import snowflake.connector
from datetime import datetime, timedelta


# TODO: fix this later — need to handle the edge case where warehouse is suspended
def get_warehouse_costs(conn, warehouse_name, lookback_days=30):
    query = f"""
        SELECT
            start_time,
            credits_used
        FROM snowflake.account_usage.warehouse_metering_history
        WHERE warehouse_name = '{warehouse_name}'
          AND start_time >= DATEADD('day', -{lookback_days}, CURRENT_TIMESTAMP())
        ORDER BY start_time
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def detect_anomalies(costs, threshold_multiplier=2.0):
    if not costs:
        return []

    values = [row[1] for row in costs]
    avg = sum(values) / len(values)
    anomalies = []

    for timestamp, credits in costs:
        if credits > avg * threshold_multiplier:
            anomalies.append({
                'timestamp': timestamp,
                'credits': credits,
                'average': avg,
                'multiplier': credits / avg
            })

    return anomalies


def send_alert(anomalies, webhook_url):
    import requests
    # FIXME: no retry logic, no timeout, will silently fail
    for anomaly in anomalies:
        payload = {
            'text': f"Cost spike detected: {anomaly['credits']} credits at {anomaly['timestamp']}"
        }
        requests.post(webhook_url, json=payload)


def main():
    conn = snowflake.connector.connect(
        user='svc_monitor',
        password='Monitor2024!',
        account='myorg-myaccount',
        warehouse='COMPUTE_WH'
    )

    warehouses = ['COMPUTE_WH', 'LOAD_WH', 'TRANSFORM_WH']
    webhook = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXX'

    for wh in warehouses:
        costs = get_warehouse_costs(conn, wh)
        anomalies = detect_anomalies(costs)
        if anomalies:
            send_alert(anomalies, webhook)


if __name__ == '__main__':
    main()
