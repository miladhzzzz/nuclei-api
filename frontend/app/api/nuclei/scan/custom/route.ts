import { NextResponse } from "next/server"
import { v4 as uuid } from "uuid"

const API_URL = "http://31.220.107.8:8000"

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const target = formData.get("target") as string
    const templateFile = formData.get("template_file") as File | null
    const templateYaml = formData.get("template_yaml") as string | null
    const scanId = formData.get("scanId") as string

    if (!target || (!templateFile && !templateYaml)) {
      return NextResponse.json({ error: "Missing target or template" }, { status: 400 })
    }

    console.log("Received custom scan request with parameters:", {
      target,
      templateFile: templateFile?.name,
      templateYaml: templateYaml ? "Provided" : "Not provided",
      scanId,
    })

    // Generate a random container name for demo purposes
    const dummyContainerName = `nuclei-custom-scan-${uuid().substring(0, 8)}`

    try {
      // Try to connect to the real API first
      const apiFormData = new FormData()
      apiFormData.append("target", target)
      if (templateFile) {
        apiFormData.append("template_file", templateFile)
      } else if (templateYaml) {
        apiFormData.append("template_yaml", templateYaml)
      }
      apiFormData.append("scanId", scanId)

      console.log("Sending request to Nuclei API for custom template scan")

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

      const response = await fetch(`${API_URL}/nuclei/scan/custom`, {
        method: "POST",
        body: apiFormData,
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

        return NextResponse.json({
          status: "success",
          ...data,
          scanId,
        })
      }

      // If we get here, the response wasn't OK
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
    console.error("Custom scan proxy error:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "An unexpected error occurred" },
      { status: 500 },
    )
  }
}

