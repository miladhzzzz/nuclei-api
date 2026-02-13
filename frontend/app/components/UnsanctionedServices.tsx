"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const services = [
  { name: "RDP", count: 14 },
  { name: "SSH", count: 32 },
  { name: "FTP", count: 42 },
]

export function UnsanctionedServices() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Services</TableHead>
          <TableHead className="text-right">Asset Count</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {services.map((service) => (
          <TableRow key={service.name}>
            <TableCell>{service.name}</TableCell>
            <TableCell className="text-right">{service.count}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

