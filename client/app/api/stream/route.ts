import { NextResponse } from "next/server"

export const runtime = "nodejs"

// SSE stream endpoint
export async function GET() {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      const net = require("net")
      const client = new net.Socket()

      client.connect(9999, "127.0.0.1", () => {
        console.log("Connected to listener.py")
      })

      client.on("data", (data: Buffer) => {
        const message = data.toString().trim()
        if (message) {
          controller.enqueue(encoder.encode(`data: ${message}\n\n`))
        }
      })

      client.on("close", () => {
        controller.enqueue(encoder.encode("event: end\ndata: Connection closed\n\n"))
        controller.close()
      })

      client.on("error", (err: Error) => {
        controller.enqueue(encoder.encode(`event: error\ndata: ${err.message}\n\n`))
      })
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
