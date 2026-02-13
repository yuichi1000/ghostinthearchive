/**
 * POST /api/podcast/generate-audio
 *
 * Podcast 音声生成を起動する。
 * Pipeline Cloud Run Service の POST /podcast/generate-audio に proxy する。
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
    const { podcast_id, script, voice_name } = body;

    if (!podcast_id || typeof podcast_id !== "string") {
      return NextResponse.json(
        { error: "podcast_id is required" },
        { status: 400 }
      );
    }

    const authHeaders = await getAuthHeaders();

    const response = await fetch(
      `${pipelineServiceUrl}/podcast/generate-audio`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          podcast_id,
          script: script || null,
          voice_name: voice_name || "en-US-Studio-O",
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
        { error: "Failed to start podcast audio generation", detail },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      status: "accepted",
      podcast_id,
      message: "Podcast audio generation started",
    });
  } catch (error) {
    console.error("Failed to start podcast audio generation:", error);
    return NextResponse.json(
      { error: "Failed to start podcast audio generation", detail: String(error) },
      { status: 500 }
    );
  }
}
