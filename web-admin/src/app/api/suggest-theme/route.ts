/**
 * POST /api/suggest-theme
 *
 * Runs the Curator agent and returns theme suggestions.
 * Synchronous call - waits for the agent to complete and returns JSON.
 */

import { NextResponse } from "next/server";
import { execSync } from "child_process";
import path from "path";

export async function POST() {
  try {
    const projectRoot = path.resolve(process.cwd(), "..");
    const pythonPath = path.join(projectRoot, ".venv", "bin", "python");
    const command = `cd ${JSON.stringify(projectRoot)} && ${JSON.stringify(pythonPath)} curator_main.py`;

    const stdout = execSync(command, {
      timeout: 120000,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });

    // Parse the last line as JSON (agent outputs JSON on the last line)
    const lines = stdout.trim().split("\n");
    const lastLine = lines[lines.length - 1];
    const suggestions = JSON.parse(lastLine);

    return NextResponse.json({ suggestions });
  } catch (error) {
    console.error("Failed to generate theme suggestions:", error);
    return NextResponse.json(
      { error: "Failed to generate theme suggestions" },
      { status: 500 }
    );
  }
}
