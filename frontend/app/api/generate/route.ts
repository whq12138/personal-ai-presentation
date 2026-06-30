import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Proxy /api/generate → backend POST /generate with auth forwarding.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get("authorization") || "";

    const response = await fetch(`${BACKEND_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify({
        text: body.text,
        style: body.style || "professional",
        target_lang: body.target_lang || "auto",
        enable_images: body.enable_images ?? true,
      }),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Generate proxy error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to connect to AI service." },
      { status: 502 }
    );
  }
}
