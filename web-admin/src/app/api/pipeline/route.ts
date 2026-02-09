/**
 * POST /api/pipeline
 *
 * Triggers blog creation pipeline.
 * - Local: executes main.py directly
 * - Production: starts a Cloud Run Job
 */

import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const isLocal = process.env.NODE_ENV === "development";
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

    if (isLocal) {
      // Local: run Python pipeline in background (fire-and-forget)
      const projectRoot = path.resolve(process.cwd(), "..");
      const pythonPath = path.join(projectRoot, ".venv", "bin", "python");

      const logFile = path.join(projectRoot, "logs", "pipeline.log");
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      const out = fs.openSync(logFile, "a");

      const child = spawn(pythonPath, ["main.py", query], {
        cwd: projectRoot,
        detached: true,
        stdio: ["ignore", out, out],
      });
      child.unref();
      fs.closeSync(out);

      console.log(`Blog pipeline started locally for query "${query}" (pid: ${child.pid})`);

      return NextResponse.json({
        status: "accepted",
        query,
        message: "Blog pipeline started (local)",
      });
    }

    // Production: start Cloud Run Job
    const { JobsClient } = await import("@google-cloud/run");
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
