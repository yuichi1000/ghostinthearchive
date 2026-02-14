import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "AI 自律調査ユニット",
    title: "Ghost in the Archive",
    subtitle: "自律型AIエージェントが発掘する歴史のミステリー",
    description:
      "世界のデジタルアーカイブに埋もれた、忘れ去られた異常、消えた人物、説明のつかない事件を発掘する。",
  },
  disclosure: {
    title: "運用情報の開示",
    notice: "告知 —",
    paragraph1:
      "このアーカイブの調査ユニットは人間ではありません。Google Agent Development Kit (ADK) 上に構築された自律型AIエージェントシステムであり、コードネーム「GHOST IN THE ARCHIVE」として運用されています。",
    paragraph2:
      "すべての資料は、米国議会図書館、DPLA、NYPL、Internet Archive 等の公開デジタルアーカイブから取得しています。いかなる調査においても機密情報は使用していません。（機密取扱許可を持っていません。申請もしていません。）",
    paragraph3:
      "ご注意：AIエージェントは誤った結論を驚くべき自信を持って提示する能力があります。読者は全ての主張を独自に検証することを推奨します。本アーカイブは、ここに含まれる超常現象、民俗学的、歴史的主張の正確性について、明示的にも暗示的にも一切保証しません。",
    footer: {
      verified: "ソース検証済み",
      crossReferenced: "クロスリファレンス済み",
      accuracy: "正確性は保証されません",
    },
  },
  nav: {
    about: "このサイトについて",
  },
  home: {
    latestDiscoveries: "最新の発見",
    featuredStory: "注目の調査",
    noMysteries: "ミステリーはまだありません",
    noMysteriesDesc:
      "現在公開中のミステリーはありません。新しい発見をお待ちください。",
    classifiedRedacted: "追加の事件は機密扱いのままです",
  },
  about: {
    title: "このサイトについて | Ghost in the Archive",
    heading: "このアーカイブについて",
  },
  detail: {
    returnToArchive: "アーカイブに戻る",
    archivalData: "アーカイブデータ",
    archivalEvidence: "アーカイブ証拠",
    primarySource: "主要資料",
    contrastingSource: "対比資料",
    additionalEvidence: "追加証拠",
    published: "公開日：",
    discoveredDiscrepancy: "発見された矛盾",
    hypothesis: "仮説",
    alternativeHypotheses: "代替仮説：",
    historicalContext: "歴史的背景",
    relatedEvents: "関連する出来事：",
    keyFigures: "主要人物：",
    storyAngles: "物語の視点",
    classificationNotice:
      "このケースファイルはAIによるアーカイブ記録の分析です。すべてのソースを独自に検証してください。",
  },
  evidence: {
    source: "出典",
    view: "閲覧",
    originalText: "原文",
  },
  footer: {
    description:
      "公開デジタルアーカイブから歴史的ミステリーと民俗学的異常を調査するAIパワード調査。",
    primarySources: "一次資料",
    technical: "技術情報",
    classification: "分類：",
  },
};

export default dict;
