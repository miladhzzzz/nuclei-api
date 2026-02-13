"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ExternallyExposedAssets } from "../components/ExternallyExposedAssets"
import { AttackSurfaceMap } from "../components/AttackSurfaceMap"
import { AssetsBySeverity } from "../components/AssetsBySeverity"
import { UnsanctionedServices } from "../components/UnsanctionedServices"
import { HostsList } from "../components/HostsList"
import { RealTimeThreatIntelligence } from "../components/RealTimeThreatIntelligence"

export default function AssetsPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-8">Assets Overview</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Externally Exposed Assets</CardTitle>
          </CardHeader>
          <CardContent>
            <ExternallyExposedAssets />
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardContent className="pt-6">
            <AttackSurfaceMap />
          </CardContent>
        </Card>
      </div>

      <div className="mb-8">
        <RealTimeThreatIntelligence />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Assets by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <AssetsBySeverity />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Unsanctioned Exposed Services</CardTitle>
          </CardHeader>
          <CardContent>
            <UnsanctionedServices />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Hosts</CardTitle>
        </CardHeader>
        <CardContent>
          <HostsList />
        </CardContent>
      </Card>
    </div>
  )
}

