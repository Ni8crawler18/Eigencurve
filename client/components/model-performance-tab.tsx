"use client"

import Image from "next/image"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const metrics = [
  "General Performance",
  "ROC Curve",
  "Precision-Recall Curve",
  "Validation Curve",
  "Calibration Curve",
  "Cumulative Gain and Lift Chart",
  "Cross-Validation Curve",
]

export function ModelPerformanceTab() {
  return (
    <div className="space-y-10">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground text-xl font-semibold">
            Model Performance Comparison — VQC (PennyLane) vs CNN
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Comparative visualization of classical and quantum models trained on CIC-IDS-2018 dataset
          </p>
        </CardHeader>

        <CardContent className="space-y-12">
          {metrics.map((metric) => (
            <div key={metric} className="space-y-4">
              <h4 className="text-lg font-semibold text-foreground">{metric}</h4>

              {/* Two-column comparison layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                {/* VQC Panel */}
                <Card className="bg-card border border-border overflow-hidden">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-foreground text-base font-medium">
                      VQC (PennyLane)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {metric === "General Performance" ? (
                      <div className="space-y-3 text-sm text-muted-foreground p-3">
                        <p><strong>Accuracy:</strong> —</p>
                        <p><strong>Precision:</strong> —</p>
                        <p><strong>Recall:</strong> —</p>
                        <p><strong>F1-Score:</strong> —</p>
                        
                        {/* CHANGED: Removed the bordered container and used flex to position the image */}
                        <div className="flex justify-end">
                          <Image
                            src="/vqc-performance.jpg"
                            alt="VQC general performance"
                            width={800}
                            height={450}
                            className="w-auto h-auto max-w-[75%] object-contain"
                          />
                        </div>

                      </div>
                    ) : (
                      <div className="flex items-center justify-center overflow-hidden rounded-md border border-border bg-card">
                        <Image
                          src={`/vqc-${metric.toLowerCase().replace(/ /g, "-")}.jpg`}
                          alt={`${metric} (VQC)`}
                          width={800}
                          height={450}
                          className="w-auto h-auto max-w-full object-contain bg-card"
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* CNN Panel */}
                <Card className="bg-card border border-border overflow-hidden">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-foreground text-base font-medium">
                      CNN (Classical)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {metric === "General Performance" ? (
                      <div className="flex items-center justify-center overflow-hidden rounded-md border border-border bg-card">
                        <Image
                          src="/cnn-performance.png"
                          alt="CNN general performance"
                          width={800}
                          height={450}
                          className="w-auto h-auto max-w-full object-contain bg-card"
                        />
                      </div>
                    ) : (
                      <div className="flex items-center justify-center overflow-hidden rounded-md border border-border bg-card">
                        <Image
                          src={`/cnn-${metric.toLowerCase().replace(/ /g, "-")}.jpg`}
                          alt={`${metric} (CNN)`}
                          width={800}
                          height={450}
                          className="w-auto h-auto max-w-full object-contain bg-card"
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          ))}

          <div className="pt-6 text-center border-t border-border">
            <p className="text-sm text-muted-foreground italic">
              Analysis conducted using the CIC-IDS-2018 dataset
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}