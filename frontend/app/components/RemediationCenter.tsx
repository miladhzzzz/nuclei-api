import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from "lucide-react"

interface Vulnerability {
  id: string
  type: string
  severity: "informational" | "low" | "medium" | "high"
  target: string
  details: string[]
}

interface RemediationCenterProps {
  vulnerabilities: Vulnerability[]
}

const severityIcons = {
  informational: Info,
  low: AlertCircle,
  medium: AlertTriangle,
  high: ShieldAlert,
}

const severityColors = {
  informational: "bg-blue-500",
  low: "bg-yellow-500",
  medium: "bg-orange-500",
  high: "bg-red-500",
}

// This function simulates AI-generated recommendations
const generateRecommendation = (vulnerability: Vulnerability): string => {
  const recommendations = {
    informational: "Monitor this finding and consider implementing additional security measures if necessary.",
    low: "Address this vulnerability as part of your regular maintenance cycle. Consider implementing security best practices.",
    medium:
      "Prioritize fixing this vulnerability in the near term. Implement security patches or configuration changes as soon as possible.",
    high: "Immediate action required. This vulnerability poses a significant risk and should be addressed as soon as possible. Consider temporary mitigations if a permanent fix is not immediately available.",
  }

  return `${recommendations[vulnerability.severity]} For ${vulnerability.type}, consider the following steps:
1. Review your current configuration and compare it against security best practices.
2. Check for any available patches or updates that address this specific vulnerability.
3. Implement access controls and limit exposure of the affected systems or services.
4. Conduct a thorough security audit to identify any related vulnerabilities.
5. Develop and implement a remediation plan with clear timelines and responsible parties.`
}

export function RemediationCenter({ vulnerabilities }: RemediationCenterProps) {
  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Remediation Center</CardTitle>
        <CardDescription>AI-powered recommendations to address identified vulnerabilities</CardDescription>
      </CardHeader>
      <CardContent>
        {vulnerabilities.length === 0 ? (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>No vulnerabilities found</AlertTitle>
            <AlertDescription>
              Great job! No vulnerabilities were detected in the scan. Keep up the good security practices!
            </AlertDescription>
          </Alert>
        ) : (
          <Accordion type="single" collapsible className="w-full">
            {vulnerabilities.map((vuln) => {
              const Icon = severityIcons[vuln.severity]
              return (
                <AccordionItem value={vuln.id} key={vuln.id}>
                  <AccordionTrigger>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <span>{vuln.type}</span>
                      <Badge className={severityColors[vuln.severity]}>
                        {vuln.severity.charAt(0).toUpperCase() + vuln.severity.slice(1)}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      <p>
                        <strong>Target:</strong> {vuln.target}
                      </p>
                      <p>
                        <strong>Details:</strong>
                      </p>
                      <ul className="list-disc pl-5 space-y-1">
                        {vuln.details.map((detail, index) => (
                          <li key={index}>{detail}</li>
                        ))}
                      </ul>
                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>AI Recommendation</AlertTitle>
                        <AlertDescription className="whitespace-pre-wrap">
                          {generateRecommendation(vuln)}
                        </AlertDescription>
                      </Alert>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )
            })}
          </Accordion>
        )}
      </CardContent>
    </Card>
  )
}

