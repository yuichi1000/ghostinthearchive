/**
 * POST /api/pipeline
 *
 * Triggers blog creation pipeline by starting a Cloud Run Job.
 */

import { NextRequest, NextResponse } from "next/server";
import { JobsClient } from "@google-cloud/run";

const projectId = process.env.GOOGLE_CLOUD_PROJECT || "ghostinthearchive";
const region = process.env.GOOGLE_CLOUD_REGION || "asia-northeast1";
const jobName = "blog-pipeline";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;

    if (!query || typeof query !== "string") {
      return NextResponse.json(
        { error: "query is required" },
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
            args: [query],
          },
        ],
      },
    });

    console.log(`Blog pipeline started for query "${query}":`, execution.name);

    return NextResponse.json({
      status: "accepted",
      query,
      message: "Blog pipeline started",
      executionName: execution.name,
    });
  } catch (error) {
    console.error("Failed to start blog pipeline:", error);
    return NextResponse.json(
      { error: "Failed to start blog pipeline" },
      { status: 500 }
    );
  }
}
