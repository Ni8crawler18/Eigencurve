"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const qsvmMetrics = {
  precision: 0.967,
  recall: 0.943,
  f1Score: 0.955,
  confusionMatrix: {
    truePositive: 1834,
    falsePositive: 62,
    trueNegative: 18456,
    falseNegative: 108,
  },
}

const isolationForestMetrics = {
  precision: 0.892,
  recall: 0.878,
  f1Score: 0.885,
  confusionMatrix: {
    truePositive: 1708,
    falsePositive: 206,
    trueNegative: 18312,
    falseNegative: 234,
  },
}

function ConfusionMatrix({ data }: { data: typeof qsvmMetrics.confusionMatrix }) {
  const total = data.truePositive + data.falsePositive + data.trueNegative + data.falseNegative

  return (
    <div className="grid grid-cols-2 gap-2 max-w-sm">
      <div className="col-span-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground mb-2">
        <div></div>
        <div className="text-center">Predicted Positive</div>
        <div className="text-center">Predicted Negative</div>
      </div>
      <div className="text-xs text-muted-foreground flex items-center">Actual Positive</div>
      <div className="bg-accent/20 border border-accent rounded p-4 text-center">
        <div className="text-2xl font-bold text-foreground">{data.truePositive}</div>
        <div className="text-xs text-muted-foreground">True Positive</div>
      </div>
      <div className="bg-destructive/20 border border-destructive rounded p-4 text-center">
        <div className="text-2xl font-bold text-foreground">{data.falseNegative}</div>
        <div className="text-xs text-muted-foreground">False Negative</div>
      </div>
      <div className="text-xs text-muted-foreground flex items-center">Actual Negative</div>
      <div className="bg-destructive/20 border border-destructive rounded p-4 text-center">
        <div className="text-2xl font-bold text-foreground">{data.falsePositive}</div>
        <div className="text-xs text-muted-foreground">False Positive</div>
      </div>
      <div className="bg-accent/20 border border-accent rounded p-4 text-center">
        <div className="text-2xl font-bold text-foreground">{data.trueNegative}</div>
        <div className="text-xs text-muted-foreground">True Negative</div>
      </div>
    </div>
  )
}

function MetricsDisplay({ metrics }: { metrics: typeof qsvmMetrics }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-muted rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Precision</p>
          <p className="text-2xl font-bold text-foreground">{(metrics.precision * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-muted rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Recall</p>
          <p className="text-2xl font-bold text-foreground">{(metrics.recall * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-muted rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">F1-Score</p>
          <p className="text-2xl font-bold text-foreground">{(metrics.f1Score * 100).toFixed(1)}%</p>
        </div>
      </div>
      <div>
        <h4 className="text-sm font-medium text-foreground mb-3">Confusion Matrix</h4>
        <ConfusionMatrix data={metrics.confusionMatrix} />
      </div>
    </div>
  )
}

export function ModelPerformanceTab() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">QSVM Performance</CardTitle>
          <p className="text-sm text-muted-foreground">Quantum Support Vector Machine</p>
        </CardHeader>
        <CardContent>
          <MetricsDisplay metrics={qsvmMetrics} />
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Isolation Forest Performance</CardTitle>
          <p className="text-sm text-muted-foreground">Classical Machine Learning Model</p>
        </CardHeader>
        <CardContent>
          <MetricsDisplay metrics={isolationForestMetrics} />
        </CardContent>
      </Card>
    </div>
  )
}
