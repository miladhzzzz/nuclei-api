import type React from "react"
import "./globals.css"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { MainNav } from "./components/MainNav"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Nuclei Automated AI Scanner",
  description: "Frontend for Nuclei AI vulnerability scanning",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SidebarProvider>
          <div className="flex min-h-screen">
            <MainNav />
            <SidebarInset>{children}</SidebarInset>
          </div>
        </SidebarProvider>
      </body>
    </html>
  )
}

