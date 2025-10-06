"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  CheckCircle2,
  Globe2,
  BarChart2,
  Wifi,
  Shield,
  Server,
} from "lucide-react"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts"
import { Tooltip } from "recharts"

const COLORS = ["#3B82F6", "#60A5FA", "#93C5FD", "#1E3A8A"]

const throughputData = [
  { time: "00:00", bytes: 2.3 },
  { time: "04:00", bytes: 3.8 },
  { time: "08:00", bytes: 5.4 },
  { time: "12:00", bytes: 7.2 },
  { time: "16:00", bytes: 6.3 },
  { time: "20:00", bytes: 4.1 },
  { time: "24:00", bytes: 3.5 },
]

const protocolData = [
  { name: "TCP", value: 65 },
  { name: "UDP", value: 25 },
  { name: "ICMP", value: 7 },
  { name: "Other", value: 3 },
]

const attackTrends = [
  { time: "00:00", ddos: 12, scan: 3, brute: 6 },
  { time: "04:00", ddos: 22, scan: 8, brute: 5 },
  { time: "08:00", ddos: 15, scan: 5, brute: 9 },
  { time: "12:00", ddos: 25, scan: 12, brute: 11 },
  { time: "16:00", ddos: 18, scan: 9, brute: 6 },
  { time: "20:00", ddos: 10, scan: 4, brute: 3 },
]

const countriesActivity = [
  { name: "United States", lat: 37.09, lon: -95.71, activity: 320 },
  { name: "China", lat: 35.86, lon: 104.19, activity: 280 },
  { name: "Russia", lat: 61.52, lon: 105.31, activity: 230 },
  { name: "India", lat: 20.59, lon: 78.96, activity: 210 },
  { name: "Brazil", lat: -14.23, lon: -51.92, activity: 180 },
  { name: "Germany", lat: 51.16, lon: 10.45, activity: 155 },
]

const topMaliciousIPs = [
  { ip: "203.0.113.45", country: "🇺🇸", asn: "AS15169 (Google)", hits: 142 },
  { ip: "198.51.100.78", country: "🇨🇳", asn: "AS4134 (China Telecom)", hits: 128 },
  { ip: "192.0.2.156", country: "🇷🇺", asn: "AS12389 (Rostelecom)", hits: 95 },
  { ip: "203.0.113.89", country: "🇮🇳", asn: "AS9829 (BSNL India)", hits: 87 },
  { ip: "198.51.100.23", country: "🇩🇪", asn: "AS3320 (Deutsche Telekom)", hits: 73 },
]

const asnContributors = [
  { asn: "AS15169 (Google)", count: 182 },
  { asn: "AS4134 (China Telecom)", count: 159 },
  { asn: "AS4837 (China Unicom)", count: 133 },
  { asn: "AS13335 (Cloudflare)", count: 122 },
  { asn: "AS9009 (M247)", count: 89 },
]

export function TelemetryTab() {
  const [RL, setRL] = useState<any>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        await import("leaflet/dist/leaflet.css")
        const mod = await import("react-leaflet")
        if (active) {
          setRL(mod)
          setReady(true)
        }
      } catch (err) {
        console.error("Leaflet load error:", err)
      }
    })()
    return () => {
      active = false
    }
  }, [])

  const mapCenter: [number, number] = [20, 0]
  const maxActivity = Math.max(...countriesActivity.map((c) => c.activity))

  return (
    <div className="space-y-8">
      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Flows / Second" value="3,128" change="+8.2%" icon={<Activity className="h-4 w-4 text-blue-400" />} />
        <KpiCard title="Active Alerts" value="29" change="+6 from last hour" icon={<AlertTriangle className="h-4 w-4 text-blue-400" />} />
        <KpiCard title="Detection Rate" value="99.1%" change="+0.4%" icon={<TrendingUp className="h-4 w-4 text-blue-400" />} />
        <KpiCard title="Model Health" value="Optimal" change="All systems operational" icon={<CheckCircle2 className="h-4 w-4 text-blue-400" />} />
      </div>

      {/* Map + ASN + Malicious IPs */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* World Map */}
        <Card className="lg:col-span-2 bg-card border-border overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Globe2 className="h-4 w-4 text-blue-400" /> Global Malicious Activity (ASN Aggregated)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[420px] w-full overflow-hidden rounded-b-md">
              {ready && RL ? (
                <RL.MapContainer center={mapCenter} zoom={2} scrollWheelZoom={false} className="h-full w-full bg-background">
                  <RL.TileLayer
                    attribution="© OpenStreetMap contributors"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {countriesActivity.map((c) => {
                    const intensity = c.activity / maxActivity
                    const color = `rgba(59,130,246,${0.3 + intensity * 0.5})`
                    return (
                      <RL.CircleMarker
                        key={c.name}
                        center={[c.lat, c.lon]}
                        radius={8 + intensity * 8}
                        pathOptions={{ color, fillColor: color, fillOpacity: 0.7 }}
                      >
                        <RL.Popup>
                          <div className="text-sm text-white">
                            <strong>{c.name}</strong>
                            <div>Activity: {c.activity}</div>
                          </div>
                        </RL.Popup>
                      </RL.CircleMarker>
                    )
                  })}
                </RL.MapContainer>
              ) : (
                <div className="flex h-full w-full items-center justify-center text-blue-300">
                  Loading map…
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* ASN + IP list */}
        <div className="space-y-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Shield className="h-4 w-4 text-blue-400" /> Top ASN Contributors
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-[200px] overflow-y-auto">
              {asnContributors.map((a, i) => (
                <div key={i} className="flex items-center justify-between border-b border-border pb-2 mb-2">
                  <span className="text-white">{a.asn}</span>
                  <span className="font-mono text-blue-300">{a.count}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Server className="h-4 w-4 text-blue-400" /> Top Malicious IPs
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-[200px] overflow-y-auto">
              {topMaliciousIPs.map((ip, i) => (
                <div key={i} className="flex justify-between items-center border-b border-border pb-2 mb-2 text-sm">
                  <div className="flex items-center gap-2 text-white">
                    <span>{ip.country}</span>
                    <span>{ip.ip}</span>
                  </div>
                  <span className="text-blue-300 font-mono">{ip.hits}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Throughput + Protocol */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 bg-card border-border overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Wifi className="h-4 w-4 text-blue-400" /> Network Throughput (GB transferred)
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={throughputData} margin={{ top: 20, right: 20, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="#93C5FD" />
                <YAxis stroke="#93C5FD" />
                <Tooltip
                  contentStyle={{ backgroundColor: "rgba(17,24,39,0.9)", border: "none" }}
                  labelStyle={{ color: "#93C5FD" }}
                  itemStyle={{ color: "#3B82F6" }}
                />
                <Line type="monotone" dataKey="bytes" stroke="#3B82F6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-card border-border overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <BarChart2 className="h-4 w-4 text-blue-400" /> Protocol Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={protocolData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={90}
                  label={({ name }) => name}
                  labelLine={false}
                >
                  {protocolData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Legend verticalAlign="bottom" height={30} wrapperStyle={{ color: "#93C5FD" }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Attack Trends */}
      <Card className="bg-card border-border overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white">Attack Vector Trends (Last 24 Hours)</CardTitle>
        </CardHeader>
        <CardContent className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={attackTrends} margin={{ top: 20, right: 20, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="#93C5FD" />
              <YAxis stroke="#93C5FD" />
              <Tooltip
                contentStyle={{ backgroundColor: "rgba(17,24,39,0.9)", border: "none" }}
                labelStyle={{ color: "#93C5FD" }}
                itemStyle={{ color: "#3B82F6" }}
              />
              <Legend verticalAlign="top" wrapperStyle={{ color: "#93C5FD" }} />
              <Line type="monotone" dataKey="ddos" stroke="#3B82F6" strokeWidth={2} />
              <Line type="monotone" dataKey="scan" stroke="#60A5FA" strokeWidth={2} />
              <Line type="monotone" dataKey="brute" stroke="#93C5FD" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

/* KPI Component */
function KpiCard({
  title,
  value,
  change,
  icon,
}: {
  title: string
  value: string
  change: string
  icon: React.ReactNode
}) {
  return (
    <Card className="bg-card border-border shadow-sm hover:shadow-md transition-all">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-blue-300">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value}</div>
        <p className="text-xs text-blue-400">{change}</p>
      </CardContent>
    </Card>
  )
}
