"use client"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CreateAlert } from "../components/CreateAlert"
import { ManageAlerts } from "../components/ManageAlerts"

export default function AlertsPage() {
  return (
    <div className="container mx-auto p-4">
      <Tabs defaultValue="create" className="w-full">
        <TabsList>
          <TabsTrigger value="manage">MANAGE ALERTS</TabsTrigger>
          <TabsTrigger value="create">CREATE ALERT</TabsTrigger>
        </TabsList>
        <TabsContent value="manage">
          <ManageAlerts />
        </TabsContent>
        <TabsContent value="create">
          <CreateAlert />
        </TabsContent>
      </Tabs>
    </div>
  )
}

