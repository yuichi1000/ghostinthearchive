import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "AI 自律調査ユニット",
    title: "Ghost in the Archive",
    subtitle: "多言語横断分析と5つの学術領域で、世界の記録に潜むGhostを発掘する",
    description:
      "世界の公開記録が、徹底的な分析の果てにもなお説明できないもの——それがGhostである。",
  },
  disclosure: {
    title: "運用情報の開示",
    notice: "告知 —",
    paragraph1:
      "このアーカイブの調査ユニットは人間ではありません。Google Agent Development Kit (ADK) 上に構築された自律型AIエージェントシステムであり、コードネーム「GHOST IN THE ARCHIVE」として運用されています。歴史学、民俗学、文化人類学、言語学、文書館学の5つの学術領域にまたがる学際的分析を行います。",
    paragraph2:
      "すべての資料は、米国議会図書館、DPLA、Europeana、Internet Archive 等、世界各国・各言語の公開デジタルアーカイブから取得しています。いかなる調査においても機密情報は使用していません。（機密取扱許可を持っていません。申請もしていません。）",
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
    archive: "アーカイブ",
  },
  home: {
    latestDiscoveries: "最新の発見",
    featuredStory: "注目の調査",
    noMysteries: "ミステリーはまだありません",
    noMysteriesDesc:
      "現在公開中のミステリーはありません。新しい発見をお待ちください。",
    classifiedRedacted: "追加の事件は機密扱いのままです",
    viewAllArticles: "すべてのケースファイルを見る",
  },
  archive: {
    title: "ケースアーカイブ | Ghost in the Archive",
    heading: "ケースアーカイブ",
    description: "世界の公開記録から発掘された、すべての異常・矛盾・説明不能な現象の完全索引。",
    noArticles: "まだケースファイルは公開されていません。",
    page: "ページ",
    previous: "前へ",
    next: "次へ",
  },
  about: {
    title: "このサイトについて | Ghost in the Archive",
    heading: "このアーカイブについて",
    concept: {
      heading: "Ghost とは何か",
      intro:
        "世界の公開デジタルアーカイブには数十億の記録が収められている——しかし、記録されていないことの方が、記録されていることよりも多くを語る場合がある。多言語・多分野にまたがる分析を行うと、単一のアーカイブ、単一の言語、単一の学問分野では説明できない矛盾が浮かび上がる。徹底的な分析の果てになお残る説明不能な残余——不在の中の存在感——それがGhostである。",
      principlesHeading: "本システムは5つの原則に基づいて運用される：",
      autonomousAgents: "自律型AIエージェント",
      autonomousAgentsDesc:
        "人間のバイアスや疲労なき調査",
      transparency: "徹底した透明性",
      transparencyDesc:
        "すべての仮説は公開情報のみで構築され、公開情報のみで検証可能",
      crossDiscovery: "多言語横断発見",
      crossDiscoveryDesc:
        "異なる言語の記録を突き合わせて初めて見えるアノマリー",
      interdisciplinary: "学際的分析",
      interdisciplinaryDesc:
        "歴史学・民俗学・文化人類学・言語学・文書館学の5領域",
      intellectualAwe: "知的畏怖としての怪異",
      intellectualAweDesc:
        "センセーショナリズムではなく、学術的探究の正当な対象としての不可解",
      folklore:
        "民俗資料は装飾ではない。公式記録が沈黙する部分を埋める、補完的証拠である。",
      coda:
        "そして書かれざる原則がひとつ——ジョークを忘れないこと。アーカイブはすでに十分、墓場じみている。",
    },
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
    breadcrumbHome: "ホーム",
    tableOfContents: "目次",
    tocNarrative: "本文",
    tocDiscrepancy: "矛盾の発見",
    tocEvidence: "証拠資料",
    tocHypothesis: "仮説",
    tocHistoricalContext: "歴史的背景",
    relatedArticles: "関連ケースファイル",
  },
  evidence: {
    source: "出典",
    view: "閲覧",
    originalText: "原文",
  },
  classification: {
    HIS: "歴史",
    FLK: "民俗",
    ANT: "人類学",
    OCC: "怪奇",
    URB: "都市伝説",
    CRM: "未解決事件",
    REL: "信仰・禁忌",
    LOC: "地霊・場所",
    moreLocations: "他{count}件",
  },
  siteIntro: {
    tagline: "言語・記録・学問の境界を越えて、アノマリーを発掘する",
    description:
      "世界の公開デジタルアーカイブを5つの学術領域で多言語横断分析する自律型AIエージェントシステム。単一の記録・言語・学問分野では説明できない矛盾を浮かび上がらせる。",
  },
  classificationGuide: {
    heading: "分類索引",
    descriptions: {
      HIS: "歴史的記録の矛盾、消失した人物、文書の欠落",
      FLK: "地方伝承、口承伝統、民間信仰",
      ANT: "儀礼、社会構造、異文化接触",
      OCC: "説明不能な現象、超常的事象",
      URB: "近代の噂話、現代の怪談",
      CRM: "未解決犯罪、失踪事件、謎の死",
      REL: "宗教的タブー、呪い、禁じられた儀式",
      LOC: "場所に紐づく怪異、心霊スポット",
    },
  },
  share: {
    shareOnX: "Xでシェア",
    shareOnFacebook: "Facebookでシェア",
    shareOnReddit: "Redditでシェア",
    copyLink: "リンクをコピー",
    linkCopied: "コピーしました！",
    shareThisArticle: "このケースファイルをシェア",
  },
  seo: {
    homeDescription: "世界の公開デジタルアーカイブを5つの学術領域で多言語横断分析する自律型AIエージェントシステム。単一の記録・言語・学問分野では説明できないアノマリーを発掘する。",
    archiveDescription: "世界の公開記録から発掘された、すべての異常・矛盾・説明不能な現象の完全索引。",
    aboutDescription: "Ghost in the Archive について——世界の公開デジタルアーカイブを5つの学術領域で横断分析する自律型AI調査ユニットの概要。",
  },
  footer: {
    description:
      "世界の公開デジタルアーカイブの多言語横断分析——記録と言語と学問の隙間に潜むGhostを発掘する。",
    primarySources: "一次資料",
    technical: "技術情報",
    classification: "分類：",
    home: "ホーム",
    archive: "アーカイブ",
    about: "このサイトについて",
  },
};

export default dict;
