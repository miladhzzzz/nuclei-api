"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Brain, TrendingUp, AlertTriangle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface PredictionData {
  asset: string
  riskScore: number
  confidence: number
  vulnerabilities: number
  previousIncidents: number
  predictedTimeframe: string
}

interface TrendData {
  date: string
  vulnerabilities: number
  incidents: number
  riskScore: number
}

const predictions: PredictionData[] = [
  {
    asset: "web-server-01.example.com",
    riskScore: 85,
    confidence: 92,
    vulnerabilities: 12,
    previousIncidents: 3,
    predictedTimeframe: "Next 7 days",
  },
  {
    asset: "db-cluster-main.example.com",
    riskScore: 76,
    confidence: 88,
    vulnerabilities: 8,
    previousIncidents: 2,
    predictedTimeframe: "Next 14 days",
  },
  {
    asset: "auth-service.example.com",
    riskScore: 71,
    confidence: 85,
    vulnerabilities: 6,
    previousIncidents: 1,
    predictedTimeframe: "Next 30 days",
  },
]

const trendData: TrendData[] = [
  { date: "2024-01", vulnerabilities: 15, incidents: 2, riskScore: 65 },
  { date: "2024-02", vulnerabilities: 18, incidents: 3, riskScore: 72 },
  { date: "2024-03", vulnerabilities: 12, incidents: 1, riskScore: 58 },
  { date: "2024-04", vulnerabilities: 20, incidents: 4, riskScore: 78 },
  { date: "2024-05", vulnerabilities: 25, incidents: 5, riskScore: 85 },
  { date: "2024-06", vulnerabilities: 22, incidents: 3, riskScore: 76 },
]

const insights = [
  "Increased attack attempts detected on web-facing assets",
  "Database servers showing patterns similar to previous incident precursors",
  "Authentication services experiencing elevated probe attempts",
]

export function IncidentPrediction() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card className="md:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-blue-500" />
                Incident Prediction & Trend Analysis
              </CardTitle>
              <CardDescription>AI-powered security incident prediction and trend analysis</CardDescription>
            </div>
            <Select defaultValue="7">
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select timeframe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Next 7 days</SelectItem>
                <SelectItem value="14">Next 14 days</SelectItem>
                <SelectItem value="30">Next 30 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="grid gap-4 md:grid-cols-3">
              {predictions.map((prediction) => (
                <Card key={prediction.asset} className="relative overflow-hidden">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium truncate">{prediction.asset}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Confidence:</span>
                        <span className="font-medium">{prediction.confidence}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Vulnerabilities:</span>
                        <span className="font-medium">{prediction.vulnerabilities}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Previous Incidents:</span>
                        <span className="font-medium">{prediction.previousIncidents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Timeframe:</span>
                        <span className="font-medium">{prediction.predictedTimeframe}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Vulnerability Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="vulnerabilities"
                        stroke="#2563eb"
                        name="Vulnerabilities"
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="incidents"
                        stroke="#dc2626"
                        name="Security Incidents"
                      />
                      <Line yAxisId="right" type="monotone" dataKey="riskScore" stroke="#eab308" name="Risk Score" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  AI Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {insights.map((insight, index) => (
                    <Alert key={index}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle>Predictive Insight</AlertTitle>
                      <AlertDescription>{insight}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

