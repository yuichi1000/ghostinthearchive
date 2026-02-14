/**
 * POST /api/themes/suggest
 *
 * Calls the Curator Cloud Run Service to generate theme suggestions.
 * - Production: IAM-authenticated HTTP call to Cloud Run Service
 * - Local: Direct HTTP call to localhost (docker compose)
 */

import { NextResponse } from "next/server";

const curatorServiceUrl = process.env.CURATOR_SERVICE_URL || "http://localhost:8001";
const isProduction = process.env.NODE_ENV === "production";

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!isProduction) {
    return {};
  }

  // Production: get ID token for Cloud Run service-to-service auth
  const { GoogleAuth } = await import("google-auth-library");
  const auth = new GoogleAuth();
  const client = await auth.getIdTokenClient(curatorServiceUrl);
  const headers = await client.getRequestHeaders();
  return headers;
}

export async function POST() {
  try {
    const authHeaders = await getAuthHeaders();

    const response = await fetch(`${curatorServiceUrl}/suggest-theme`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      signal: AbortSignal.timeout(120000),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`Curator service error (${response.status}):`, errorBody);
      let detail = errorBody;
      let errorType: string | undefined;
      try {
        const parsed = JSON.parse(errorBody);
        detail = parsed.detail || parsed.error || parsed.message || errorBody;
        errorType = parsed.error_type;
      } catch { /* テキストのまま */ }
      return NextResponse.json(
        { error: "Failed to generate theme suggestions", detail, ...(errorType && { error_type: errorType }) },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to generate theme suggestions:", error);
    return NextResponse.json(
      { error: "Failed to generate theme suggestions", detail: String(error) },
      { status: 500 }
    );
  }
}
