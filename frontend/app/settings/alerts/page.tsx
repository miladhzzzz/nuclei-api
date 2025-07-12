"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CreateAlert } from "../../components/CreateAlert"
import { ManageAlerts } from "../../components/ManageAlerts"
import { Card } from "@/components/ui/card"

export default function AlertsSettingsPage() {
  return (
    <Card>
      <Tabs defaultValue="manage" className="w-full">
        <TabsList className="w-full justify-start border-b rounded-none px-6 pt-2">
          <TabsTrigger value="manage">MANAGE ALERTS</TabsTrigger>
          <TabsTrigger value="create">CREATE ALERT</TabsTrigger>
        </TabsList>

        <TabsContent value="manage" className="p-6">
          <ManageAlerts />
        </TabsContent>

        <TabsContent value="create" className="p-6">
          <CreateAlert />
        </TabsContent>
      </Tabs>
    </Card>
  )
}

