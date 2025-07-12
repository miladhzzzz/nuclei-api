"use client"

import { LayoutDashboard, Shield, Database, Search } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar"

const navigation = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    href: "#",
  },
  {
    title: "My Scans",
    icon: Search,
    href: "#",
    isActive: true,
  },
  {
    title: "Assets",
    icon: Database,
    href: "#",
  },
  {
    title: "Vulnerabilities",
    icon: Shield,
    href: "#",
  },
]

export function AppSidebar() {
  return (
    <Sidebar className="border-r-0">
      <SidebarHeader className="border-b border-border p-4">
        <h2 className="text-lg font-semibold">Cybernod Scanner</h2>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {navigation.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild isActive={item.isActive}>
                <a href={item.href}>
                  <item.icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  )
}

