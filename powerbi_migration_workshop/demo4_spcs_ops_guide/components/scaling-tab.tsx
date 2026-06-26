export function ScalingTab() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Scaling and Warm Pools</h2>

      <div className="bg-muted rounded-lg p-4">
        <h3 className="font-medium mb-2">Recommended Compute Pool Configuration</h3>
        <pre className="text-xs font-mono overflow-x-auto">
{`CREATE COMPUTE POOL plant_dashboard_pool
  MIN_NODES = 1          -- Always warm (eliminates cold start)
  MAX_NODES = 3          -- Scale out for peak load
  INSTANCE_FAMILY = CPU_X64_S
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 3600;  -- Suspend after 1hr idle

CREATE SERVICE plant_dashboard_service
  IN COMPUTE POOL plant_dashboard_pool
  MIN_INSTANCES = 1      -- Always have 1 replica ready
  MAX_INSTANCES = 5;     -- Scale replicas for concurrent users`}
        </pre>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded-lg p-4 border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800">
          <h4 className="font-medium text-green-700 dark:text-green-400">Warm Pools (GA Feb 2025)</h4>
          <p className="text-sm text-muted-foreground mt-1">
            Pre-provisioned nodes eliminate cold start latency. Set MIN_NODES=1 so at least one node is always ready.
          </p>
        </div>
        <div className="border rounded-lg p-4 border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800">
          <h4 className="font-medium text-green-700 dark:text-green-400">Auto-Scaling (GA May 2026)</h4>
          <p className="text-sm text-muted-foreground mt-1">
            Configurable MIN/MAX with automatic scale-out based on load. Handles variable concurrent users.
          </p>
        </div>
      </div>

      <h3 className="text-lg font-medium">Scaling Strategy</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border">
          <thead className="bg-muted">
            <tr>
              <th className="p-2 text-left">Parameter</th>
              <th className="p-2 text-left">Dev/Test</th>
              <th className="p-2 text-left">Production</th>
              <th className="p-2 text-left">High Traffic</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t"><td className="p-2">Instance Family</td><td className="p-2">CPU_X64_XS</td><td className="p-2">CPU_X64_S</td><td className="p-2">CPU_X64_M</td></tr>
            <tr className="border-t"><td className="p-2">MIN_NODES</td><td className="p-2">0</td><td className="p-2">1</td><td className="p-2">2</td></tr>
            <tr className="border-t"><td className="p-2">MAX_NODES</td><td className="p-2">1</td><td className="p-2">3</td><td className="p-2">5</td></tr>
            <tr className="border-t"><td className="p-2">MIN_INSTANCES</td><td className="p-2">1</td><td className="p-2">1</td><td className="p-2">2</td></tr>
            <tr className="border-t"><td className="p-2">MAX_INSTANCES</td><td className="p-2">1</td><td className="p-2">5</td><td className="p-2">10</td></tr>
            <tr className="border-t"><td className="p-2">AUTO_SUSPEND_SECS</td><td className="p-2">300</td><td className="p-2">3600</td><td className="p-2">7200</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
