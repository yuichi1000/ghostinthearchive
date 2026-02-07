/**
 * POST /api/translate
 *
 * Triggers translation pipeline by starting a Cloud Run Job.
 * Status should already be set to "translating" by approveMystery().
 */

import { NextRequest, NextResponse } from "next/server";
import { JobsClient } from "@google-cloud/run";

const projectId = process.env.GOOGLE_CLOUD_PROJECT || "ghostinthearchive";
const region = process.env.GOOGLE_CLOUD_REGION || "asia-northeast1";
const jobName = "translate-pipeline";

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

    // Start Cloud Run Job
    const client = new JobsClient();
    const name = `projects/${projectId}/locations/${region}/jobs/${jobName}`;

    const [execution] = await client.runJob({
      name,
      overrides: {
        containerOverrides: [
          {
            args: [mysteryId],
          },
        ],
      },
    });

    console.log(`Translation job started for ${mysteryId}:`, execution.name);

    return NextResponse.json({
      status: "accepted",
      mysteryId,
      message: "Translation job started",
      executionName: execution.name,
    });
  } catch (error) {
    console.error("Failed to start translation job:", error);
    return NextResponse.json(
      { error: "Failed to start translation job" },
      { status: 500 }
    );
  }
}
