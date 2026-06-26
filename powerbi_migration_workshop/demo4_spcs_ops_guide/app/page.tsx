import { TabNav } from "@/components/tab-nav"

export const dynamic = "force-dynamic"

export default function Home() {
  return (
    <main className="w-full py-8 px-4 max-w-7xl mx-auto">
      <p className="text-muted-foreground mb-8">
        Running Streamlit at Scale — Architecture, Scaling, Monitoring, and Cost
      </p>
      <TabNav />
    </main>
  )
}
