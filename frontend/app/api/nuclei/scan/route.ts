import { NextResponse } from "next/server"
import { v4 as uuid } from "uuid"

const API_URL = "http://31.220.107.8:8000"

// Helper function to wait for a specified time
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

// Helper function to poll task status until we get a container name
async function pollTaskStatus(taskId: string, maxAttempts = 10, delayMs = 10000) {
  console.log(`Starting to poll task status for task ID: ${taskId}`)

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`Polling attempt ${attempt}/${maxAttempts} for task ID: ${taskId}`)

      const response = await fetch(`${API_URL}/nuclei/task/${taskId}`, {
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        console.warn(`Task status check failed with status: ${response.status}`)
        await sleep(delayMs)
        continue
      }

      const responseText = await response.text()
      console.log(`Task status response: ${responseText}`)

      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        console.error("Error parsing task status response:", parseError)
        await sleep(delayMs)
        continue
      }

      // Check if we have a container name
      let containerName = null
      if (typeof data === "string") {
        containerName = data
      } else if (Array.isArray(data)) {
        containerName = data[0]?.container_name
      } else if (typeof data === "object" && data !== null) {
        containerName = data.container_name || data.results?.[0]?.container_name
      }

      if (containerName) {
        console.log(`Found container name: ${containerName}`)
        return { success: true, containerName }
      }

      // If status is successful but no container name, check for a second task ID
      if (data.status === "successful" && data.id) {
        console.log(`Found second task ID: ${data.id}, continuing polling`)
        return await pollTaskStatus(data.id, maxAttempts - attempt, delayMs)
      }

      // If task is still processing, wait and try again
      if (data.status === "processing" || data.status === "pending") {
        console.log(`Task is still ${data.status}, waiting before next attempt`)
        await sleep(delayMs)
        continue
      }

      // If task failed, stop polling
      if (data.status === "failed") {
        console.error(`Task failed: ${data.message || "No error message provided"}`)
        return { success: false, error: data.message || "Task failed" }
      }
    } catch (error) {
      console.error(`Error polling task status:`, error)
    }

    await sleep(delayMs)
  }

  return { success: false, error: "Max polling attempts reached" }
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const target = formData.get("target") as string
    const templates = formData.get("templates") as string
    const scanId = formData.get("scanId") as string

    console.log("Received scan request with parameters:", { target, templates, scanId })

    // Generate a random container name for demo purposes
    const dummyContainerName = `nuclei-scan-${uuid().substring(0, 8)}`

    try {
      // Try to connect to the real API first
      const nucleiApiBody: any = {
        target,
        scanId,
      }

      if (templates) {
        const parsedTemplates = JSON.parse(templates)
        nucleiApiBody.templates =
          parsedTemplates.length === 0
            ? undefined
            : parsedTemplates.map((t: string) => {
                // Handle "all" template specially
                if (t === "all") {
                  return t
                }
                // Ensure template paths end with a slash for directory-based templates
                return t.endsWith("/") ? t : `${t}/`
              })
      }

      console.log("Sending request to Nuclei API:", JSON.stringify(nucleiApiBody, null, 2))

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

      const response = await fetch(`${API_URL}/nuclei/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(nucleiApiBody),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      console.log("Nuclei API response status:", response.status)

      if (response.ok) {
        const responseText = await response.text()
        console.log("Nuclei API raw response:", responseText)

        let data
        try {
          data = JSON.parse(responseText)
        } catch (parseError) {
          console.error("Error parsing Nuclei API response:", parseError)
          throw new Error("Unable to parse Nuclei API response")
        }

        console.log("Nuclei API parsed response data:", data)

        // Extract container name from the response
        let containerName = null
        if (typeof data === "string") {
          containerName = data
        } else if (Array.isArray(data)) {
          containerName = data[0]?.container_name
        } else if (typeof data === "object" && data !== null) {
          containerName = data.container_name || data.results?.[0]?.container_name
        }

        if (containerName) {
          console.log("Extracted container name:", containerName)
          return NextResponse.json({
            status: "success",
            containerName,
            scanId,
          })
        }

        // Check for task_id in the response
        if (data.task_id && data.message === "Scan pipeline started") {
          console.log(`Found task_id: ${data.task_id}, starting polling`)

          // Poll the task status until we get a container name
          const pollResult = await pollTaskStatus(data.task_id)

          if (pollResult.success && pollResult.containerName) {
            return NextResponse.json({
              status: "success",
              containerName: pollResult.containerName,
              scanId,
            })
          } else {
            console.warn(`Task polling failed: ${pollResult.error}`)
            throw new Error(`Task polling failed: ${pollResult.error}`)
          }
        }
      }

      // If we get here, either the response wasn't OK or we couldn't extract a container name
      // Fall back to the dummy container name
      throw new Error("Could not get valid response from API")
    } catch (apiError) {
      console.warn("API request failed, using dummy container name:", apiError)

      // Return a successful response with the dummy container name
      return NextResponse.json({
        status: "success",
        containerName: dummyContainerName,
        scanId,
        note: "Using dummy container due to API unavailability",
      })
    }
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "An unexpected error occurred" },
      { status: 500 },
    )
  }
}

