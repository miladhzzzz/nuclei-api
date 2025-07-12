import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Vulnerability {
  id: string
  type: string
  protocol: string
  severity: "informational" | "low" | "medium" | "high"
  target: string
  details: string[]
}

interface VulnerabilitiesProps {
  vulnerabilities: Vulnerability[]
}

const severityColors = {
  informational: "bg-blue-500",
  low: "bg-yellow-500",
  medium: "bg-orange-500",
  high: "bg-red-500",
}

const severityIcons = {
  informational: Info,
  low: AlertCircle,
  medium: AlertTriangle,
  high: ShieldAlert,
}

export function Vulnerabilities({ vulnerabilities }: VulnerabilitiesProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const filteredVulnerabilities = useMemo(() => {
    return vulnerabilities.filter(
      (vuln) =>
        (severityFilter === "all" || vuln.severity === severityFilter) &&
        (vuln.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
          vuln.target.toLowerCase().includes(searchTerm.toLowerCase())),
    )
  }, [vulnerabilities, searchTerm, severityFilter])

  const severityCounts = useMemo(() => {
    return vulnerabilities.reduce(
      (acc, vuln) => {
        acc[vuln.severity] = (acc[vuln.severity] || 0) + 1
        return acc
      },
      {} as Record<string, number>,
    )
  }, [vulnerabilities])

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Vulnerabilities</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4 mb-6">
          {(["informational", "low", "medium", "high"] as const).map((severity) => {
            const Icon = severityIcons[severity]
            return (
              <Card key={severity} className={`${severityColors[severity]} text-white`}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {severity.charAt(0).toUpperCase() + severity.slice(1)}
                  </CardTitle>
                  <Icon className="h-4 w-4" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{severityCounts[severity] || 0}</div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="flex space-x-2 mb-4">
          <Input
            placeholder="Search vulnerabilities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severities</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="informational">Informational</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {filteredVulnerabilities.length === 0 ? (
          <p className="text-muted-foreground">No vulnerabilities found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">#</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Protocol</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredVulnerabilities.map((vuln, index) => (
                <TableRow key={vuln.id}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>{vuln.type}</TableCell>
                  <TableCell>
                    <Badge className={severityColors[vuln.severity]}>
                      {vuln.severity.charAt(0).toUpperCase() + vuln.severity.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>{vuln.protocol}</TableCell>
                  <TableCell>{vuln.target}</TableCell>
                  <TableCell>
                    <ul className="list-decimal pl-5">
                      {vuln.details.slice(0, expandedRows.has(vuln.id) ? undefined : 3).map((detail, index) => (
                        <li key={index}>{detail}</li>
                      ))}
                    </ul>
                    {vuln.details.length > 3 && (
                      <Button
                        variant="link"
                        onClick={() =>
                          setExpandedRows((prev) => {
                            const next = new Set(prev)
                            if (next.has(vuln.id)) {
                              next.delete(vuln.id)
                            } else {
                              next.add(vuln.id)
                            }
                            return next
                          })
                        }
                        className="mt-2"
                      >
                        {expandedRows.has(vuln.id) ? "Show less" : `Show ${vuln.details.length - 3} more`}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

