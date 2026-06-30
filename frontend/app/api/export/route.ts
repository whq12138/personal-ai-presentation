import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * POST /api/export — canvas 导出 (presentation JSON 在 body)
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get("authorization") || "";

    const response = await fetch(`${BACKEND_URL}/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify({
        presentation: body.presentation,
        filename: body.filename || "presentation.pptx",
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return NextResponse.json(
        { success: false, error: errText || "Export failed" },
        { status: response.status },
      );
    }

    const pptxBuffer = await response.arrayBuffer();
    return new NextResponse(pptxBuffer, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": `attachment; filename="${body.filename || "presentation.pptx"}"`,
      },
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: "Export failed." }, { status: 502 });
  }
}

/**
 * GET /api/export/:id  — 浏览器 <a> 标签原生下载
 * URL: /api/export/xxx?token=eyJ...
 */
export async function GET(request: NextRequest) {
  try {
    const { pathname, searchParams } = request.nextUrl;
    // pathname = /api/export/{id}  或  /api/export/download/{id}
    const segments = pathname.replace("/api/export", "").replace(/^\//, "").split("/");

    const token = searchParams.get("token") || request.headers.get("authorization")?.replace("Bearer ", "") || "";

    let backendUrl: string;

    if (segments.length === 1 && segments[0]) {
      // /api/export/{saved_id}
      backendUrl = `${BACKEND_URL}/export/${segments[0]}`;
    } else if (segments.length === 2 && segments[0] === "download") {
      // /api/export/download/{saved_id}
      backendUrl = `${BACKEND_URL}/export/download/${segments[1]}?token=${encodeURIComponent(token)}`;
    } else {
      return NextResponse.json({ success: false, error: "Invalid export path" }, { status: 400 });
    }

    const fetchHeaders: Record<string, string> = {};
    if (token && !backendUrl.includes("?token=")) {
      fetchHeaders["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(backendUrl, { headers: fetchHeaders });

    if (!response.ok) {
      const errText = await response.text();
      return NextResponse.json(
        { success: false, error: errText || "Export failed" },
        { status: response.status },
      );
    }

    const pptxBuffer = await response.arrayBuffer();
    const disposition = response.headers.get("content-disposition") || 'attachment; filename="presentation.pptx"';
    const contentType = response.headers.get("content-type") || "application/vnd.openxmlformats-officedocument.presentationml.presentation";

    return new NextResponse(pptxBuffer, {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": disposition,
      },
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: "Export failed." }, { status: 502 });
  }
}
