/**
 * POST /api/rebuild-public
 *
 * approve/archive 後に web-public の SSG リビルドを発火する。
 * - 本番: google-auth-library で access token を取得し、Cloud Build triggers.run を呼び出す
 * - ローカル: 何もしない（dev モードでは Firestore 更新が即座に反映されるため不要）
 */

import { NextResponse } from "next/server";

const projectId = process.env.GOOGLE_CLOUD_PROJECT;
const triggerId = process.env.CLOUD_BUILD_TRIGGER_ID;
const isProduction = process.env.NODE_ENV === "production";

export async function POST() {
  // ローカル開発ではリビルドをスキップ
  if (!isProduction) {
    return NextResponse.json({ status: "skipped", reason: "not production" });
  }

  if (!projectId || !triggerId) {
    console.error("Missing GOOGLE_CLOUD_PROJECT or CLOUD_BUILD_TRIGGER_ID");
    return NextResponse.json(
      { error: "Missing configuration" },
      { status: 500 }
    );
  }

  try {
    const { GoogleAuth } = await import("google-auth-library");
    const auth = new GoogleAuth({
      scopes: ["https://www.googleapis.com/auth/cloud-platform"],
    });
    const client = await auth.getClient();
    const { token } = await client.getAccessToken();

    const url = `https://cloudbuild.googleapis.com/v1/projects/${projectId}/triggers/${triggerId}:run`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ branchName: "main" }),
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`Cloud Build API error (${response.status}):`, errorBody);
      return NextResponse.json(
        { error: "Failed to trigger rebuild" },
        { status: 500 }
      );
    }

    const data = await response.json();
    console.log("Cloud Build triggered:", data.metadata?.build?.id);
    return NextResponse.json({
      status: "triggered",
      buildId: data.metadata?.build?.id,
    });
  } catch (error) {
    console.error("Failed to trigger Cloud Build:", error);
    return NextResponse.json(
      { error: "Failed to trigger rebuild" },
      { status: 500 }
    );
  }
}
