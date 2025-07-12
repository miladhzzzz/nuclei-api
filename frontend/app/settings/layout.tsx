"use client"

import type React from "react"

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Link from "next/link"
import { usePathname } from "next/navigation"

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your account settings and preferences.</p>
      </div>
      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <aside className="-mx-4 lg:w-1/5">
          <Tabs defaultValue={pathname.split("/")[2] || "general"} className="w-full" orientation="vertical">
            <TabsList className="flex flex-col items-start justify-start">
              <TabsTrigger value="general" asChild>
                <Link href="/settings" className="w-full">
                  General
                </Link>
              </TabsTrigger>
              <TabsTrigger value="alerts" asChild>
                <Link href="/settings/alerts" className="w-full">
                  Alerts
                </Link>
              </TabsTrigger>
              <TabsTrigger value="security" asChild>
                <Link href="/settings/security" className="w-full">
                  Security
                </Link>
              </TabsTrigger>
              <TabsTrigger value="api" asChild>
                <Link href="/settings/api" className="w-full">
                  API
                </Link>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </aside>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  )
}

