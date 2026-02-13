"use client"

import { LayoutDashboard, Shield, Database, Search, FileText, Settings } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar"
import { usePathname } from "next/navigation"
import Link from "next/link"

const mainNavItems = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard",
  },
  {
    title: "My Scans",
    icon: Search,
    href: "/",
  },
  {
    title: "Assets",
    icon: Database,
    href: "/assets",
  },
  {
    title: "Vulnerabilities",
    icon: Shield,
    href: "/vulnerabilities",
  },
  {
    title: "Reporting",
    icon: FileText,
    href: "/reporting",
  },
  {
    title: "Settings",
    icon: Settings,
    href: "/settings",
  },
]

export function MainNav() {
  const pathname = usePathname()

  return (
    <Sidebar className="border-r">
      <SidebarHeader className="border-b px-2 py-4">
        <h2 className="text-xl font-bold">Cybernod Scanner</h2>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {mainNavItems.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild isActive={pathname === item.href}>
                <Link href={item.href}>
                  <item.icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  )
}

