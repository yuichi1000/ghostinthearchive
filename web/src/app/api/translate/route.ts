/**
 * POST /api/translate
 *
 * Triggers translation pipeline for a pending mystery article.
 * Status should already be set to "translating" by approveMystery().
 * Launches the Python pipeline in background.
 */

import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";

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

    // Launch translation as a background process
    const projectRoot = path.resolve(process.cwd(), "..");
    const pythonPath = path.join(projectRoot, ".venv", "bin", "python");
    const command = `cd ${JSON.stringify(projectRoot)} && ${JSON.stringify(pythonPath)} translate_main.py ${JSON.stringify(mysteryId)}`;

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Translation error for ${mysteryId}:`, error.message);
        if (stderr) console.error("stderr:", stderr);
      } else {
        console.log(`Translation completed for ${mysteryId}`);
        if (stdout) console.log("stdout:", stdout);
      }
    });

    return NextResponse.json({
      status: "accepted",
      mysteryId,
      message: "Translation started",
    });
  } catch (error) {
    console.error("Failed to start translation:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
