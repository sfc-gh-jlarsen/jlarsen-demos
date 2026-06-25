import { Suspense } from "react"
import { querySnowflake } from "@/lib/snowflake"
import { ArchitectureTab } from "@/components/architecture-tab"
import { ScalingTab } from "@/components/scaling-tab"
import { MonitoringTab } from "@/components/monitoring-tab"
import { CostTab } from "@/components/cost-tab"
import { RuntimeComparisonTab } from "@/components/runtime-comparison-tab"
import { TabNav } from "@/components/tab-nav"

export const dynamic = "force-dynamic"

async function getSpcsUsage() {
  try {
    const rows = await querySnowflake(`
      SELECT START_TIME, END_TIME, CREDITS_USED, SERVICE_TYPE
      FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
      WHERE SERVICE_TYPE = 'SNOWPARK_CONTAINER_SERVICES'
      ORDER BY START_TIME DESC
      LIMIT 30
    `)
    return rows
  } catch {
    return []
  }
}

export default async function Home() {
  const spcsUsage = await getSpcsUsage()

  return (
    <main className="w-full py-8 px-4 max-w-7xl mx-auto">
      <p className="text-muted-foreground mb-8">
        Running Streamlit at Scale — Architecture, Scaling, Monitoring, and Cost
      </p>
      <TabNav spcsUsage={spcsUsage} />
    </main>
  )
}
