/**
 * Mysteries Firestore 操作
 * ミステリーデータのCRUD操作を提供
 */

import type {
  FirestoreMystery,
  MysteryStatus,
  MysteryCardData,
} from "@/types/mystery";

/**
 * モックモードが有効かどうか
 * Firebase設定がない場合はモックデータを使用
 */
const USE_MOCK = !process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

/**
 * モックデータ（開発用サンプル）
 */
const MOCK_MYSTERIES: FirestoreMystery[] = [
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
    analysis_timestamp: "2026-01-25T10:00:00.000Z",
    status: "published",
    createdAt: new Date("2026-01-20"),
    updatedAt: new Date("2026-01-25"),
    publishedAt: new Date("2026-01-25"),
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
    analysis_timestamp: "2026-01-24T15:30:00.000Z",
    status: "published",
    createdAt: new Date("2026-01-18"),
    updatedAt: new Date("2026-01-24"),
    publishedAt: new Date("2026-01-24"),
  },
  {
    mystery_id: "MYSTERY-1845-PHILA-003",
    title: "フィラデルフィアの幽霊船",
    summary:
      "1845年、フィラデルフィア港で発見された無人のスペイン船。乗組員は消え、積荷だけが残されていた。新聞は「海難事故」と報じたが、スペイン文書には不穏な記録が...",
    discrepancy_detected:
      "船の発見状況と乗組員の消失について、英語新聞とスペイン文書で説明が大きく異なる。",
    discrepancy_type: "event_outcome",
    evidence_a: {
      source_type: "newspaper",
      source_language: "en",
      source_title: "Philadelphia Inquirer",
      source_date: "1845-09-10",
      source_url: "https://chroniclingamerica.loc.gov/example3",
      relevant_excerpt:
        "A Spanish vessel was discovered adrift near the harbor, its crew presumed lost to a terrible storm...",
      location_context: "Philadelphia, Pennsylvania",
    },
    evidence_b: {
      source_type: "newspaper",
      source_language: "es",
      source_title: "Informe del Cónsul de España en Filadelfia",
      source_date: "1845-09-12",
      source_url: "https://catalog.archives.gov/example3",
      relevant_excerpt:
        "La tripulación fue vista desembarcando en secreto tres días antes del hallazgo oficial del navío...",
      location_context: "Philadelphia, Pennsylvania",
    },
    additional_evidence: [],
    hypothesis:
      "乗組員は船を放棄し、秘密裏に上陸した可能性がある。密輸や亡命が関係している可能性。",
    alternative_hypotheses: [
      "本当に嵐による海難事故だった",
      "乗組員の反乱が起きた",
    ],
    confidence_level: "medium",
    historical_context: {
      time_period: "1840年代（米墨戦争前夜）",
      geographic_scope: ["Philadelphia", "Caribbean", "Cuba"],
      relevant_events: ["キューバ独立運動の萌芽", "米墨関係の緊張"],
      key_figures: [],
      political_climate:
        "米国の領土拡張主義が高まる中、スペイン領キューバへの関心も増大していた。",
    },
    research_questions: [
      "船の積荷の最終的な行方は？",
      "乗組員の目撃情報の詳細は？",
    ],
    story_hooks: [
      "消えた乗組員の謎",
      "19世紀の幽霊船伝説",
    ],
    analysis_timestamp: "2026-01-23T09:00:00.000Z",
    status: "pending",
    createdAt: new Date("2026-01-23"),
    updatedAt: new Date("2026-01-23"),
  },
];

// ============================================
// Firestore関数（モック対応版）
// ============================================

/**
 * 公開済みミステリー一覧を取得
 * 公開サイトのトップページ用
 */
export async function getPublishedMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  if (USE_MOCK) {
    return MOCK_MYSTERIES
      .filter((m) => m.status === "published")
      .sort((a, b) => (b.publishedAt?.getTime() || 0) - (a.publishedAt?.getTime() || 0))
      .slice(0, maxCount);
  }

  // Firestore実装
  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "published" as MysteryStatus),
    orderBy("publishedAt", "desc"),
    limit(maxCount)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

/**
 * 承認待ちミステリー一覧を取得
 * 管理ダッシュボード用
 */
export async function getPendingMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  if (USE_MOCK) {
    return MOCK_MYSTERIES
      .filter((m) => m.status === "pending")
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
      .slice(0, maxCount);
  }

  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "pending" as MysteryStatus),
    orderBy("createdAt", "desc"),
    limit(maxCount)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

/**
 * 全ミステリー一覧を取得（管理者用）
 */
export async function getAllMysteries(
  maxCount: number = 100
): Promise<FirestoreMystery[]> {
  if (USE_MOCK) {
    return MOCK_MYSTERIES
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
      .slice(0, maxCount);
  }

  const { collection, getDocs, query, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(mysteriesRef, orderBy("createdAt", "desc"), limit(maxCount));

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

/**
 * 単一ミステリーをIDで取得
 */
export async function getMysteryById(
  mysteryId: string
): Promise<FirestoreMystery | null> {
  if (USE_MOCK) {
    return MOCK_MYSTERIES.find((m) => m.mystery_id === mysteryId) || null;
  }

  const { doc, getDoc } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    return null;
  }

  return docToMystery(docSnap.data());
}

/**
 * ミステリーを公開（承認）
 * status を pending → published に更新
 */
export async function approveMystery(mysteryId: string): Promise<void> {
  if (USE_MOCK) {
    const mystery = MOCK_MYSTERIES.find((m) => m.mystery_id === mysteryId);
    if (mystery) {
      mystery.status = "published";
      mystery.publishedAt = new Date();
      mystery.updatedAt = new Date();
    }
    return;
  }

  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "published" as MysteryStatus,
    publishedAt: Timestamp.now(),
    updatedAt: Timestamp.now(),
  });
}

/**
 * ミステリーをアーカイブ（非公開化）
 */
export async function archiveMystery(mysteryId: string): Promise<void> {
  if (USE_MOCK) {
    const mystery = MOCK_MYSTERIES.find((m) => m.mystery_id === mysteryId);
    if (mystery) {
      mystery.status = "archived";
      mystery.updatedAt = new Date();
    }
    return;
  }

  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "archived" as MysteryStatus,
    updatedAt: Timestamp.now(),
  });
}

/**
 * 公開済みミステリーのIDリストを取得
 * generateStaticParams用
 */
export async function getPublishedMysteryIds(): Promise<string[]> {
  if (USE_MOCK) {
    return MOCK_MYSTERIES
      .filter((m) => m.status === "published")
      .map((m) => m.mystery_id);
  }

  const { collection, getDocs, query, where } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "published" as MysteryStatus)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => doc.id);
}

/**
 * FirestoreMysteryをMysteryCardDataに変換
 * 一覧表示用の軽量オブジェクト
 */
export function toCardData(mystery: FirestoreMystery): MysteryCardData {
  return {
    mystery_id: mystery.mystery_id,
    title: mystery.title,
    summary: mystery.summary,
    discrepancy_type: mystery.discrepancy_type,
    confidence_level: mystery.confidence_level,
    status: mystery.status,
    createdAt: mystery.createdAt,
  };
}

// ============================================
// ヘルパー関数
// ============================================

import { Timestamp, DocumentData } from "firebase/firestore";

/**
 * FirestoreのタイムスタンプをDateに変換
 */
function convertTimestamp(timestamp: Timestamp | Date | undefined): Date {
  if (!timestamp) return new Date();
  if (timestamp instanceof Timestamp) {
    return timestamp.toDate();
  }
  return timestamp;
}

/**
 * FirestoreドキュメントをFirestoreMysteryに変換
 */
function docToMystery(docData: DocumentData): FirestoreMystery {
  return {
    ...docData,
    createdAt: convertTimestamp(docData.createdAt),
    updatedAt: convertTimestamp(docData.updatedAt),
    publishedAt: docData.publishedAt
      ? convertTimestamp(docData.publishedAt)
      : undefined,
  } as FirestoreMystery;
}
