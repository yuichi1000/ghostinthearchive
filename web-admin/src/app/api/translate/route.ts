/**
 * POST /api/translate
 *
 * Triggers translation pipeline.
 * - Local: executes translate_main.py directly
 * - Production: starts a Cloud Run Job
 *
 * Status should already be set to "translating" by approveMystery().
 */

import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const isLocal = process.env.NODE_ENV === "development";
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

    if (isLocal) {
      // Local: run Python pipeline in background (fire-and-forget)
      const projectRoot = path.resolve(process.cwd(), "..");
      const pythonPath = path.join(projectRoot, ".venv", "bin", "python");

      const logFile = path.join(projectRoot, "logs", "translate.log");
      fs.mkdirSync(path.dirname(logFile), { recursive: true });
      const out = fs.openSync(logFile, "a");

      const child = spawn(pythonPath, ["translate_main.py", mysteryId], {
        cwd: projectRoot,
        detached: true,
        stdio: ["ignore", out, out],
      });
      child.unref();
      fs.closeSync(out);

      console.log(`Translation started locally for ${mysteryId} (pid: ${child.pid})`);

      return NextResponse.json({
        status: "accepted",
        mysteryId,
        message: "Translation started (local)",
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
    console.error("Failed to run translation:", error);
    return NextResponse.json(
      { error: "Failed to run translation" },
      { status: 500 }
    );
  }
}
