export function MonitoringTab() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Monitoring and Logging</h2>

      <div className="space-y-4">
        <div>
          <h3 className="font-medium mb-2">Check Service Status</h3>
          <pre className="bg-muted p-3 rounded text-xs font-mono overflow-x-auto">
{`SELECT SYSTEM$GET_SERVICE_STATUS('plant_dashboard_service');`}
          </pre>
        </div>

        <div>
          <h3 className="font-medium mb-2">View Container Logs</h3>
          <pre className="bg-muted p-3 rounded text-xs font-mono overflow-x-auto">
{`CALL SYSTEM$GET_SERVICE_LOGS(
  'plant_dashboard_service',  -- service name
  '0',                        -- instance index
  'streamlit',                -- container name
  50                          -- last N lines
);`}
          </pre>
        </div>

        <div>
          <h3 className="font-medium mb-2">Query Event Table for Errors</h3>
          <pre className="bg-muted p-3 rounded text-xs font-mono overflow-x-auto">
{`SELECT TIMESTAMP, RECORD['severity_text'] AS severity,
       VALUE AS message
FROM my_event_table
WHERE RESOURCE_ATTRIBUTES['snow.service.name'] = 'PLANT_DASHBOARD_SERVICE'
  AND RECORD['severity_text'] IN ('ERROR', 'WARN')
ORDER BY TIMESTAMP DESC
LIMIT 20;`}
          </pre>
        </div>

        <div>
          <h3 className="font-medium mb-2">SPCS Billing Check</h3>
          <pre className="bg-muted p-3 rounded text-xs font-mono overflow-x-auto">
{`SELECT START_TIME, END_TIME, CREDITS_USED, SERVICE_TYPE
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE SERVICE_TYPE = 'SNOWPARK_CONTAINER_SERVICES'
ORDER BY START_TIME DESC
LIMIT 20;`}
          </pre>
        </div>
      </div>

      <div className="border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 p-4 rounded">
        <h4 className="font-medium text-yellow-800 dark:text-yellow-400 mb-2">Best Practices</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>Set up an Event Table early — it is your primary observability channel</li>
          <li>Use structured JSON logging (import logging with JSON formatter)</li>
          <li>Monitor restart counts — frequent restarts indicate OOM or crashes</li>
          <li>Set resource limits slightly above requests for burst headroom</li>
          <li>Use DESCRIBE SERVICE to check current health and endpoint status</li>
        </ul>
      </div>
    </div>
  )
}
