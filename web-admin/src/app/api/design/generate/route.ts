/**
 * POST /api/design/generate
 *
 * デザイン提案生成パイプラインを起動する。
 * Pipeline Cloud Run Service の POST /design/generate に proxy する。
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
    const { mystery_id, custom_instructions } = body;

    if (!mystery_id || typeof mystery_id !== "string") {
      return NextResponse.json(
        { error: "mystery_id is required" },
        { status: 400 }
      );
    }

    const authHeaders = await getAuthHeaders();

    const response = await fetch(
      `${pipelineServiceUrl}/design/generate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          mystery_id,
          custom_instructions: custom_instructions || "",
        }),
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
        { error: "Failed to start design generation", detail },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      status: "accepted",
      mystery_id,
      message: "Design generation started",
      run_id: data.run_id,
      design_id: data.design_id,
    });
  } catch (error) {
    console.error("Failed to start design generation:", error);
    return NextResponse.json(
      { error: "Failed to start design generation", detail: String(error) },
      { status: 500 }
    );
  }
}
