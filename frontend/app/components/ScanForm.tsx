"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Settings, Activity, Eye, ShieldAlert, AlertCircle, Loader2 } from "lucide-react"
import { v4 as uuid } from "uuid"
import { useEffect } from "react"
import ScanConfiguration from "./ScanConfiguration" // Import ScanConfiguration component

const CVE_TEMPLATES = "cves"
const VULNERABILITIES_TEMPLATES = "vulnerabilities"
const MISCONFIGURATIONS_TEMPLATES = "misconfiguration"
const EXPOSURES_TEMPLATES = "exposures"

const TEMPLATES = [
  {
    value: CVE_TEMPLATES,
    label: "CVE Detection",
    description: "Scan for known Common Vulnerabilities and Exposures (CVEs).",
    icon: ShieldAlert,
    className: "bg-red-500/10 hover:bg-red-500/20 [&_svg]:text-red-500",
  },
  {
    value: VULNERABILITIES_TEMPLATES,
    label: "Vulnerability Scan",
    description: "Detect common security vulnerabilities across various technologies.",
    icon: Activity,
    className: "bg-orange-500/10 hover:bg-orange-500/20 [&_svg]:text-orange-500",
  },
  {
    value: MISCONFIGURATIONS_TEMPLATES,
    label: "Misconfigurations",
    description: "Identify security misconfigurations in applications and services.",
    icon: Settings,
    className: "bg-blue-500/10 hover:bg-blue-500/20 [&_svg]:text-blue-500",
  },
  {
    value: EXPOSURES_TEMPLATES,
    label: "Sensitive Exposures",
    description: "Discover exposed sensitive information and services.",
    icon: Eye,
    className: "bg-purple-500/10 hover:bg-purple-500/20 [&_svg]:text-purple-500",
  },
]

const FULL_AUDIT = "all"
const BASIC_NETWORK_SCAN = "basic-network-scan"
const HOST_DISCOVERY = "host-discovery"
const WEB_APPLICATION_SCAN = "web-application-scan"

interface ScanFormProps {
  onScanComplete: (containerName: string, scanId: string, templates: string[], customTemplateFilename?: string) => void
}

export default function ScanForm({ onScanComplete }: ScanFormProps) {
  const [target, setTarget] = useState("")
  const [selectedTemplate, setSelectedTemplate] = useState<string>(FULL_AUDIT)
  const [customTemplateFile, setCustomTemplateFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [apiStatus, setApiStatus] = useState<"unknown" | "online" | "offline">("unknown")
  const [activeTab, setActiveTab] = useState<"predefined" | "aiCustom">("predefined")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [showConfiguration, setShowConfiguration] = useState(false)
  const [targetType, setTargetType] = useState<"url" | "ip-range">("ip-range")

  // AI Custom Template states
  const [templateName, setTemplateName] = useState("")
  const [vulnerabilityDescription, setVulnerabilityDescription] = useState("")
  const [generatedTemplate, setGeneratedTemplate] = useState("")
  const [aiTemplateTab, setAiTemplateTab] = useState<"create" | "preview">("create")
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    checkApiStatus()
  }, [])

  const checkApiStatus = async () => {
    try {
      const response = await fetch("api/nuclei/health")
      if (response.ok) {
        const data = await response.json()
        if (data.ping === "pong!") {
          setApiStatus("online")
          setError(null)

          // Check if we're in demo mode
          if (data.status === "demo_mode") {
            setError("API is in demo mode. Using simulated data for demonstration purposes.")
          }
          return
        }
      }
      setApiStatus("offline")
      setError("API is not responding correctly. Using simulated data for demonstration purposes.")
    } catch (error) {
      console.error("API check error:", error)
      setApiStatus("offline")
      setError("Failed to connect to the API. Using simulated data for demonstration purposes.")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    const scanId = uuid()

    try {
      const formData = new FormData()
      formData.append("target", target)
      formData.append("scanId", scanId)

      let apiEndpoint = "/api/nuclei/scan"

      if (activeTab === "predefined") {
        // If Full Audit is selected, use all available templates
        if (selectedTemplate === FULL_AUDIT) {
          const allTemplates = TEMPLATES.map((template) => template.value)
          formData.append("templates", JSON.stringify(allTemplates))
        } else {
          formData.append("templates", JSON.stringify([selectedTemplate]))
        }
      } else if (activeTab === "aiCustom" && generatedTemplate) {
        formData.append("template", generatedTemplate)
        apiEndpoint = "/api/nuclei/scan/custom"
      } else {
        throw new Error("No template selected")
      }

      console.log(
        `Submitting scan with ${activeTab === "predefined" ? "template" : "custom template"}:`,
        activeTab === "predefined"
          ? selectedTemplate === FULL_AUDIT
            ? "All templates"
            : selectedTemplate
          : generatedTemplate,
      )

      const response = await fetch(apiEndpoint, {
        method: "POST",
        body: formData,
      })

      const responseText = await response.text()
      console.log("Raw API response:", responseText)

      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        console.error("Error parsing API response:", parseError)
        throw new Error(`Invalid JSON response: ${responseText}`)
      }

      console.log("Parsed API response:", data)

      if (!response.ok) {
        throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`)
      }

      if (!data.containerName) {
        throw new Error("No container name received from the API")
      }

      onScanComplete(
        data.containerName,
        scanId,
        activeTab === "predefined"
          ? selectedTemplate === FULL_AUDIT
            ? TEMPLATES.map((t) => t.value)
            : [selectedTemplate]
          : [],
        activeTab === "aiCustom" ? templateName : undefined,
      )
    } catch (error) {
      console.error("Error details:", error)
      let errorMessage = "An unexpected error occurred"
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (typeof error === "string") {
        errorMessage = error
      } else if (error && typeof error === "object" && "message" in error) {
        errorMessage = String(error.message)
      }
      setError(`Error submitting scan: ${errorMessage}`)
      console.error("Scan submission error:", {
        scanType: activeTab,
        template: activeTab === "predefined" ? selectedTemplate : "N/A",
        target,
        error: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    //This function is no longer used but kept for potential future use.
  }

  const handleCustomTemplateClick = () => {
    //This function is no longer used but kept for potential future use.
  }

  const handleTemplateSelect = (template: string) => {
    if (template === VULNERABILITIES_TEMPLATES || template === MISCONFIGURATIONS_TEMPLATES) {
      setShowConfiguration(true)
    }
    setSelectedTemplate(template)
  }

  const handleGenerateTemplate = async () => {
    setIsGenerating(true)
    try {
      // Simulate AI template generation
      await new Promise((resolve) => setTimeout(resolve, 2000))
      const template = `id: ${templateName.toLowerCase().replace(/\s+/g, "-")}
info:
  name: ${templateName}
  author: AI Generator
  severity: medium
  description: ${vulnerabilityDescription}

requests:
  - method: GET
    path:
      - "{{BaseURL}}/"
    matchers:
      - type: word
        words:
          - "vulnerable_pattern"
        condition: and`

      setGeneratedTemplate(template)
      setAiTemplateTab("preview")
    } catch (error) {
      setError("Failed to generate template")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="target-type">Target Type</Label>
        <div className="flex space-x-2 mb-2">
          <Button
            type="button"
            variant={targetType === "ip-range" ? "default" : "outline"}
            size="sm"
            onClick={() => setTargetType("ip-range")}
          >
            IP Address/Range
          </Button>
          <Button
            type="button"
            variant={targetType === "url" ? "default" : "outline"}
            size="sm"
            onClick={() => setTargetType("url")}
          >
            URL
          </Button>
        </div>

        <Label htmlFor="target">Target {targetType === "url" ? "URL" : "IP Address/Range"}</Label>
        <Input
          id="target"
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder={
            targetType === "url" ? "https://example.com" : "192.168.1.1 or 192.168.1.0/24 or 192.168.1.1-192.168.1.254"
          }
          required
        />
        <p className="text-xs text-muted-foreground">
          {targetType === "url"
            ? "Enter a URL to scan (e.g., https://example.com)"
            : "Enter a single IP address, CIDR notation (e.g., 192.168.1.0/24), or a range (e.g., 192.168.1.1-192.168.1.254)"}
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(value: "predefined" | "aiCustom") => setActiveTab(value)}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="predefined">Predefined Templates</TabsTrigger>
          <TabsTrigger value="aiCustom">AI Generated Custom Template</TabsTrigger>
        </TabsList>

        <TabsContent value="predefined">
          <div>
            <Label className="mb-4 block">Select a template</Label>
            <div className="grid gap-4 md:grid-cols-2">
              {TEMPLATES.map((template) => {
                const Icon = template.icon
                return (
                  <Card
                    key={template.value}
                    className={cn(
                      "cursor-pointer transition-colors",
                      template.className,
                      selectedTemplate === template.value && "ring-2 ring-primary",
                    )}
                    onClick={() => handleTemplateSelect(template.value)}
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start space-x-4">
                        <div className="shrink-0">
                          <Icon className="h-8 w-8" />
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-medium leading-none">{template.label}</h3>
                          <p className="text-sm text-muted-foreground">{template.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="aiCustom">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <Tabs value={aiTemplateTab} onValueChange={(value: "create" | "preview") => setAiTemplateTab(value)}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="create">Create Template</TabsTrigger>
                    <TabsTrigger value="preview">Preview & Run</TabsTrigger>
                  </TabsList>

                  <TabsContent value="create" className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="template-name">Template Name</Label>
                      <Input
                        id="template-name"
                        placeholder="e.g., Custom SQL Injection Check"
                        value={templateName}
                        onChange={(e) => setTemplateName(e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="vulnerability-description">Describe the vulnerability you want to detect</Label>
                      <Textarea
                        id="vulnerability-description"
                        placeholder="e.g., Check for SQL injection vulnerabilities in login forms by testing various payloads..."
                        value={vulnerabilityDescription}
                        onChange={(e) => setVulnerabilityDescription(e.target.value)}
                        className="min-h-[100px]"
                      />
                    </div>

                    <Button
                      type="button"
                      onClick={handleGenerateTemplate}
                      disabled={isGenerating || !templateName || !vulnerabilityDescription}
                      className="w-full"
                    >
                      {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      {isGenerating ? "Generating Template..." : "Generate Template"}
                    </Button>
                  </TabsContent>

                  <TabsContent value="preview" className="space-y-4">
                    {generatedTemplate ? (
                      <pre className="rounded-lg bg-zinc-950 p-4 text-sm text-white overflow-auto">
                        <code>{generatedTemplate}</code>
                      </pre>
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        Generate a template first to preview it here
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {showConfiguration && (
        <ScanConfiguration
          onSave={(config) => {
            console.log("Scan configuration saved:", config)
            // Handle the configuration save
          }}
          onCancel={() => setShowConfiguration(false)}
        />
      )}
      <div className="flex space-x-2">
        <Button
          type="submit"
          disabled={isLoading || apiStatus === "offline" || (activeTab === "aiCustom" && !generatedTemplate)}
        >
          {isLoading ? "Scanning..." : "Start Scan"}
        </Button>
        <Button type="button" onClick={checkApiStatus} variant="outline">
          Check API Status
        </Button>
      </div>
      {error && (
        <Alert variant={apiStatus === "offline" ? "warning" : "destructive"}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>{apiStatus === "offline" ? "Demo Mode Active" : "Error"}</AlertTitle>
          <AlertDescription>
            {error}
            {apiStatus === "offline" && (
              <>
                <br />
                <span className="block mt-2 text-sm">
                  The application is running in demo mode with simulated data. All functionality will work, but no
                  actual scans will be performed.
                </span>
              </>
            )}
            {apiStatus !== "offline" && error && error.includes("API is in demo mode") && (
              <>
                <br />
                <span className="block mt-2 text-sm">
                  The application is running in demo mode with simulated data. All functionality will work, but no
                  actual scans will be performed.
                </span>
              </>
            )}
            {apiStatus !== "offline" && error && !error.includes("API is in demo mode") && (
              <>
                <br />
                <span className="block mt-2 text-sm">
                  Please check the browser console for more details. If the issue persists, contact support with the
                  following information:
                  <br />- Scan type: {activeTab === "predefined" ? "Predefined template" : "AI generated template"}
                  <br />- Selected template: {activeTab === "predefined" ? selectedTemplate : "N/A"}
                  <br />- Target URL: {target}
                  <br />- Error message: {error}
                </span>
              </>
            )}
          </AlertDescription>
        </Alert>
      )}
    </form>
  )
}

