"use client"

import { useState } from "react"
import { DiscoveredDomains } from "../components/DiscoveredDomains"
import RiskiestAssets from "../components/RiskiestAssets"
import CriticalVulnerabilityAssets from "../components/CriticalVulnerabilityAssets"
import AssetsByOperatingSystem from "../components/AssetsByOperatingSystem"
import { IncidentPrediction } from "../components/IncidentPrediction"
import { SecurityGuidanceChatbot } from "../components/SecurityGuidanceChatbot"

export default function DashboardPage() {
  const [discoveredDomains] = useState([
    { subdomain: "blog.example.com", ipAddress: "192.168.1.10", isScanning: false, scanResults: "Not scanned" },
    { subdomain: "shop.example.com", ipAddress: "192.168.1.11", isScanning: false, scanResults: "Not scanned" },
    { subdomain: "api.example.com", ipAddress: "192.168.1.12", isScanning: false, scanResults: "Not scanned" },
    { subdomain: "mail.example.com", ipAddress: "192.168.1.13", isScanning: false, scanResults: "Not scanned" },
    { subdomain: "dev.example.com", ipAddress: "192.168.1.14", isScanning: false, scanResults: "Not scanned" },
  ])

  const riskiestAssets = [
    {
      address: "192.168.1.10",
      name: "localhost",
      os: "Linux",
      findings: {
        critical: 1,
        high: 2,
        medium: 3,
        info: 1,
      },
    },
    {
      address: "192.168.1.11",
      name: "localhost",
      os: "Linux",
      findings: {
        critical: 0,
        high: 2,
        medium: 1,
        info: 2,
      },
    },
    {
      address: "192.168.1.12",
      name: "DESKTOP-WXA",
      os: "Windows",
      findings: {
        critical: 1,
        high: 1,
        medium: 2,
        info: 1,
      },
    },
    {
      address: "192.168.1.13",
      name: "localhost",
      os: "Linux",
      findings: {
        critical: 0,
        high: 1,
        medium: 1,
        info: 0,
      },
    },
    {
      address: "192.168.1.14",
      name: "WIN-25A",
      os: "Windows",
      findings: {
        critical: 0,
        high: 0,
        medium: 2,
        info: 1,
      },
    },
  ]

  const handleToggleScan = (subdomain: string) => {
    console.log(`Toggle scan for ${subdomain}`)
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
        <div className="text-sm text-muted-foreground">
          <p>
            <strong>Company:</strong> Acme Corporation
          </p>
          <p>
            <strong>Domain:</strong> acme.com
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        <DiscoveredDomains domains={discoveredDomains} onToggleScan={handleToggleScan} />
        <RiskiestAssets assets={riskiestAssets} />
      </div>

      <div className="mb-8">
        <IncidentPrediction />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        <CriticalVulnerabilityAssets assets={riskiestAssets} />
        <AssetsByOperatingSystem assets={riskiestAssets} />
      </div>

      <div className="mb-8">
        <SecurityGuidanceChatbot />
      </div>
    </div>
  )
}

