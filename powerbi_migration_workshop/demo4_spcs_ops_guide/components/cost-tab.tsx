"use client"

import { useState } from "react"

const CREDIT_RATES: Record<string, number> = {
  CPU_X64_XS: 0.5,
  CPU_X64_S: 1.0,
  CPU_X64_M: 2.0,
  CPU_X64_L: 4.0,
}

export function CostTab({ spcsUsage }: { spcsUsage: any[] }) {
  const [family, setFamily] = useState("CPU_X64_S")
  const [nodes, setNodes] = useState(1)
  const [hours, setHours] = useState(10)

  const rate = CREDIT_RATES[family]
  const dailyCredits = rate * nodes * hours
  const monthlyCredits = dailyCredits * 22

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Cost Estimator</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="text-sm font-medium">Instance Family</label>
          <select
            value={family}
            onChange={(e) => setFamily(e.target.value)}
            className="mt-1 block w-full rounded border p-2 bg-background"
          >
            {Object.keys(CREDIT_RATES).map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-sm font-medium">Nodes</label>
          <input
            type="range"
            min={1}
            max={5}
            value={nodes}
            onChange={(e) => setNodes(Number(e.target.value))}
            className="mt-1 block w-full"
          />
          <span className="text-sm text-muted-foreground">{nodes} node(s)</span>
        </div>
        <div>
          <label className="text-sm font-medium">Hours/day active</label>
          <input
            type="range"
            min={1}
            max={24}
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="mt-1 block w-full"
          />
          <span className="text-sm text-muted-foreground">{hours} hrs/day</span>
        </div>
      </div>

      <div className="border rounded-lg p-6 text-center">
        <p className="text-sm text-muted-foreground">Estimated Monthly Credits</p>
        <p className="text-4xl font-bold mt-1">{monthlyCredits.toLocaleString()}</p>
        <p className="text-xs text-muted-foreground mt-2">
          {hours}hr/day x {nodes} node(s) x {rate} credits/hr x 22 business days
        </p>
      </div>

      {spcsUsage.length > 0 && (
        <div>
          <h3 className="text-lg font-medium mb-2">Recent SPCS Usage (from ACCOUNT_USAGE)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border">
              <thead className="bg-muted">
                <tr>
                  <th className="p-2 text-left">Start Time</th>
                  <th className="p-2 text-left">End Time</th>
                  <th className="p-2 text-right">Credits Used</th>
                </tr>
              </thead>
              <tbody>
                {spcsUsage.slice(0, 10).map((row: any, i: number) => (
                  <tr key={i} className="border-t">
                    <td className="p-2">{row.START_TIME}</td>
                    <td className="p-2">{row.END_TIME}</td>
                    <td className="p-2 text-right">{row.CREDITS_USED}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
