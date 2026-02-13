"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface Domain {
  subdomain: string
  ipAddress: string
  isScanning: boolean
  scanResults: string
}

interface DiscoveredDomainsProps {
  domains: Domain[]
  onToggleScan: (subdomain: string) => void
}

export function DiscoveredDomains({ domains = [], onToggleScan }: DiscoveredDomainsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Discovered Domains and Subdomains</CardTitle>
        <CardDescription>
          List of domains and subdomains associated with the scanned target. Toggle vulnerability scans for each
          subdomain and download full reports.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Subdomain</TableHead>
              <TableHead>IP Address</TableHead>
              <TableHead>Vulnerability Scan</TableHead>
              <TableHead>Scan Results</TableHead>
              <TableHead>Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {domains.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No domains discovered yet. Start a scan to discover subdomains.
                </TableCell>
              </TableRow>
            ) : (
              domains.map((domain) => (
                <TableRow key={domain.subdomain}>
                  <TableCell className="font-medium">{domain.subdomain}</TableCell>
                  <TableCell>{domain.ipAddress}</TableCell>
                  <TableCell>
                    <Switch checked={domain.isScanning} onCheckedChange={() => onToggleScan(domain.subdomain)} />
                  </TableCell>
                  <TableCell>{domain.scanResults}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" disabled={domain.scanResults === "Not scanned"}>
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

