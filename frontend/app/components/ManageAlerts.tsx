"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Pencil, Trash2 } from "lucide-react"

const alerts = [
  {
    id: 1,
    name: "Failed and Paused Alert",
    enabled: true,
    events: "Failed, Paused",
    method: "SMTP e-mail",
  },
  {
    id: 2,
    name: "Critical Vulnerabilities Alert",
    enabled: false,
    events: "Vulnerability Detection",
    method: "Slack",
  },
]

export function ManageAlerts() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Manage Alerts</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Alert Name</TableHead>
              <TableHead>Enabled</TableHead>
              <TableHead>Events</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id}>
                <TableCell>{alert.name}</TableCell>
                <TableCell>
                  <Switch checked={alert.enabled} />
                </TableCell>
                <TableCell>{alert.events}</TableCell>
                <TableCell>{alert.method}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon">
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4" />
                    </Button>
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

