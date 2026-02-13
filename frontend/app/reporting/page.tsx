"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ExecutiveSummary } from "../components/reporting/ExecutiveSummary"
import { FullReport } from "../components/reporting/FullReport"

export default function ReportingPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-8">Reports</h1>

      <Tabs defaultValue="executive" className="space-y-4">
        <TabsList>
          <TabsTrigger value="executive">Executive Summary</TabsTrigger>
          <TabsTrigger value="full">Full Report</TabsTrigger>
        </TabsList>

        <TabsContent value="executive">
          <ExecutiveSummary />
        </TabsContent>

        <TabsContent value="full">
          <FullReport />
        </TabsContent>
      </Tabs>
    </div>
  )
}

