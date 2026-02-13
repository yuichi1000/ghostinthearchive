/**
 * POST /api/podcasts/generate
 *
 * Triggers podcast generation pipeline via HTTP POST to Pipeline Cloud Run Service.
 * - Production: IAM-authenticated HTTP call to Cloud Run Service
 * - Local: Direct HTTP call to localhost (docker compose)
 */

import { NextRequest, NextResponse } from "next/server";

const pipelineServiceUrl =
  process.env.PIPELINE_SERVICE_URL || "http://localhost:8002";
const isProduction = process.env.NODE_ENV === "production";

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!isProduction) {
    return {};
  }

  // Production: get ID token for Cloud Run service-to-service auth
  const { GoogleAuth } = await import("google-auth-library");
  const auth = new GoogleAuth();
  const client = await auth.getIdTokenClient(pipelineServiceUrl);
  const headers = await client.getRequestHeaders();
  return headers;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { mysteryId } = body;

    if (!mysteryId || typeof mysteryId !== "string") {
      return NextResponse.json(
        { error: "mysteryId is required" },
        { status: 400 }
      );
    }

    const authHeaders = await getAuthHeaders();

    const response = await fetch(`${pipelineServiceUrl}/podcast`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify({ mystery_id: mysteryId }),
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`Pipeline service error (${response.status}):`, errorBody);
      return NextResponse.json(
        { error: "Failed to start podcast pipeline" },
        { status: 500 }
      );
    }

    const data = await response.json();
    return NextResponse.json({
      status: "accepted",
      mysteryId,
      message: "Podcast pipeline started",
      run_id: data.run_id,
    });
  } catch (error) {
    console.error("Failed to start podcast pipeline:", error);
    return NextResponse.json(
      { error: "Failed to start podcast pipeline" },
      { status: 500 }
    );
  }
}
