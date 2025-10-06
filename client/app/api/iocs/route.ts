import { NextResponse } from "next/server"
import { MongoClient } from "mongodb"

const uri = process.env.MONGODB_URI!
const dbName = process.env.MONGODB_DB || "IOC"

export async function GET() {
  try {
    const client = await MongoClient.connect(uri)
    const db = client.db(dbName)
    const collection = db.collection("iocs")

    const docs = await collection.find({}, { limit: 100 }).sort({ detection_date: -1 }).toArray()

    const formatted = docs.map((d) => ({
      id: d._id?.toString(),
      entity: d.entity || "N/A",
      entity_type: d.entity_type || "N/A",
      asn: d.entity_enrichment?.company?.asn || "N/A",
      as_name: d.entity_enrichment?.company?.as_name || "N/A",
      as_type: d.entity_enrichment?.company?.as_type || "N/A",
      country: d.entity_enrichment?.company?.country || d.entity_src_meta?.country_code || "N/A",
      threat_type:
        d.entity_threat_attr?.malware_family ||
        d.entity_threat_attr?.threat_type ||
        d.entity_threat_attr?.meta?.["1_type"] ||
        "Unknown",
      conf_score: d.entity_src_meta?.conf_score || 0,
      detection_date: d.detection_date
        ? new Date(d.detection_date).toISOString().split("T")[0]
        : "N/A",
      source: d.source || "Unknown",
    }))

    client.close()
    return NextResponse.json(formatted)
  } catch (err) {
    console.error("MongoDB error:", err)
    return NextResponse.json({ error: "Database connection failed" }, { status: 500 })
  }
}
