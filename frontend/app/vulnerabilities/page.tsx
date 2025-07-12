"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { VulnerabilityTable } from "../components/VulnerabilityTable"

const targetedVulnerabilities = [
  {
    name: "Microsoft CVE-2017-0146: Windows...",
    assetsAffected: 1258,
    cvssScore: 9.3,
    publishedOn: "Mon, Mar 13, 2017",
    riskScore: 918.75,
  },
  {
    name: "Microsoft CVE-2017-0102: Windows...",
    assetsAffected: 374,
    cvssScore: 4.5,
    publishedOn: "Mon, Mar 13, 2017",
    riskScore: 203.78,
  },
  {
    name: "Microsoft CVE-2017-0199: Microsoft...",
    assetsAffected: 327,
    cvssScore: 9.3,
    publishedOn: "Mon, Apr 10, 2017",
    riskScore: 315.55,
  },
]

export default function VulnerabilitiesPage() {
  return (
    <div className="container mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold mb-8">Vulnerabilities Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">MOST COMMON ACTIVELY TARGETED VULNERABILITIES</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Assets Affected</TableHead>
                  <TableHead>CVSS Score</TableHead>
                  <TableHead>Risk Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {targetedVulnerabilities.map((vuln) => (
                  <TableRow key={vuln.name}>
                    <TableCell className="font-medium max-w-[200px] truncate">{vuln.name}</TableCell>
                    <TableCell>{vuln.assetsAffected}</TableCell>
                    <TableCell>
                      <Badge
                        className={
                          vuln.cvssScore >= 9.0
                            ? "bg-red-500"
                            : vuln.cvssScore >= 7.0
                              ? "bg-orange-500"
                              : "bg-yellow-500"
                        }
                      >
                        {vuln.cvssScore}
                      </Badge>
                    </TableCell>
                    <TableCell>{vuln.riskScore}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">ASSETS WITH ACTIVELY TARGETED VULNERABILITIES</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center h-[200px]">
            <div className="text-5xl font-bold text-blue-400">1.58k</div>
            <div className="text-sm text-muted-foreground mt-2">Assets with Actively Targeted Vulnerabilities</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">DETAILED VULNERABILITY ANALYSIS</CardTitle>
        </CardHeader>
        <CardContent>
          <VulnerabilityTable />
        </CardContent>
      </Card>
    </div>
  )
}

