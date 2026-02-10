/**
 * Firestore サンプルデータ投入スクリプト
 * 開発用のダミーミステリーデータをFirestoreに登録
 *
 * 使用方法:
 *   cd web-admin && npx tsx ../scripts/seed-firestore.ts
 */

import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getFirestore, Timestamp } from "firebase-admin/firestore";
import type { FirestoreMystery } from "../web-admin/src/types/mystery";

// Firebase Admin SDK初期化
if (getApps().length === 0) {
  // 環境変数からプロジェクトIDを取得
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "demo-project";

  // エミュレータ使用時の設定
  if (process.env.USE_FIREBASE_EMULATOR === "true") {
    process.env.FIRESTORE_EMULATOR_HOST = `${
      process.env.FIREBASE_EMULATOR_HOST || "localhost"
    }:${process.env.FIRESTORE_EMULATOR_PORT || "8080"}`;
  }

  initializeApp({ projectId });
}

const db = getFirestore();

/**
 * サンプルミステリーデータ
 */
const sampleMysteries: Omit<FirestoreMystery, "createdAt" | "updatedAt">[] = [
  {
    mystery_id: "MYSTERY-1820-BOSTON-001",
    title: "消えたサンタマリア号の積荷",
    summary:
      "1820年、ボストン港に到着したスペイン船サンタマリア号。英語新聞は「香辛料を積んでいた」と報じたが、スペイン外交文書には「銀貨3000枚」の記録が。積荷はどこへ消えたのか？",
    discrepancy_detected:
      "英語新聞では「香辛料の積荷」と報道されているが、スペイン外交文書には「銀貨3000枚」と明記されている。同一船舶の積荷情報に重大な矛盾がある。",
    discrepancy_type: "narrative_gap",
    evidence_a: {
      source_type: "newspaper",
      source_language: "en",
      source_title: "The Boston Daily Advertiser",
      source_date: "1820-03-15",
      source_url: "https://chroniclingamerica.loc.gov/example",
      relevant_excerpt:
        "The Spanish vessel Santa Maria arrived at Boston Harbor yesterday, carrying a cargo of spices from the Caribbean...",
      location_context: "Boston, Massachusetts",
    },
    evidence_b: {
      source_type: "newspaper",
      source_language: "es",
      source_title: "Despacho del Consulado de España en Boston",
      source_date: "1820-03-14",
      source_url: "https://catalog.archives.gov/example",
      relevant_excerpt:
        "El navío Santa María transporta 3,000 monedas de plata destinadas al consulado...",
      location_context: "Boston, Massachusetts",
    },
    additional_evidence: [],
    hypothesis:
      "積荷の矛盾は、密輸を隠蔽するための意図的な情報操作の可能性がある。当時の米西関係の緊張を考慮すると、スペイン政府が銀貨の輸送を秘密にしようとした可能性が高い。",
    alternative_hypotheses: [
      "新聞記者が積荷を誤認した単純なミス",
      "二つの異なる船舶を混同している可能性",
      "スペイン文書が別の船を指している可能性",
    ],
    confidence_level: "medium",
    historical_context: {
      time_period: "1820年代初頭（モンロー・ドクトリン前夜）",
      geographic_scope: ["Boston", "Caribbean", "Spain"],
      relevant_events: [
        "スペイン植民地の独立運動",
        "米国とスペインの外交交渉",
        "フロリダ購入条約（1819年）",
      ],
      key_figures: ["John Quincy Adams", "Spanish Consul in Boston"],
      political_climate:
        "スペイン帝国の衰退期であり、中南米での独立運動が活発化。米国はスペインの弱体化を利用してフロリダを獲得したばかりであった。",
    },
    research_questions: [
      "サンタマリア号の船長と乗組員の記録は残っているか？",
      "同時期のボストン税関記録に該当する船舶の記載はあるか？",
      "スペイン外交文書に銀貨の最終的な処理記録はあるか？",
    ],
    story_hooks: [
      "消えた銀貨のミステリー",
      "19世紀初頭の密輸ネットワーク",
      "新聞とは異なる真実を語る外交文書",
    ],
    analysis_timestamp: new Date().toISOString(),
    status: "pending",
    publishedAt: undefined,
  },
  {
    mystery_id: "MYSTERY-1835-NYC-002",
    title: "二人のフアン・ガルシア",
    summary:
      "1835年、ニューヨークで逮捕されたスペイン人「フアン・ガルシア」。英語新聞は「海賊」と報じたが、スペイン領事館の記録では「外交官の息子」とされていた。彼の正体は？",
    discrepancy_detected:
      "逮捕された人物の身元について、英語新聞とスペイン外交文書で全く異なる説明がなされている。",
    discrepancy_type: "person_missing",
    evidence_a: {
      source_type: "newspaper",
      source_language: "en",
      source_title: "New York Herald",
      source_date: "1835-07-22",
      source_url: "https://chroniclingamerica.loc.gov/example2",
      relevant_excerpt:
        "Juan Garcia, a notorious pirate operating in the Caribbean waters, was apprehended yesterday by authorities...",
      location_context: "New York City",
    },
    evidence_b: {
      source_type: "newspaper",
      source_language: "es",
      source_title: "Correspondencia del Consulado de España en Nueva York",
      source_date: "1835-07-23",
      source_url: "https://catalog.archives.gov/example2",
      relevant_excerpt:
        "Don Juan García, hijo del embajador García de Madrid, ha sido detenido injustamente...",
      location_context: "New York City",
    },
    additional_evidence: [],
    hypothesis:
      "同姓同名の人物が存在した可能性、または外交的理由で身元が意図的に隠蔽された可能性がある。",
    alternative_hypotheses: [
      "外交官の息子が実際に海賊行為に関与していた",
      "スペイン領事館が身元を偽装して救出を試みた",
    ],
    confidence_level: "low",
    historical_context: {
      time_period: "1830年代（ジャクソン大統領時代）",
      geographic_scope: ["New York City", "Caribbean", "Madrid"],
      relevant_events: ["カリブ海における海賊行為の取り締まり強化"],
      key_figures: ["Juan Garcia", "Spanish Ambassador García"],
      political_climate:
        "米国は海賊行為の取り締まりを強化しており、スペインとの外交関係は微妙な時期であった。",
    },
    research_questions: [
      "フアン・ガルシアの裁判記録は残っているか？",
      "スペイン大使ガルシアの家族構成は確認できるか？",
    ],
    story_hooks: [
      "海賊か外交官か—二つの顔を持つ男",
      "19世紀ニューヨークの外交スキャンダル",
    ],
    analysis_timestamp: new Date().toISOString(),
    status: "published",
    publishedAt: new Date(),
  },
];

/**
 * サンプルデータを投入
 */
async function seedFirestore() {
  console.log("🌱 サンプルデータの投入を開始します...\n");

  const mysteriesCollection = db.collection("mysteries");

  for (const mystery of sampleMysteries) {
    const docRef = mysteriesCollection.doc(mystery.mystery_id);

    // タイムスタンプを追加
    const mysteryWithTimestamps = {
      ...mystery,
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
      publishedAt: mystery.publishedAt ? Timestamp.fromDate(mystery.publishedAt as Date) : null,
    };

    await docRef.set(mysteryWithTimestamps);
    console.log(`  ✅ ${mystery.mystery_id}: ${mystery.title}`);
  }

  console.log(`\n🎉 ${sampleMysteries.length} 件のサンプルデータを投入しました`);
  console.log("\nステータス:");
  console.log(`  - pending: ${sampleMysteries.filter((m) => m.status === "pending").length} 件`);
  console.log(`  - published: ${sampleMysteries.filter((m) => m.status === "published").length} 件`);
}

// 実行
seedFirestore()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("エラー:", error);
    process.exit(1);
  });
