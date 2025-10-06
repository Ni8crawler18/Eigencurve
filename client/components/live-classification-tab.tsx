"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Search } from "lucide-react"

interface FlowClassification {
  timestamp: string
  srcIp: string
  dstIp: string
  protocol: string
  duration: number
  bytes: number
  packets: number
  verdict: "Malware" | "Benign"
}

export function LiveClassificationTab() {
  const [flows, setFlows] = useState<FlowClassification[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    if (isPaused) return

    const evtSource = new EventSource("/api/stream")

    evtSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const flow: FlowClassification = {
          timestamp: new Date().toLocaleTimeString(),
          srcIp: data.src_ip,
          dstIp: data.dst_ip,
          protocol:
            data.protocol === 6
              ? "TCP"
              : data.protocol === 17
              ? "UDP"
              : data.protocol === 1
              ? "ICMP"
              : String(data.protocol),
          duration: data.duration_ms,
          bytes: data.bytes,
          packets: data.packets,
          verdict: data.bytes > 90000 || data.duration_ms > 50000 ? "Malware" : "Benign",
        }

        setFlows((prev) => [flow, ...prev].slice(0, 100))
      } catch (err) {
        console.error("Bad JSON:", err)
      }
    }

    evtSource.onerror = (err) => {
      console.error("SSE error:", err)
    }

    return () => evtSource.close()
  }, [isPaused])

  const filteredFlows = flows.filter(
    (flow) =>
      flow.srcIp.includes(searchTerm) ||
      flow.dstIp.includes(searchTerm) ||
      flow.protocol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      flow.verdict.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-card-foreground">Live Network Flow Stream</CardTitle>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch id="pause-feed" checked={isPaused} onCheckedChange={setIsPaused} />
              <Label htmlFor="pause-feed" className="text-sm text-muted-foreground">
                {isPaused ? "Paused" : "Live"}
              </Label>
            </div>
          </div>
        </div>
        <div className="relative mt-4">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by IP, protocol, or verdict..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-background border-border text-foreground"
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border border-border overflow-hidden">
          <div className="max-h-[600px] overflow-y-auto">
            <table className="w-full">
              <thead className="bg-muted sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Source IP
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Destination IP
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Protocol
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Duration (ms)
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Bytes
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Packets
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Verdict
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredFlows.map((flow, idx) => (
                  <tr key={idx} className="hover:bg-muted/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-mono">{flow.timestamp}</td>
                    <td className="px-4 py-3 text-sm font-mono">{flow.srcIp}</td>
                    <td className="px-4 py-3 text-sm font-mono">{flow.dstIp}</td>
                    <td className="px-4 py-3 text-sm">{flow.protocol}</td>
                    <td className="px-4 py-3 text-sm">{flow.duration}</td>
                    <td className="px-4 py-3 text-sm">{flow.bytes}</td>
                    <td className="px-4 py-3 text-sm">{flow.packets}</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={flow.verdict === "Malware" ? "destructive" : "secondary"}
                        className={
                          flow.verdict === "Malware"
                            ? "bg-destructive text-destructive-foreground"
                            : "bg-secondary text-secondary-foreground"
                        }
                      >
                        {flow.verdict}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-4">
          Showing {filteredFlows.length} of {flows.length} flows
        </p>
      </CardContent>
    </Card>
  )
}