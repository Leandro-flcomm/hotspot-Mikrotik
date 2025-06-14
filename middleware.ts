import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// This middleware adds CORS headers to API requests
export function middleware(request: NextRequest) {
  // Only run this middleware for API routes
  if (request.nextUrl.pathname.startsWith("/api/")) {
    // Get response
    const response = NextResponse.next()

    // Add CORS headers
    response.headers.set("Access-Control-Allow-Origin", "*")
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization")

    return response
  }
}

// Configure middleware to run only for API routes
export const config = {
  matcher: "/api/:path*",
}
