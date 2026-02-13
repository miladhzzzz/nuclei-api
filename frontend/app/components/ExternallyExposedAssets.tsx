"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const data = [
  { date: "11/19", value: 0 },
  { date: "12/19", value: 50 },
  { date: "1/20", value: 100 },
  { date: "Today", value: 150 },
]

export function ExternallyExposedAssets() {
  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#2563eb" />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-2 text-sm text-muted-foreground">Showing last 90 days • 27.82% ↑</div>
    </div>
  )
}

