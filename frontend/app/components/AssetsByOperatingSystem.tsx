"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"

interface Asset {
  address: string
  name: string
  os: string
  findings: {
    critical: number
    high: number
    medium: number
    info: number
  }
}

interface AssetsByOperatingSystemProps {
  assets: Asset[]
}

export default function AssetsByOperatingSystem({ assets }: AssetsByOperatingSystemProps) {
  const groupedAssets = assets.reduce(
    (acc, asset) => {
      if (!acc[asset.os]) {
        acc[asset.os] = 0
      }
      acc[asset.os]++
      return acc
    },
    {} as Record<string, number>,
  )

  const data = Object.entries(groupedAssets).map(([os, count]) => ({
    name: os,
    value: count,
  }))

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"]

  return (
    <Card className="bg-zinc-900 text-white">
      <CardHeader>
        <CardTitle className="text-sm font-medium">ASSETS BY OPERATING SYSTEM</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

