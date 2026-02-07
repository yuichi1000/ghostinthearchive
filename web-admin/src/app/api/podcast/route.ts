/**
 * POST /api/podcast
 *
 * Triggers podcast generation pipeline by starting a Cloud Run Job.
 */

import { NextRequest, NextResponse } from "next/server";
import { JobsClient } from "@google-cloud/run";

const projectId = process.env.GOOGLE_CLOUD_PROJECT || "ghostinthearchive";
const region = process.env.GOOGLE_CLOUD_REGION || "asia-northeast1";
const jobName = "podcast-pipeline";

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

    console.log(`Podcast pipeline started for ${mysteryId}:`, execution.name);

    return NextResponse.json({
      status: "accepted",
      mysteryId,
      message: "Podcast pipeline started",
      executionName: execution.name,
    });
  } catch (error) {
    console.error("Failed to start podcast pipeline:", error);
    return NextResponse.json(
      { error: "Failed to start podcast pipeline" },
      { status: 500 }
    );
  }
}
