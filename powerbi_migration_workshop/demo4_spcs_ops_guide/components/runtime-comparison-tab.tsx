export function RuntimeComparisonTab() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Container vs Warehouse Runtime</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border">
          <thead className="bg-muted">
            <tr>
              <th className="p-3 text-left">Aspect</th>
              <th className="p-3 text-left">Warehouse Runtime</th>
              <th className="p-3 text-left">Container Runtime (SPCS)</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t"><td className="p-3">Cold start</td><td className="p-3">Seconds</td><td className="p-3 font-medium">Minutes (use warm pools)</td></tr>
            <tr className="border-t"><td className="p-3">Python packages</td><td className="p-3">Anaconda channel only</td><td className="p-3 font-medium">Anything (Docker/pip)</td></tr>
            <tr className="border-t"><td className="p-3">Cost model</td><td className="p-3">Per-second (warehouse credits)</td><td className="p-3">Per-node-hour</td></tr>
            <tr className="border-t"><td className="p-3">GPU support</td><td className="p-3">No</td><td className="p-3 font-medium">Yes (GPU instance families)</td></tr>
            <tr className="border-t"><td className="p-3">Outbound networking</td><td className="p-3">No outbound</td><td className="p-3">EAI for outbound</td></tr>
            <tr className="border-t"><td className="p-3">Caller&apos;s Rights</td><td className="p-3">No (READ SESSION workaround)</td><td className="p-3 font-medium">Yes (GA Jun 2026)</td></tr>
            <tr className="border-t"><td className="p-3">Max memory</td><td className="p-3">Limited by warehouse</td><td className="p-3">Up to 56 GB (CPU_X64_L)</td></tr>
            <tr className="border-t"><td className="p-3">Concurrent users</td><td className="p-3">1 per warehouse</td><td className="p-3 font-medium">Auto-scaled horizontally</td></tr>
            <tr className="border-t"><td className="p-3">Framework</td><td className="p-3">Streamlit only</td><td className="p-3 font-medium">Any (Next.js, Streamlit, Flask, etc.)</td></tr>
          </tbody>
        </table>
      </div>

      <div className="border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/20 p-4 rounded">
        <h4 className="font-medium text-blue-800 dark:text-blue-400 mb-2">Active Migration (Q2 FY27)</h4>
        <p className="text-sm text-muted-foreground">
          Warehouse-runtime SiS apps are being migrated to container runtime.
          All new apps should target container runtime.
        </p>
      </div>

      <div className="border rounded-lg p-4 bg-green-50 dark:bg-green-950/20">
        <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">Recommendation</h4>
        <p className="text-sm text-muted-foreground">
          Start with container runtime for all new apps. Use CPU_X64_XS for dev/test,
          CPU_X64_S for production dashboards. Set MIN_NODES=1 with warm pool for instant access.
          Auto-suspend after business hours to control costs.
        </p>
      </div>

      <h3 className="text-lg font-medium">When to Use App Runtime (Next.js) vs Streamlit</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border">
          <thead className="bg-muted">
            <tr>
              <th className="p-3 text-left">Use Case</th>
              <th className="p-3 text-left">Streamlit</th>
              <th className="p-3 text-left">App Runtime (Next.js)</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t"><td className="p-3">Quick dashboard/prototype</td><td className="p-3 font-medium">Best choice</td><td className="p-3">Overkill</td></tr>
            <tr className="border-t"><td className="p-3">Multi-page enterprise app</td><td className="p-3">Possible but limited</td><td className="p-3 font-medium">Best choice</td></tr>
            <tr className="border-t"><td className="p-3">Custom UI/branding</td><td className="p-3">Limited theming</td><td className="p-3 font-medium">Full control (CSS/React)</td></tr>
            <tr className="border-t"><td className="p-3">Complex forms/workflows</td><td className="p-3">Awkward state management</td><td className="p-3 font-medium">Native React patterns</td></tr>
            <tr className="border-t"><td className="p-3">Data scientist audience</td><td className="p-3 font-medium">Familiar, fast</td><td className="p-3">Higher barrier</td></tr>
            <tr className="border-t"><td className="p-3">Customer-facing app</td><td className="p-3">Not ideal</td><td className="p-3 font-medium">Production-grade</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
