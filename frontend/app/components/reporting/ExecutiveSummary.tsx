"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis } from "recharts"
import { Button } from "@/components/ui/button"
import { Share2, Download, MoreHorizontal, ChevronDown } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"

const vulnerabilityStateData = [
  {
    state: "New",
    exploitable: "2.2K",
    critical: "554",
    high: "2.7K",
    medium: "5.3K",
  },
  {
    state: "Active",
    exploitable: "2.3K",
    critical: "630",
    high: "3.3K",
    medium: "8.2K",
  },
  {
    state: "Fixed",
    exploitable: "32",
    critical: "20",
    high: "28",
    medium: "146",
  },
  {
    state: "Resurfaced",
    exploitable: "52",
    critical: "26",
    high: "95",
    medium: "166",
  },
]

const prevalentVulnerabilities = [
  {
    name: "Security Updates for Microsoft .NET Framework",
    shortName: "MS .NET Framework",
    value: 20,
    color: "#0088FE",
  },
  {
    name: "Windows Speculative Execution Configuration",
    shortName: "Win Spec Execution",
    value: 18,
    color: "#00C49F",
  },
  {
    name: "KB5009557: Windows 10 Version 1809",
    shortName: "KB5009557",
    value: 15,
    color: "#FFBB28",
  },
  {
    name: "KB5005030: Windows 10 Version 1809",
    shortName: "KB5005030",
    value: 12,
    color: "#FF8042",
  },
  {
    name: "KB5005568: Windows 10 Version 1809",
    shortName: "KB5005568",
    value: 10,
    color: "#8884D8",
  },
]

const patchableVulnerabilities = [
  { plugin: "OpenSSH < 8.0", firstSeen: "701156", type: "SSH", severity: "Medium", count: "340" },
  { plugin: "OpenSSH 7.9.A", firstSeen: "701157", type: "SSH", severity: "Medium", count: "303" },
  { plugin: "OpenSSH 7.8.A", firstSeen: "701158", type: "SSH", severity: "Medium", count: "256" },
]

const operatingSystemData = [
  { name: "Windows", count: 250 },
  { name: "Linux (kernel)", count: 180 },
  { name: "Linux kernel 2.6", count: 120 },
  { name: "Windows xp", count: 90 },
  { name: "Linux Ubuntu", count: 85 },
]

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"]

export function ExecutiveSummary() {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center border-b pb-4">
        <h2 className="text-xl font-semibold">Executive Summary (Explore)</h2>
        <div className="flex gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Jump to Dashboard
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Dashboard 1</DropdownMenuItem>
              <DropdownMenuItem>Dashboard 2</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="outline">Dashboards</Button>
          <Button variant="outline">
            <Share2 className="mr-2 h-4 w-4" />
            Share
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Vulnerabilities by State</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>State</TableHead>
                  <TableHead>Exploitable</TableHead>
                  <TableHead>Critical</TableHead>
                  <TableHead>High</TableHead>
                  <TableHead>Medium</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {vulnerabilityStateData.map((row) => (
                  <TableRow key={row.state}>
                    <TableCell>{row.state}</TableCell>
                    <TableCell>{row.exploitable}</TableCell>
                    <TableCell>{row.critical}</TableCell>
                    <TableCell>{row.high}</TableCell>
                    <TableCell>{row.medium}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Most Prevalent Vulnerabilities Discovered in the Last 14 Days
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={prevalentVulnerabilities}
                  cx="50%"
                  cy="45%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                >
                  {prevalentVulnerabilities.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name, props) => [value, props.payload.name]}
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                    padding: "8px",
                  }}
                />
                <Legend
                  layout="vertical"
                  align="center"
                  verticalAlign="bottom"
                  formatter={(value, entry, index) => {
                    const { shortName } = prevalentVulnerabilities[index]
                    return <span className="text-sm">{shortName}</span>
                  }}
                  wrapperStyle={{
                    paddingTop: "20px",
                    width: "100%",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Top 100 Vulnerabilities with Patch Available More than 120 Days
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Plugin Name</TableHead>
                  <TableHead>First Seen</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Count</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patchableVulnerabilities.map((vuln) => (
                  <TableRow key={vuln.plugin}>
                    <TableCell className="font-medium">{vuln.plugin}</TableCell>
                    <TableCell>{vuln.firstSeen}</TableCell>
                    <TableCell>{vuln.type}</TableCell>
                    <TableCell>
                      <Badge className={vuln.severity === "High" ? "bg-red-500" : "bg-yellow-500"}>
                        {vuln.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>{vuln.count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Asset Count by Operating System (Top 15)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={operatingSystemData} layout="vertical">
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={150} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

