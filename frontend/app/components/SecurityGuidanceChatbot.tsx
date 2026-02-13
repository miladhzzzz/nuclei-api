"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

const dummyResponses: { [key: string]: string } = {
  "How critical is this vulnerability?":
    "Based on the information provided, this vulnerability appears to be of high criticality. It could potentially allow unauthorized access to sensitive data or system compromise. Immediate action is recommended to mitigate the risk.",
  "What is the best fix for this issue?":
    "The best fix for this issue would be to update the affected software to the latest patched version. If that's not immediately possible, consider implementing a web application firewall (WAF) as a temporary mitigation. Always follow the principle of least privilege and ensure all systems are properly hardened.",
  "Are there known exploits in the wild for this vulnerability?":
    "Yes, there are known exploits in the wild for this vulnerability. It has been actively exploited by threat actors. It's crucial to apply the necessary patches or mitigations as soon as possible to protect your systems from potential attacks.",
  "How can I protect my system from this vulnerability?":
    "To protect your system from this vulnerability, you should: 1) Apply the latest security patches, 2) Implement network segmentation, 3) Use strong authentication methods, 4) Regularly monitor and audit your systems, and 5) Educate your team about security best practices.",
  "What are the potential impacts of this vulnerability?":
    "The potential impacts of this vulnerability include: unauthorized data access, system compromise, data theft, installation of malware, and potential use of your system as a launchpad for further attacks. In severe cases, it could lead to significant financial losses and damage to your organization's reputation.",
}

export function SecurityGuidanceChatbot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    }

    setMessages((prevMessages) => [...prevMessages, userMessage])
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          dummyResponses[input] ||
          "I'm sorry, I don't have specific information about that. Could you provide more context or ask a different question?",
      }
      setMessages((prevMessages) => [...prevMessages, aiResponse])
    }, 1000)
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>AI Security Guidance Assistant</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 flex ${message.role === "assistant" ? "justify-start" : "justify-end"}`}
            >
              {message.role === "assistant" && (
                <Avatar className="mr-2">
                  <AvatarImage src="/ai-assistant.png" alt="AI" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              )}
              <div
                className={`rounded-lg p-2 ${
                  message.role === "assistant" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                {message.content}
              </div>
              {message.role === "user" && (
                <Avatar className="ml-2">
                  <AvatarImage src="/user-avatar.png" alt="User" />
                  <AvatarFallback>U</AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </ScrollArea>
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about security vulnerabilities..."
          />
          <Button type="submit">Send</Button>
        </form>
      </CardContent>
    </Card>
  )
}

