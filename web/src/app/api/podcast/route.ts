/**
 * POST /api/podcast
 *
 * Triggers podcast generation for a published mystery article.
 * Updates Firestore status to "generating" and launches the Python pipeline.
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

    // Launch podcast generation as a background process
    const projectRoot = path.resolve(process.cwd(), "..");
    const command = `cd ${JSON.stringify(projectRoot)} && python podcast_main.py ${JSON.stringify(mysteryId)}`;

    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Podcast generation error for ${mysteryId}:`, error.message);
        if (stderr) console.error("stderr:", stderr);
      } else {
        console.log(`Podcast generation completed for ${mysteryId}`);
        if (stdout) console.log("stdout:", stdout);
      }
    });

    return NextResponse.json({
      status: "accepted",
      mysteryId,
      message: "Podcast generation started",
    });
  } catch (error) {
    console.error("Failed to start podcast generation:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
