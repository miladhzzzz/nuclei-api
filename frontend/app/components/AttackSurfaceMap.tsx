"use client"

import type React from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Minus, Plus } from "lucide-react"
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from "react-simple-maps"
import { useState } from "react"

interface CountryData {
  name: string
  hosts: number
  newHosts: number
  coordinates: [number, number]
  type: "primary" | "secondary"
}

const countryData: CountryData[] = [
  {
    name: "United States",
    hosts: 215,
    newHosts: 20,
    coordinates: [-95.7129, 37.0902],
    type: "primary",
  },
  {
    name: "Japan",
    hosts: 37,
    newHosts: 5,
    coordinates: [139.6917, 35.6895],
    type: "primary",
  },
  {
    name: "Germany",
    hosts: 29,
    newHosts: 2,
    coordinates: [13.405, 52.52],
    type: "secondary",
  },
  {
    name: "India",
    hosts: 27,
    newHosts: 5,
    coordinates: [77.209, 28.6139],
    type: "secondary",
  },
  {
    name: "United Kingdom",
    hosts: 25,
    newHosts: 2,
    coordinates: [-0.1276, 51.5074],
    type: "secondary",
  },
  {
    name: "Brazil",
    hosts: 24,
    newHosts: 1,
    coordinates: [-47.8645, -15.7942],
    type: "primary",
  },
]

function getMarkerSize(hosts: number): number {
  // Scale marker size based on number of hosts
  const baseSize = 3
  const scale = Math.log(hosts) / Math.log(10) // logarithmic scaling
  return baseSize * (1 + scale)
}

export function AttackSurfaceMap() {
  const [zoom, setZoom] = useState(1)
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [tooltipContent, setTooltipContent] = useState<string | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null)

  const handleCountryClick = (country: CountryData) => {
    setSelectedCountry(selectedCountry === country.name ? null : country.name)
  }

  const handleMarkerMouseEnter = (event: React.MouseEvent, country: CountryData) => {
    const content = `${country.name}\nHosts: ${country.hosts}${country.newHosts > 0 ? `\nNew: ${country.newHosts}` : ""}`
    setTooltipContent(content)
    setTooltipPosition({ x: event.clientX, y: event.clientY })
  }

  const handleMarkerMouseLeave = () => {
    setTooltipContent(null)
    setTooltipPosition(null)
  }

  return (
    <div className="flex gap-4">
      <div className="w-64 shrink-0 space-y-4">
        <div>
          <h3 className="font-semibold mb-4">Host Locations</h3>
          <div className="space-y-2">
            <h4 className="text-sm text-muted-foreground">Hosts by Country</h4>
            <div className="space-y-2">
              {countryData.map((country) => (
                <div
                  key={country.name}
                  className={`flex items-center justify-between text-sm p-2 rounded-md cursor-pointer transition-colors ${
                    selectedCountry === country.name ? "bg-muted" : "hover:bg-muted/50"
                  }`}
                  onClick={() => handleCountryClick(country)}
                >
                  <div className="flex items-center gap-2">
                    <span>{country.name}</span>
                    {country.newHosts > 0 && (
                      <Badge variant="outline" className="bg-orange-500/10 text-orange-500 border-orange-500/20">
                        {country.newHosts} NEW
                      </Badge>
                    )}
                  </div>
                  <span className="font-medium">{country.hosts}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="relative flex-1">
        <div className="absolute right-2 top-2 z-10 flex flex-col gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setZoom(Math.min(zoom + 0.5, 4))}
            className="h-8 w-8 bg-background"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setZoom(Math.max(zoom - 0.5, 1))}
            className="h-8 w-8 bg-background"
          >
            <Minus className="h-4 w-4" />
          </Button>
        </div>

        <ComposableMap
          projection="geoEquirectangular"
          style={{
            background: `url('https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-yGlB0IIvugL4WIvk1wCFOML25DAPKn.png')`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
        >
          <ZoomableGroup zoom={zoom} maxZoom={4} minZoom={1}>
            <Geographies geography="/world-110m.json">
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill="transparent"
                    stroke="transparent"
                    strokeWidth={0}
                    style={{
                      default: { outline: "none" },
                      hover: { outline: "none" },
                      pressed: { outline: "none" },
                    }}
                  />
                ))
              }
            </Geographies>
            {countryData.map((country) => (
              <Marker
                key={country.name}
                coordinates={country.coordinates}
                onMouseEnter={(e) => handleMarkerMouseEnter(e, country)}
                onMouseLeave={handleMarkerMouseLeave}
                onClick={() => handleCountryClick(country)}
              >
                <circle
                  r={getMarkerSize(country.hosts)}
                  fill={country.type === "primary" ? "#F97316" : "#3B82F6"}
                  fillOpacity={selectedCountry === country.name ? 1 : 0.8}
                  stroke={selectedCountry === country.name ? "#FFF" : "rgba(255,255,255,0.3)"}
                  strokeWidth={2}
                  className="cursor-pointer transition-all duration-200 drop-shadow-lg"
                  style={{
                    transform: selectedCountry === country.name ? "scale(1.2)" : "scale(1)",
                  }}
                />
              </Marker>
            ))}
          </ZoomableGroup>
        </ComposableMap>

        {tooltipContent && tooltipPosition && (
          <div
            className="absolute bg-background border rounded-md p-2 text-sm pointer-events-none z-50 whitespace-pre-line"
            style={{
              left: tooltipPosition.x + 10,
              top: tooltipPosition.y - 40,
            }}
          >
            {tooltipContent}
          </div>
        )}

        <div className="absolute bottom-2 left-2 text-xs text-muted-foreground">
          Only hosts with geolocation data are shown
        </div>
      </div>
    </div>
  )
}

