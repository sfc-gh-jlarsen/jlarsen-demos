"use client"

import { useState } from "react"
import { ArchitectureTab } from "@/components/architecture-tab"
import { ScalingTab } from "@/components/scaling-tab"
import { MonitoringTab } from "@/components/monitoring-tab"
import { CostTab } from "@/components/cost-tab"
import { RuntimeComparisonTab } from "@/components/runtime-comparison-tab"

const TABS = [
  { id: "architecture", label: "Architecture" },
  { id: "scaling", label: "Scaling & Warm Pools" },
  { id: "monitoring", label: "Monitoring & Logging" },
  { id: "cost", label: "Cost Estimator" },
  { id: "runtime", label: "Container vs Warehouse" },
]

export function TabNav() {
  const [active, setActive] = useState("architecture")

  return (
    <div>
      <div className="flex border-b mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              active === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div>
        {active === "architecture" && <ArchitectureTab />}
        {active === "scaling" && <ScalingTab />}
        {active === "monitoring" && <MonitoringTab />}
        {active === "cost" && <CostTab />}
        {active === "runtime" && <RuntimeComparisonTab />}
      </div>
    </div>
  )
}
