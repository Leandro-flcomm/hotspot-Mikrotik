"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle } from "lucide-react"

interface ApiStatusProps {
  apiUrl: string
}

export function ApiStatus({ apiUrl }: ApiStatusProps) {
  const [status, setStatus] = useState<"loading" | "online" | "offline">("loading")

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        // Try to fetch from the API
        const response = await fetch(`${apiUrl}/api/dashboard/stats`, {
          method: "HEAD",
          // Add a timeout to prevent long waits
          signal: AbortSignal.timeout(5000),
        })

        setStatus(response.ok ? "online" : "offline")
      } catch (error) {
        setStatus("offline")
      }
    }

    checkApiStatus()

    // Check status every 30 seconds
    const interval = setInterval(checkApiStatus, 30000)

    return () => clearInterval(interval)
  }, [apiUrl])

  if (status === "loading") {
    return (
      <Badge variant="outline" className="ml-2">
        Verificando API...
      </Badge>
    )
  }

  if (status === "online") {
    return (
      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 ml-2">
        <CheckCircle className="h-3 w-3 mr-1" />
        API Online
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 ml-2">
      <AlertCircle className="h-3 w-3 mr-1" />
      API Offline
    </Badge>
  )
}
