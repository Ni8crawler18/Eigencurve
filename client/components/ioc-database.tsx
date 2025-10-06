"use client"

import React, { useEffect, useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RefreshCw, Search, Shield } from "lucide-react"

interface IOC {
  id: string
  entity: string
  entity_type: string
  asn: string
  as_name: string
  as_type: string
  country: string
  threat_type: string
  detection_date: string
  source: string
}

export default function IOCDatabase() {
  const [iocs, setIocs] = useState<IOC[]>([])
  const [loading, setLoading] = useState(false)

  const fetchIocs = async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/iocs")
      const data = await res.json()
      setIocs(data)
    } catch (err) {
      console.error("Failed to fetch IOCs:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIocs()
  }, [])

  return (
    <div className="space-y-6 bg-black min-h-screen text-white text-sm">
      {/* Header Section */}
      <Card className="bg-black border border-[#1E40AF]/40 shadow-none">
        <CardHeader className="flex justify-between items-center">
          <div>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#1E40AF]" /> Indicators of Compromise (IOC) Database
            </CardTitle>
            <p className="text-xs text-gray-500 mt-1">
              Real-time IOC data
            </p>
          </div>
          <Button
            onClick={fetchIocs}
            disabled={loading}
            className="bg-[#1E40AF] text-white hover:bg-[#1E3A8A] transition-colors"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        </CardHeader>
      </Card>

      {/* Data Table */}
      <Card className="bg-black border border-[#1E40AF]/40 shadow-none">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2 text-base">
            <Search className="w-4 h-4 text-[#1E40AF]" /> IOC Records ({iocs.length})
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="rounded-md border border-[#1E40AF]/40 overflow-hidden bg-black">
            <table className="w-full text-xs bg-black">
              <thead className="bg-black border-b border-[#1E40AF]/40">
                <tr>
                  {[
                    "Entity",
                    "Type",
                    "ASN",
                    "ASN Name",
                    "ASN Type",
                    "Country",
                    "Threat Type",
                    "Detection Date",
                    "Source",
                  ].map((header) => (
                    <th
                      key={header}
                      className="px-4 py-3 text-left font-medium text-gray-400 uppercase tracking-wider bg-black"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E40AF]/40 bg-black">
                {iocs.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center text-gray-500 py-6">
                      {loading ? "Loading..." : "No data available."}
                    </td>
                  </tr>
                ) : (
                  iocs.map((ioc) => (
                    <tr
                      key={ioc.id}
                      className="hover:bg-[#0A0A0A] transition-colors"
                    >
                      <td className="px-4 py-2 text-white font-mono">{ioc.entity}</td>
                      <td className="px-4 py-2 text-gray-300">{ioc.entity_type}</td>
                      <td className="px-4 py-2 text-gray-300">{ioc.asn}</td>
                      <td className="px-4 py-2 text-gray-300">{ioc.as_name}</td>
                      <td className="px-4 py-2 text-gray-300">{ioc.as_type}</td>
                      <td className="px-4 py-2 text-[#1E40AF]">{ioc.country}</td>
                      <td className="px-4 py-2 text-gray-300">{ioc.threat_type}</td>
                      <td className="px-4 py-2 text-gray-400">{ioc.detection_date}</td>
                      <td className="px-4 py-2 text-gray-400">{ioc.source}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}