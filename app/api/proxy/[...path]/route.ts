import { type NextRequest, NextResponse } from "next/server"

// Proxy para contornar problemas de CORS
export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/")
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://hotspot-backend:5000"

  // Não adicionar /api se já estiver no path
  const fullUrl = path.startsWith("api/") ? `${apiUrl}/${path}` : `${apiUrl}/api/${path}`

  console.log(`Proxying GET request to: ${fullUrl}`)

  try {
    const response = await fetch(fullUrl, {
      headers: {
        "Content-Type": "application/json",
      },
    })

    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Failed to fetch from API" }, { status: 500 })
  }
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/")
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://hotspot-backend:5000"

  // Não adicionar /api se já estiver no path
  const fullUrl = path.startsWith("api/") ? `${apiUrl}/${path}` : `${apiUrl}/api/${path}`

  console.log(`Proxying POST request to: ${fullUrl}`)

  try {
    const body = await request.json()

    const response = await fetch(fullUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Failed to post to API" }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/")
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://hotspot-backend:5000"

  // Não adicionar /api se já estiver no path
  const fullUrl = path.startsWith("api/") ? `${apiUrl}/${path}` : `${apiUrl}/api/${path}`

  console.log(`Proxying DELETE request to: ${fullUrl}`)

  try {
    const response = await fetch(fullUrl, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })

    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Failed to delete from API" }, { status: 500 })
  }
}

export const dynamic = "force-dynamic"
