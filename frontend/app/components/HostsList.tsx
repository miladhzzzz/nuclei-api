"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MoreHorizontal, ArrowUpDown } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

interface Host {
  id: string
  name: string
  aes: number
  acr: number
  ipAddress: string
  operatingSystem: string
  lastSeen: string
  source: string
  tags: string[]
}

const hosts: Host[] = [
  {
    id: "1",
    name: "host-1.subdomain.example.com",
    aes: 478,
    acr: 8,
    ipAddress: "192.168.1.1",
    operatingSystem: "Linux Kernel 2.6",
    lastSeen: "03/21/2023",
    source: "Nessus Scan",
    tags: ["Tag-1", "LastSe"],
  },
  {
    id: "2",
    name: "host-2.subdomain.example.com",
    aes: 414,
    acr: 6,
    ipAddress: "192.168.1.2",
    operatingSystem: "Linux Kernel 3.10 on CentOS Linux release",
    lastSeen: "03/21/2023",
    source: "Nessus Scan",
    tags: ["Tag-1", "LastSe"],
  },
  {
    id: "3",
    name: "host-3.subdomain.example.com",
    aes: 533,
    acr: 6,
    ipAddress: "192.168.1.3",
    operatingSystem: "Linux Kernel 2.6 on CentOS Linux release 6",
    lastSeen: "03/21/2023",
    source: "Nessus Scan",
    tags: ["Tag-1", "LastSe"],
  },
  {
    id: "4",
    name: "host-4.subdomain.example.com",
    aes: 338,
    acr: 4,
    ipAddress: "192.168.1.4",
    operatingSystem: "Linux Kernel 3.13 on Ubuntu 14.04 (trusty)",
    lastSeen: "03/21/2023",
    source: "Nessus Scan",
    tags: ["Tag-1", "LastSe"],
  },
]

type SortField = "aes" | "acr" | "lastSeen"
type SortOrder = "asc" | "desc"

export function HostsList() {
  const [selectedHosts, setSelectedHosts] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<SortField>("aes")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortOrder("desc")
    }
  }

  const sortedHosts = [...hosts].sort((a, b) => {
    const modifier = sortOrder === "asc" ? 1 : -1
    return (a[sortField] > b[sortField] ? 1 : -1) * modifier
  })

  const toggleHost = (hostId: string) => {
    const newSelected = new Set(selectedHosts)
    if (newSelected.has(hostId)) {
      newSelected.delete(hostId)
    } else {
      newSelected.add(hostId)
    }
    setSelectedHosts(newSelected)
  }

  const toggleAll = () => {
    if (selectedHosts.size === hosts.length) {
      setSelectedHosts(new Set())
    } else {
      setSelectedHosts(new Set(hosts.map((host) => host.id)))
    }
  }

  const getAESColor = (score: number) => {
    if (score >= 500) return "bg-red-500"
    if (score >= 400) return "bg-orange-500"
    return "bg-yellow-500"
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]">
              <Checkbox checked={selectedHosts.size === hosts.length} onCheckedChange={toggleAll} />
            </TableHead>
            <TableHead>Name</TableHead>
            <TableHead>
              <Button variant="ghost" className="h-8 p-0" onClick={() => toggleSort("aes")}>
                AES
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>
              <Button variant="ghost" className="h-8 p-0" onClick={() => toggleSort("acr")}>
                ACR
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>IPv4 Address</TableHead>
            <TableHead>Operating System</TableHead>
            <TableHead>
              <Button variant="ghost" className="h-8 p-0" onClick={() => toggleSort("lastSeen")}>
                Last Seen
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Tags</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedHosts.map((host) => (
            <TableRow key={host.id}>
              <TableCell>
                <Checkbox checked={selectedHosts.has(host.id)} onCheckedChange={() => toggleHost(host.id)} />
              </TableCell>
              <TableCell className="font-medium">{host.name}</TableCell>
              <TableCell>
                <Badge className={getAESColor(host.aes)}>{host.aes}</Badge>
              </TableCell>
              <TableCell>{host.acr}</TableCell>
              <TableCell>{host.ipAddress}</TableCell>
              <TableCell className="max-w-[300px] truncate" title={host.operatingSystem}>
                {host.operatingSystem}
              </TableCell>
              <TableCell>{host.lastSeen}</TableCell>
              <TableCell>
                <Badge variant="outline">{host.source}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex gap-1">
                  {host.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>View Details</DropdownMenuItem>
                    <DropdownMenuItem>Edit Tags</DropdownMenuItem>
                    <DropdownMenuItem>Run Scan</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

