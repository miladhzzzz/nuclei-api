"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

interface Asset {
  address: string
  name: string
  findings: {
    critical: number
    high: number
    medium: number
    info: number
  }
}

interface RiskiestAssetsProps {
  assets: Asset[]
}

export default function RiskiestAssets({ assets }: RiskiestAssetsProps) {
  const getSeverityColor = (severity: keyof Asset["findings"]) => {
    const colors = {
      critical: "bg-red-500",
      high: "bg-orange-500",
      medium: "bg-yellow-500",
      info: "bg-blue-500",
    }
    return colors[severity]
  }

  const getTotalFindings = (findings: Asset["findings"]) =>
    Object.values(findings).reduce((sum, count) => sum + count, 0)

  return (
    <Card className="bg-zinc-900 text-white">
      <CardHeader>
        <CardTitle className="text-sm font-medium">TOP RISKIEST ASSETS BY SECURITY FINDINGS</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800">
              <TableHead className="text-zinc-400">Address</TableHead>
              <TableHead className="text-zinc-400">Asset Name</TableHead>
              <TableHead className="text-zinc-400">Security Findings</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {assets.map((asset) => (
              <TableRow key={asset.address} className="border-zinc-800">
                <TableCell className="font-mono">{asset.address}</TableCell>
                <TableCell>{asset.name}</TableCell>
                <TableCell>
                  <div className="flex flex-col gap-1.5">
                    <div className="text-sm text-zinc-400 mb-1">
                      Total: <span className="font-bold">{getTotalFindings(asset.findings)}</span>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {Object.entries(asset.findings).map(
                        ([severity, count]) =>
                          count > 0 && (
                            <div key={severity} className="flex items-center gap-2">
                              <Badge
                                className={`
                                ${getSeverityColor(severity as keyof Asset["findings"])} 
                                w-32 flex justify-between items-center px-3
                              `}
                              >
                                <span>{severity.toUpperCase()}</span>
                                <span className="font-bold">{count}</span>
                              </Badge>
                            </div>
                          ),
                      )}
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

