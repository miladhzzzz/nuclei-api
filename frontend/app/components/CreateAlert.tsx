"use client"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { InfoIcon as InfoCircle } from "lucide-react"

const formSchema = z.object({
  enabled: z.boolean().default(true),
  alertName: z.string().min(1, "Alert name is required"),
  maxAlerts: z.string().optional(),
  scanEvents: z.object({
    started: z.boolean().default(false),
    stopped: z.boolean().default(false),
    failed: z.boolean().default(false),
    paused: z.boolean().default(false),
    resumed: z.boolean().default(false),
  }),
  vulnerabilityEvents: z.object({
    severity: z.string().default("any"),
    confirmed: z.boolean().default(false),
    unconfirmed: z.boolean().default(false),
    potential: z.boolean().default(false),
  }),
  notificationMethod: z.string().min(1, "Notification method is required"),
  recipientEmails: z.string().min(1, "At least one recipient email is required"),
  fromEmail: z.string().email("Invalid email address"),
  smtpServer: z.string().min(1, "SMTP server is required"),
  limitAlertText: z.boolean().default(false),
})

export function CreateAlert() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      enabled: true,
      scanEvents: {
        started: false,
        stopped: false,
        failed: false,
        paused: false,
        resumed: false,
      },
      vulnerabilityEvents: {
        severity: "any",
        confirmed: false,
        unconfirmed: false,
        potential: false,
      },
      notificationMethod: "smtp",
      limitAlertText: false,
    },
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    console.log(values)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>New Alert</CardTitle>
          <InfoCircle className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between">
                  <FormLabel>Enable</FormLabel>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="alertName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-green-600">Alert Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Failed and Paused Alert" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="maxAlerts"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Maximum Alerts to Send</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} />
                  </FormControl>
                  <FormDescription>alerts</FormDescription>
                </FormItem>
              )}
            />

            <div className="space-y-4">
              <FormLabel>Scan Events</FormLabel>
              <div className="flex gap-4">
                {["started", "stopped", "failed", "paused", "resumed"].map((event) => (
                  <FormField
                    key={event}
                    control={form.control}
                    name={`scanEvents.${event}` as any}
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-2">
                        <FormControl>
                          <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                        <FormLabel className="capitalize">{event}</FormLabel>
                      </FormItem>
                    )}
                  />
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <FormLabel>Vulnerability Events</FormLabel>
              <div className="flex items-center gap-4">
                <FormField
                  control={form.control}
                  name="vulnerabilityEvents.severity"
                  render={({ field }) => (
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Select severity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="any">Any severity</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
                {["confirmed", "unconfirmed", "potential"].map((type) => (
                  <FormField
                    key={type}
                    control={form.control}
                    name={`vulnerabilityEvents.${type}` as any}
                    render={({ field }) => (
                      <FormItem className="flex items-center gap-2">
                        <FormControl>
                          <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                        <FormLabel className="capitalize">{type}</FormLabel>
                      </FormItem>
                    )}
                  />
                ))}
              </div>
            </div>

            <FormField
              control={form.control}
              name="notificationMethod"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notification Method</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select notification method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="smtp">SMTP e-mail</SelectItem>
                      <SelectItem value="webhook">Webhook</SelectItem>
                      <SelectItem value="slack">Slack</SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="recipientEmails"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-red-500">Recipient E-mail Addresses</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Enter email addresses" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="fromEmail"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>From E-mail Address</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="smtpServer"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>SMTP Relay Server</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="limitAlertText"
              render={({ field }) => (
                <FormItem className="flex items-center gap-2">
                  <FormControl>
                    <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                  <FormLabel>Limit Alert Text</FormLabel>
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2">
              <Button type="submit">Save</Button>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

