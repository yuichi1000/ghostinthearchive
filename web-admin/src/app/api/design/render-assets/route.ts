/**
 * POST /api/design/render-assets
 *
 * デザインアセットレンダリングパイプラインを起動する。
 * Pipeline Cloud Run Service の POST /design/render-assets に proxy する。
 */

import { NextRequest, NextResponse } from "next/server";

const pipelineServiceUrl =
  process.env.PIPELINE_SERVICE_URL || "http://localhost:8002";
const isProduction = process.env.NODE_ENV === "production";

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!isProduction) {
    return {};
  }

  const { GoogleAuth } = await import("google-auth-library");
  const auth = new GoogleAuth();
  const client = await auth.getIdTokenClient(pipelineServiceUrl);
  const headers = await client.getRequestHeaders();
  return headers;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { design_id } = body;

    if (!design_id || typeof design_id !== "string") {
      return NextResponse.json(
        { error: "design_id is required" },
        { status: 400 }
      );
    }

    const authHeaders = await getAuthHeaders();

    const response = await fetch(
      `${pipelineServiceUrl}/design/render-assets`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({ design_id }),
        signal: AbortSignal.timeout(30000),
      }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(
        `Pipeline service error (${response.status}):`,
        errorBody
      );
      let detail = errorBody;
      try {
        const parsed = JSON.parse(errorBody);
        detail = parsed.detail || parsed.error || parsed.message || errorBody;
      } catch { /* テキストのまま */ }
      return NextResponse.json(
        { error: "Failed to start design rendering", detail },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      status: "accepted",
      design_id,
      message: "Design rendering started",
      run_id: data.run_id,
    });
  } catch (error) {
    console.error("Failed to start design rendering:", error);
    return NextResponse.json(
      { error: "Failed to start design rendering", detail: String(error) },
      { status: 500 }
    );
  }
}
