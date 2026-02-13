import { NextResponse } from "next/server"

const API_URL = "http://31.220.107.8:8000"

export async function GET() {
  try {
    // Add a timeout to the fetch request
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

    try {
      const response = await fetch(API_URL, {
        signal: controller.signal,
        headers: {
          "Cache-Control": "no-cache",
        },
      })

      clearTimeout(timeoutId)
      const data = await response.json()
      return NextResponse.json(data)
    } catch (fetchError) {
      console.warn("API fetch failed, returning fallback health data:", fetchError)

      // Return a fallback response for demo purposes
      return NextResponse.json({
        ping: "pong!",
        status: "demo_mode",
        message: "Running in demo mode with simulated data",
      })
    }
  } catch (error) {
    console.error("Health check error:", error)
    return NextResponse.json(
      {
        error: "Failed to connect to Nuclei API",
        status: "offline",
        demo_mode: true,
      },
      { status: 200 },
    ) // Return 200 instead of 500 to prevent UI errors
  }
}

