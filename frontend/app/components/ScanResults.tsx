"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Loader2, CheckCircle, AlertTriangle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Vulnerabilities } from "./Vulnerabilities"
import { TemplatesList } from "./TemplatesList"
import { Badge } from "@/components/ui/badge"

interface ScanResultsProps {
  scanIdentifier: string
  scanId: string
  templates: string[]
  customTemplateFilename?: string
  onVulnerabilitiesUpdate: (vulnerabilities: Vulnerability[]) => void
}

interface LogEntry {
  source: string
  log: string
  timestamp: number
}

interface Vulnerability {
  id: string
  type: string
  protocol: string
  severity: "informational" | "low" | "medium" | "high"
  target: string
  details: string[]
}

const MAX_LOOP_COUNT = 5
const LOG_WINDOW_SIZE = 20

const FULL_AUDIT = "full_audit"
const BASIC_NETWORK_SCAN = "basic-network-scan"

const AVAILABLE_TEMPLATES = [FULL_AUDIT, BASIC_NETWORK_SCAN]

const log = (message: string, data?: any) => {
  console.log(`[ScanResults] ${message}`, data)
}

export default function ScanResults({
  scanIdentifier,
  scanId,
  templates,
  customTemplateFilename,
  onVulnerabilitiesUpdate,
}: ScanResultsProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [rawLogs, setRawLogs] = useState<string[]>([])
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [progress, setProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState("Initializing...")
  const [loopDetected, setLoopDetected] = useState(false)
  const [scanComplete, setScanComplete] = useState(false)
  const [noResultsFound, setNoResultsFound] = useState(false)
  const [usedTemplates, setUsedTemplates] = useState<Set<string>>(new Set())

  const logContainerRef = useRef<HTMLPreElement>(null)
  const progressRef = useRef(0)
  const lastUpdateTimeRef = useRef(Date.now())
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastLogTimestampRef = useRef<number | null>(null)
  const processedResultsRef = useRef<Set<string>>(new Set())
  const logWindowRef = useRef<string[]>([])
  const uniqueLogsCountRef = useRef<number>(0)
  const totalLogsCountRef = useRef<number>(0)
  const fetchAttemptsRef = useRef<number>(0)
  const maxFetchAttempts = 5

  const updateProgress = useCallback((newProgress: number, message: string) => {
    if (newProgress > progressRef.current) {
      progressRef.current = newProgress
      setProgress(newProgress)
      setStatusMessage(message)
      lastUpdateTimeRef.current = Date.now()
    }
  }, [])

  const processLogForProgress = useCallback(
    (log: string) => {
      if (log.includes("v3.3.8") || log.includes("projectdiscovery.io")) {
        updateProgress(5, "Cybernod initialized")
      } else if (log.includes("nuclei-templates are not installed")) {
        updateProgress(10, "Starting template installation")
      } else if (log.includes("downloading nuclei-templates")) {
        updateProgress(20, "Downloading templates")
      } else if (log.includes("nuclei-templates installed")) {
        updateProgress(30, "Templates installed")
      } else if (log.includes("[INF] Current nuclei version")) {
        updateProgress(60, "Initializing scan")
      } else if (log.includes("[INF] Current engine version")) {
        updateProgress(70, "Engine initialized")
      } else if (log.includes("[INF] Creating runners")) {
        updateProgress(80, "Creating scan runners")
      } else if (log.includes("[INF] Using")) {
        updateProgress(85, "Starting vulnerability scan")
      } else if (log.includes("[INF] New Scan Started")) {
        updateProgress(90, "Scan in progress")
      } else if (log.includes("[INF] Found")) {
        updateProgress(95, "Processing results")
      } else if (log.includes("scan completed") || log.includes("No results found")) {
        updateProgress(100, "Scan completed")
        setScanComplete(true)
        setIsLoading(false)
        if (log.includes("No results found")) {
          setNoResultsFound(true)
        }
      }
    },
    [updateProgress],
  )

  const detectLoop = useCallback((log: string) => {
    logWindowRef.current.push(log)
    if (logWindowRef.current.length > LOG_WINDOW_SIZE) {
      logWindowRef.current.shift()
    }

    totalLogsCountRef.current++
    uniqueLogsCountRef.current = new Set(logWindowRef.current).size

    const repetitionRatio = uniqueLogsCountRef.current / LOG_WINDOW_SIZE
    const isLooping = repetitionRatio < 0.5 && totalLogsCountRef.current > LOG_WINDOW_SIZE * 2

    if (isLooping) {
      setLoopDetected(true)
      setError("Scan loop detected. The scan might be stuck.")
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  const processVulnerability = useCallback((log: string) => {
    const match = log.match(/\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*?) (.*)/)
    if (match) {
      const [, type, protocol, severity, target, details] = match
      const resultKey = `${type}-${protocol}-${severity}-${target}-${details}`

      if (!processedResultsRef.current.has(resultKey)) {
        processedResultsRef.current.add(resultKey)

        const id = `${type}-${target}-${Date.now()}`
        const newVulnerability: Vulnerability = {
          id,
          type,
          protocol,
          severity: severity === "info" ? "informational" : (severity as "low" | "medium" | "high"),
          target,
          details: [details],
        }
        setVulnerabilities((prevVulns) => {
          const existingVuln = prevVulns.find((v) => v.type === type && v.target === target)
          if (existingVuln) {
            return prevVulns.map((v) => (v.id === existingVuln.id ? { ...v, details: [...v.details, details] } : v))
          } else {
            return [...prevVulns, newVulnerability]
          }
        })
      }
    }
  }, [])

  const processLogs = useCallback(
    (newLogs: string[]) => {
      newLogs.forEach((log) => {
        const currentTimestamp = Date.now()
        setLogs((prevLogs) => [
          ...prevLogs,
          {
            source: "stdout",
            log: log.trim(),
            timestamp: currentTimestamp,
          },
        ])
        setRawLogs((prevRawLogs) => [...prevRawLogs, log])

        AVAILABLE_TEMPLATES.forEach((template) => {
          if (log.toLowerCase().includes(template.toLowerCase())) {
            setUsedTemplates((prev) => new Set(prev).add(template))
          }
        })

        processLogForProgress(log)
        detectLoop(log)
        processVulnerability(log)
      })
    },
    [processLogForProgress, detectLoop, processVulnerability],
  )

  const fetchLogs = useCallback(async () => {
    if (loopDetected || scanComplete) return

    try {
      fetchAttemptsRef.current += 1
      log(`Fetching logs (attempt ${fetchAttemptsRef.current}/${maxFetchAttempts})`, {
        scanIdentifier,
        scanId,
        templates,
      })

      // Encode templates properly for URL
      const templatesParam = templates.join(",")
      const url = `/api/nuclei/scan/${scanIdentifier}/logs?scanId=${scanId}&templates=${encodeURIComponent(templatesParam)}`
      log(`Fetching logs from URL: ${url}`)

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

      try {
        const response = await fetch(url, {
          signal: controller.signal,
          headers: {
            Accept: "text/plain",
            "Cache-Control": "no-cache",
          },
        })

        clearTimeout(timeoutId)
        log(`API response status: ${response.status}`)

        if (!response.ok) {
          const errorText = await response.text()
          log(`Error response from API: ${errorText}`)
          throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
        }

        // Reset fetch attempts on successful fetch
        fetchAttemptsRef.current = 0

        // Check if response body exists
        if (!response.body) {
          throw new Error("Response body is null")
        }

        const reader = response.body.getReader()
        let receivedData = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          receivedData = true
          const chunk = new TextDecoder().decode(value)
          log(`Received chunk: ${chunk.substring(0, 100)}...`)
          const lines = chunk.split("\n").filter(Boolean)

          if (lines.length > 0) {
            log(`Processing ${lines.length} new log entries`)
            processLogs(lines)
          }
        }

        if (!receivedData) {
          log("No data received from the logs endpoint")
        }

        setIsLoading(false)
      } catch (fetchError) {
        clearTimeout(timeoutId)
        throw fetchError
      }
    } catch (error) {
      log("Error fetching logs:", error)

      // If we've reached max attempts, set error state
      if (fetchAttemptsRef.current >= maxFetchAttempts) {
        let errorMessage = "Maximum retry attempts reached while fetching logs"
        if (error instanceof Error) {
          errorMessage = `${error.name}: ${error.message}`
          log("Error stack:", error.stack)
        } else if (typeof error === "string") {
          errorMessage = error
        } else if (error && typeof error === "object" && error !== null) {
          errorMessage = String(error)
        }
        setError(`Error fetching logs: ${errorMessage}`)
        setIsLoading(false)
        return
      }

      // Otherwise, we'll retry on the next interval
      log(`Will retry on next interval (attempt ${fetchAttemptsRef.current}/${maxFetchAttempts})`)
    }
  }, [scanIdentifier, scanId, templates, processLogs, loopDetected, scanComplete])

  useEffect(() => {
    fetchLogs()
    const intervalId = setInterval(fetchLogs, 5000)
    pollingIntervalRef.current = intervalId

    return () => {
      clearInterval(intervalId)
    }
  }, [fetchLogs])

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs])

  useEffect(() => {
    onVulnerabilitiesUpdate(vulnerabilities)
  }, [vulnerabilities, onVulnerabilitiesUpdate])

  const handleRetry = useCallback(() => {
    setLogs([])
    setRawLogs([])
    setVulnerabilities([])
    setError(null)
    setProgress(0)
    setStatusMessage("Initializing...")
    setLoopDetected(false)
    setScanComplete(false)
    setNoResultsFound(false)
    setUsedTemplates(new Set())
    progressRef.current = 0
    lastUpdateTimeRef.current = Date.now()
    lastLogTimestampRef.current = null
    processedResultsRef.current.clear()
    logWindowRef.current = []
    uniqueLogsCountRef.current = 0
    totalLogsCountRef.current = 0
    fetchAttemptsRef.current = 0
    setIsLoading(true)
    fetchLogs()
  }, [fetchLogs])

  return (
    <div className="space-y-4">
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Scan Results
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {scanComplete && <CheckCircle className="h-4 w-4 text-green-500" />}
          </CardTitle>
          <p className="text-sm text-muted-foreground">Scan ID: {scanId}</p>
          <p className="text-sm text-muted-foreground">Scan Identifier: {scanIdentifier}</p>
          <p className="text-sm text-muted-foreground">
            Templates:{" "}
            {customTemplateFilename
              ? "Custom Template"
              : templates.includes(FULL_AUDIT)
                ? "Full Audit"
                : templates.includes(BASIC_NETWORK_SCAN)
                  ? "Basic Network Scan"
                  : templates.join(", ")}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{statusMessage}</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                {error}
                <div className="mt-2 text-sm">
                  If this error persists, please check your network connection and try again. If the issue continues,
                  contact support with the following information:
                </div>
                <ul className="mt-2 text-sm list-disc list-inside">
                  <li>Scan ID: {scanId}</li>
                  <li>Scan Identifier: {scanIdentifier}</li>
                  <li>Templates: {templates.join(", ")}</li>
                  <li>Error message: {error}</li>
                </ul>
                <Button onClick={handleRetry} className="mt-2" variant="outline">
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          )}
          {loopDetected && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                A potential loop has been detected in the scan process. The scan might be stuck.
              </AlertDescription>
            </Alert>
          )}
          {noResultsFound && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                The scan has completed, but no vulnerabilities were found. This could mean that the target is secure, or
                that the selected templates did not match any potential vulnerabilities.
              </AlertDescription>
            </Alert>
          )}
          {scanComplete && (
            <Alert variant={usedTemplates.size === templates.length ? "default" : "warning"}>
              <AlertDescription>
                {usedTemplates.size === templates.length ? (
                  <>
                    <CheckCircle className="inline-block mr-2 h-4 w-4 text-green-500" />
                    All selected templates were successfully used in this scan.
                  </>
                ) : (
                  <>
                    <AlertTriangle className="inline-block mr-2 h-4 w-4 text-yellow-500" />
                    Not all selected templates were used in this scan. This might be due to compatibility issues or
                    errors during the scan process. Templates used: {Array.from(usedTemplates).join(", ")}
                  </>
                )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Vulnerabilities vulnerabilities={vulnerabilities} />
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Templates Used</CardTitle>
        </CardHeader>
        <CardContent>
          {Array.from(usedTemplates).length === 0 ? (
            <p className="text-muted-foreground">No templates have been used in this scan yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {Array.from(usedTemplates).map((template) => (
                <Badge key={template} variant="secondary">
                  {template}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <TemplatesList templates={Array.from(usedTemplates)} />

      {customTemplateFilename && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Custom Template Used</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Filename: {customTemplateFilename}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Scan Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <h3 className="text-lg font-semibold mb-2">Processed Logs</h3>
          <pre
            ref={logContainerRef}
            className="bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto max-h-[300px] overflow-y-auto font-mono text-sm whitespace-pre"
          >
            {logs.map((entry, index) => (
              <div
                key={index}
                className={`${
                  entry.source === "stderr"
                    ? "text-red-500 dark:text-red-400"
                    : entry.log.includes("[INF]")
                      ? "text-green-600 dark:text-green-400"
                      : entry.log.includes("[WRN]")
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-foreground"
                }`}
              >
                {new Date(entry.timestamp).toISOString()} - {entry.log}
              </div>
            ))}
            {logs.length === 0 && !isLoading && (
              <div className="text-muted-foreground">Waiting for scan to start...</div>
            )}
          </pre>
          <h3 className="text-lg font-semibold mt-4 mb-2">Raw Logs</h3>
          <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto max-h-[300px] overflow-y-auto font-mono text-sm whitespace-pre">
            {rawLogs.map((log, index) => (
              <div key={index} className="text-foreground">
                {log}
              </div>
            ))}
            {rawLogs.length === 0 && !isLoading && (
              <div className="text-muted-foreground">No raw logs available yet...</div>
            )}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

