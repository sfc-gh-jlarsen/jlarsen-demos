export function ArchitectureTab() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">SPCS Architecture</h2>
      <pre className="bg-muted p-4 rounded-lg text-xs overflow-x-auto font-mono">
{`┌─────────────────────────────────────────────────────────────┐
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
└─────────────────────────────────────────────────────────────┘`}
      </pre>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-blue-600 mb-2">Compute Pool</h3>
          <p className="text-sm text-muted-foreground">
            Your VM fleet — like an auto-scaling group. Choose instance family for CPU/memory sizing.
          </p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-blue-600 mb-2">Nodes</h3>
          <p className="text-sm text-muted-foreground">
            Individual VMs within the pool. MIN/MAX_NODES controls fleet size.
          </p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-blue-600 mb-2">Service Instances</h3>
          <p className="text-sm text-muted-foreground">
            Replicas of your container (horizontal scale). MIN/MAX_INSTANCES per service.
          </p>
        </div>
      </div>

      <h3 className="text-lg font-medium mt-6">Instance Family Reference</h3>
      <div className="border-l-4 border-amber-500 bg-amber-50 dark:bg-amber-950/20 p-3 rounded mb-4">
        <p className="text-sm text-amber-800 dark:text-amber-400">
          Credit rates shown are approximate. The{" "}
          <a href="https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf" className="underline font-medium" target="_blank" rel="noopener noreferrer">
            Snowflake Consumption Table
          </a>{" "}
          is the authoritative source of truth on credit consumption rates.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border">
          <thead className="bg-muted">
            <tr>
              <th className="p-2 text-left">Family</th>
              <th className="p-2 text-left">vCPUs</th>
              <th className="p-2 text-left">Memory</th>
              <th className="p-2 text-left">Credits/hr</th>
              <th className="p-2 text-left">Best For</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t"><td className="p-2 font-mono">CPU_X64_XS</td><td className="p-2">1</td><td className="p-2">6 GB</td><td className="p-2">~0.5</td><td className="p-2">Dev/test, simple apps</td></tr>
            <tr className="border-t"><td className="p-2 font-mono">CPU_X64_S</td><td className="p-2">3</td><td className="p-2">13 GB</td><td className="p-2">~1.0</td><td className="p-2">Standard dashboards</td></tr>
            <tr className="border-t"><td className="p-2 font-mono">CPU_X64_M</td><td className="p-2">6</td><td className="p-2">28 GB</td><td className="p-2">~2.0</td><td className="p-2">Data processing apps</td></tr>
            <tr className="border-t"><td className="p-2 font-mono">CPU_X64_L</td><td className="p-2">12</td><td className="p-2">56 GB</td><td className="p-2">~4.0</td><td className="p-2">ML inference</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
