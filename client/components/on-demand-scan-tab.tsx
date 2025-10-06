"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, Download } from "lucide-react"

interface ScanResult {
  srcIp: string
  dstIp: string
  protocol: number
  verdict: "Malware" | "Benign"
  confidence: number
}

export function OnDemandScanTab() {
  const [logText, setLogText] = useState("")
  const [results, setResults] = useState<ScanResult[] | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleAnalyze = () => {
    setIsAnalyzing(true)

    // Simulate analysis
    setTimeout(() => {
      const mockResults: ScanResult[] = [
        { srcIp: "192.168.100.38", dstIp: "8.8.8.156", protocol: 6, verdict: "Benign", confidence: 94.2 },
        { srcIp: "10.0.0.45", dstIp: "203.0.113.89", protocol: 6, verdict: "Malware", confidence: 97.8 },
        { srcIp: "172.16.0.12", dstIp: "1.1.1.1", protocol: 17, verdict: "Benign", confidence: 92.1 },
        { srcIp: "192.168.1.100", dstIp: "198.51.100.78", protocol: 6, verdict: "Malware", confidence: 89.5 },
        { srcIp: "10.10.10.5", dstIp: "8.8.4.4", protocol: 17, verdict: "Benign", confidence: 95.7 },
      ]
      setResults(mockResults)
      setIsAnalyzing(false)
    }, 2000)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        setLogText(event.target?.result as string)
      }
      reader.readAsText(file)
    }
  }

  const threatsDetected = results?.filter((r) => r.verdict === "Malware").length || 0

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Upload or Paste Logs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pcap,.csv,.txt"
              onChange={handleFileUpload}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-sm text-foreground mb-1">
                <span className="text-primary font-medium">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-muted-foreground">.pcap, .csv, or .txt files</p>
            </label>
          </div>

          <div className="relative">
            <Textarea
              placeholder="Or paste raw NetFlow logs here..."
              value={logText}
              onChange={(e) => setLogText(e.target.value)}
              className="min-h-[200px] font-mono text-sm bg-background border-border text-foreground"
            />
            <FileText className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={!logText || isAnalyzing}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {isAnalyzing ? "Analyzing..." : "Analyze Logs"}
          </Button>
        </CardContent>
      </Card>

      {results && (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-card-foreground">Analysis Results</CardTitle>
              <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                <Download className="h-4 w-4" />
                Export to CSV
              </Button>
            </div>
            <div className="flex gap-6 mt-4">
              <div>
                <p className="text-sm text-muted-foreground">Logs Processed</p>
                <p className="text-2xl font-bold text-foreground">{results.length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Threats Detected</p>
                <p className="text-2xl font-bold text-destructive">{threatsDetected}</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
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
                      Confidence
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Verdict
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {results.map((result, idx) => (
                    <tr key={idx} className="hover:bg-muted/50 transition-colors">
                      <td className="px-4 py-3 text-sm text-foreground font-mono">{result.srcIp}</td>
                      <td className="px-4 py-3 text-sm text-foreground font-mono">{result.dstIp}</td>
                      <td className="px-4 py-3 text-sm text-foreground">{result.protocol === 6 ? "TCP" : "UDP"}</td>
                      <td className="px-4 py-3 text-sm text-foreground">{result.confidence.toFixed(1)}%</td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={result.verdict === "Malware" ? "destructive" : "secondary"}
                          className={
                            result.verdict === "Malware"
                              ? "bg-destructive text-destructive-foreground"
                              : "bg-secondary text-secondary-foreground"
                          }
                        >
                          {result.verdict}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
