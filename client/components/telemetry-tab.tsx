"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, AlertTriangle, TrendingUp, CheckCircle2 } from "lucide-react"
import { Line, LineChart, Bar, BarChart, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const detectionsData = [
  { time: "00:00", benign: 2400, malware: 12 },
  { time: "02:00", benign: 2210, malware: 18 },
  { time: "04:00", benign: 2100, malware: 8 },
  { time: "06:00", benign: 2450, malware: 22 },
  { time: "08:00", benign: 2890, malware: 15 },
  { time: "10:00", benign: 3200, malware: 28 },
  { time: "12:00", benign: 3100, malware: 19 },
  { time: "14:00", benign: 2950, malware: 24 },
  { time: "16:00", benign: 3300, malware: 31 },
  { time: "18:00", benign: 3150, malware: 17 },
  { time: "20:00", benign: 2800, malware: 21 },
  { time: "22:00", benign: 2600, malware: 14 },
]

const topMaliciousIPs = [
  { ip: "203.0.113.45", count: 142 },
  { ip: "198.51.100.78", count: 128 },
  { ip: "192.0.2.156", count: 95 },
  { ip: "203.0.113.89", count: 87 },
  { ip: "198.51.100.23", count: 73 },
]

const topTargetedPorts = [
  { port: "443", count: 1842 },
  { port: "80", count: 1523 },
  { port: "22", count: 892 },
  { port: "3389", count: 645 },
  { port: "8080", count: 421 },
]

export function TelemetryTab() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-card-foreground">Flows / Second</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-card-foreground">2,847</div>
            <p className="text-xs text-muted-foreground">+12.5% from last hour</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-card-foreground">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-card-foreground">23</div>
            <p className="text-xs text-muted-foreground">-3 from last hour</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-card-foreground">Detection Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-card-foreground">98.7%</div>
            <p className="text-xs text-muted-foreground">+0.3% from yesterday</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-card-foreground">Model Health</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-card-foreground">Optimal</div>
            <p className="text-xs text-muted-foreground">All systems operational</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2 bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Detections Over Time (Last 24 Hours)</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={{
                benign: {
                  label: "Benign Flows",
                  color: "hsl(var(--chart-1))",
                },
                malware: {
                  label: "Malware Detections",
                  color: "hsl(var(--chart-2))",
                },
              }}
              className="h-[300px]"
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={detectionsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
                  <YAxis stroke="hsl(var(--muted-foreground))" />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line type="monotone" dataKey="benign" stroke="var(--color-benign)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="malware" stroke="var(--color-malware)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm text-card-foreground">Top Malicious Source IPs</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer
                config={{
                  count: {
                    label: "Detections",
                    color: "hsl(var(--chart-2))",
                  },
                }}
                className="h-[130px]"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topMaliciousIPs} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis
                      dataKey="ip"
                      type="category"
                      width={100}
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="count" fill="var(--color-count)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm text-card-foreground">Top Targeted Ports</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer
                config={{
                  count: {
                    label: "Connections",
                    color: "hsl(var(--chart-1))",
                  },
                }}
                className="h-[130px]"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topTargetedPorts} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis
                      dataKey="port"
                      type="category"
                      width={50}
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="count" fill="var(--color-count)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
