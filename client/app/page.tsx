"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TelemetryTab } from "@/components/telemetry-tab"
import { LiveClassificationTab } from "@/components/live-classification-tab"
import { OnDemandScanTab } from "@/components/on-demand-scan-tab"
import { ModelPerformanceTab } from "@/components/model-performance-tab"
import { Activity } from "lucide-react"

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
              <Activity className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Eigencurve</h1>
              <p className="text-sm text-muted-foreground">Quantum ML Threat Detection</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        <Tabs defaultValue="telemetry" className="w-full">
          <TabsList className="grid w-full max-w-2xl grid-cols-4 mb-6">
            <TabsTrigger value="telemetry">Telemetry</TabsTrigger>
            <TabsTrigger value="live">Live Classification</TabsTrigger>
            <TabsTrigger value="scan">On-Demand Scan</TabsTrigger>
            <TabsTrigger value="performance">Model Performance</TabsTrigger>
          </TabsList>

          <TabsContent value="telemetry" className="mt-0">
            <TelemetryTab />
          </TabsContent>

          <TabsContent value="live" className="mt-0">
            <LiveClassificationTab />
          </TabsContent>

          <TabsContent value="scan" className="mt-0">
            <OnDemandScanTab />
          </TabsContent>

          <TabsContent value="performance" className="mt-0">
            <ModelPerformanceTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
