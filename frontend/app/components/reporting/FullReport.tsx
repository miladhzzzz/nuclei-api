"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Download, MoreHorizontal, FileText, Filter } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const vulnerabilityData = [
  {
    id: "V-1",
    name: "OpenSSH < 8.0",
    severity: "Critical",
    category: "SSH",
    affectedHosts: 340,
    firstFound: "2023-01-15",
    lastSeen: "2023-03-21",
    status: "Active",
  },
  {
    id: "V-2",
    name: "SSL 64-bit Block Size Cipher Suites Supported",
    severity: "High",
    category: "SSL/TLS",
    affectedHosts: 172,
    firstFound: "2023-02-01",
    lastSeen: "2023-03-21",
    status: "New",
  },
  {
    id: "V-3",
    name: "Apache HTTP Server 2.4.x < 2.4.55 Multiple Vulnerabilities",
    severity: "High",
    category: "Web Servers",
    affectedHosts: 156,
    firstFound: "2023-02-15",
    lastSeen: "2023-03-21",
    status: "Active",
  },
]

export function FullReport() {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Full Report</h2>
        <div className="flex gap-2">
          <Button variant="outline">
            <FileText className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Data
          </Button>
          <Button variant="outline">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Detailed Vulnerability Analysis</CardTitle>
            <div className="flex gap-2">
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Vulnerability</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Affected Hosts</TableHead>
                <TableHead>First Found</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {vulnerabilityData.map((vuln) => (
                <TableRow key={vuln.id}>
                  <TableCell>{vuln.id}</TableCell>
                  <TableCell className="max-w-[300px] truncate" title={vuln.name}>
                    {vuln.name}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        vuln.severity === "Critical"
                          ? "bg-red-500"
                          : vuln.severity === "High"
                            ? "bg-orange-500"
                            : "bg-yellow-500"
                      }
                    >
                      {vuln.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>{vuln.category}</TableCell>
                  <TableCell>{vuln.affectedHosts}</TableCell>
                  <TableCell>{vuln.firstFound}</TableCell>
                  <TableCell>{vuln.lastSeen}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={
                        vuln.status === "Active" ? "border-orange-500 text-orange-500" : "border-blue-500 text-blue-500"
                      }
                    >
                      {vuln.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

