"use client"

import { useState, useCallback } from "react"
import ScanForm from "./components/ScanForm"
import ScanResults from "./components/ScanResults"
import { RemediationCenter } from "./components/RemediationCenter"

interface Vulnerability {
  id: string
  type: string
  severity: "informational" | "low" | "medium" | "high"
  target: string
  details: string[]
}

export default function Home() {
  const [scanInfo, setScanInfo] = useState<{
    containerName: string
    scanId: string
    templates: string[]
    customTemplateFilename?: string
  } | null>(null)
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([])

  const handleScanComplete = useCallback(
    (containerName: string, scanId: string, templates: string[], customTemplateFilename?: string) => {
      console.log(
        `Scan completed. Container: ${containerName}, ScanID: ${scanId}, Templates: ${templates.join(
          ", ",
        )}, Custom Template: ${customTemplateFilename || "No"}`,
      )
      setScanInfo({ containerName, scanId, templates, customTemplateFilename })
    },
    [],
  )

  const handleVulnerabilitiesUpdate = useCallback((newVulnerabilities: Vulnerability[]) => {
    setVulnerabilities(newVulnerabilities)
  }, [])

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-8">My Scans</h1>

      <div className="max-w-2xl">
        <ScanForm onScanComplete={handleScanComplete} />
      </div>

      {scanInfo && (
        <div className="mt-8">
          <ScanResults
            scanIdentifier={scanInfo.containerName}
            scanId={scanInfo.scanId}
            templates={scanInfo.templates}
            customTemplateFilename={scanInfo.customTemplateFilename}
            onVulnerabilitiesUpdate={handleVulnerabilitiesUpdate}
          />
          <RemediationCenter vulnerabilities={vulnerabilities} />
        </div>
      )}
    </div>
  )
}

