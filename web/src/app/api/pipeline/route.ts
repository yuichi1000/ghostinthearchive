/**
 * POST /api/pipeline
 *
 * Triggers the blog creation pipeline with a given investigation theme/query.
 * Launches the Python pipeline as a background process (fire-and-forget).
 */

import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";

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

    // Launch blog pipeline as a background process
    const projectRoot = path.resolve(process.cwd(), "..");
    const pythonPath = path.join(projectRoot, ".venv", "bin", "python");
    const command = `cd ${JSON.stringify(projectRoot)} && ${JSON.stringify(pythonPath)} main.py ${JSON.stringify(query)}`;

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Pipeline error for query "${query}":`, error.message);
        if (stderr) console.error("stderr:", stderr);
      } else {
        console.log(`Pipeline completed for query "${query}"`);
        if (stdout) console.log("stdout:", stdout);
      }
    });

    return NextResponse.json({
      status: "accepted",
      query,
      message: "Pipeline started",
    });
  } catch (error) {
    console.error("Failed to start pipeline:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
