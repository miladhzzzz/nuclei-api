"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Skull, Zap, ShieldAlert } from "lucide-react"

interface ThreatIntelligence {
  exploitedVulnerabilities: number
  activeExploits: number
  associatedAPTGroups: string[]
  malwareCampaigns: string[]
}

const dummyThreatIntelligence: ThreatIntelligence = {
  exploitedVulnerabilities: 5,
  activeExploits: 3,
  associatedAPTGroups: ["APT29", "Lazarus Group", "Fancy Bear"],
  malwareCampaigns: ["Emotet", "TrickBot", "Ryuk"],
}

export function RealTimeThreatIntelligence() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          Real-Time Threat Intelligence Integration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert variant="destructive">
          <Skull className="h-4 w-4" />
          <AlertTitle>Critical Threat Alert</AlertTitle>
          <AlertDescription>
            {dummyThreatIntelligence.exploitedVulnerabilities} of your critical vulnerabilities are currently being
            exploited in the wild by ransomware groups.
          </AlertDescription>
        </Alert>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Active Exploits</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dummyThreatIntelligence.activeExploits}</div>
              <p className="text-xs text-muted-foreground">Known exploits targeting your vulnerabilities</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Associated APT Groups</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dummyThreatIntelligence.associatedAPTGroups.map((group) => (
                  <Badge key={group} variant="secondary">
                    {group}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Active Malware Campaigns</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dummyThreatIntelligence.malwareCampaigns.map((campaign) => (
                <Alert key={campaign}>
                  <ShieldAlert className="h-4 w-4" />
                  <AlertTitle>{campaign}</AlertTitle>
                  <AlertDescription>
                    This malware campaign is actively exploiting vulnerabilities similar to those found in your assets.
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  )
}

