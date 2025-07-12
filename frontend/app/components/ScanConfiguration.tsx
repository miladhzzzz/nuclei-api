"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ChevronLeft, Upload } from "lucide-react"
import Link from "next/link"

interface ScanConfigurationProps {
  onSave: (config: any) => void
  onCancel: () => void
}

// Changed to default export
export default function ScanConfiguration({ onSave, onCancel }: ScanConfigurationProps) {
  return (
    <div className="container mx-auto p-4">
      <div className="mb-6">
        <Link href="#" className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1">
          <ChevronLeft className="h-4 w-4" />
          Back to Scan Templates
        </Link>
        <h1 className="text-2xl font-semibold mt-2">New Scan / Basic Network Scan</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-6">
        <div className="space-y-4">
          <div className="font-medium">BASIC</div>
          <nav className="space-y-1">
            <Button variant="ghost" className="w-full justify-start text-primary">
              General
            </Button>
            <Button variant="ghost" className="w-full justify-start text-muted-foreground">
              Schedule
            </Button>
            <Button variant="ghost" className="w-full justify-start text-muted-foreground">
              Notifications
            </Button>
          </nav>

          <div className="font-medium">DISCOVERY</div>
          <div className="font-medium">ASSESSMENT</div>
          <div className="font-medium">REPORT</div>
          <div className="font-medium">ADVANCED</div>
        </div>

        <div className="space-y-6">
          <Tabs defaultValue="settings">
            <TabsList>
              <TabsTrigger value="settings">Settings</TabsTrigger>
              <TabsTrigger value="credentials">Credentials</TabsTrigger>
              <TabsTrigger value="plugins">Plugins</TabsTrigger>
            </TabsList>

            <TabsContent value="settings" className="space-y-6">
              <div className="border rounded-lg p-6 space-y-6">
                <h2 className="text-lg font-medium">General Settings</h2>

                <div className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input id="name" placeholder="Enter scan name" />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea id="description" placeholder="Enter scan description" className="min-h-[100px]" />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="folder">Folder</Label>
                    <Select defaultValue="my-scans">
                      <SelectTrigger id="folder">
                        <SelectValue placeholder="Select folder" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="my-scans">My Scans</SelectItem>
                        <SelectItem value="shared">Shared Scans</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="targets">Targets</Label>
                    <Textarea
                      id="targets"
                      placeholder="Example: 192.168.1.1, 192.168.1.2-5, 192.168.1.0/24, hostname"
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label>Upload Targets</Label>
                    <Button variant="outline" className="w-fit">
                      <Upload className="mr-2 h-4 w-4" />
                      Add File
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <Label>Post-Processing</Label>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="live-results" />
                      <Label htmlFor="live-results" className="font-normal">
                        Live Results
                      </Label>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Enabling this option will identify potential issues discovered by plugins added during
                      updates—without actively scanning targets.
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="credentials">
              <div className="border rounded-lg p-6">
                <h2 className="text-lg font-medium">Credentials Configuration</h2>
                {/* Add credentials configuration fields here */}
              </div>
            </TabsContent>

            <TabsContent value="plugins">
              <div className="border rounded-lg p-6">
                <h2 className="text-lg font-medium">Plugins Configuration</h2>
                {/* Add plugins configuration fields here */}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      <div className="mt-6 flex items-center gap-2">
        <Button onClick={() => onSave({})}>Save</Button>
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  )
}

