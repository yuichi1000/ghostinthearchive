import type { FirestoreMystery, TranslatedContent } from "../types/mystery";

/**
 * ローカライズ済みフィールドの型
 */
export interface LocalizedMystery {
  title: string;
  summary: string;
  narrativeContent: string;
  discrepancyDetected: string;
  hypothesis: string;
  alternativeHypotheses: string[];
  politicalClimate: string;
  storyHooks: string[];
  confidenceRationale: string;
}

/**
 * ミステリーのフィールドを指定言語にローカライズする
 *
 * フォールバック順:
 * - en: base fields（*_en レガシー → base）
 * - ja: translations["ja"] → *_ja レガシー → base fields
 * - その他: translations[lang] → base fields
 */
export function localizeMystery(
  mystery: FirestoreMystery,
  lang: string = "en"
): LocalizedMystery {
  if (lang === "en") {
    return {
      title: mystery.title_en || mystery.title,
      summary: mystery.summary_en || mystery.summary,
      narrativeContent: mystery.narrative_content_en || mystery.narrative_content || "",
      discrepancyDetected: mystery.discrepancy_detected_en || mystery.discrepancy_detected,
      hypothesis: mystery.hypothesis_en || mystery.hypothesis,
      alternativeHypotheses: mystery.alternative_hypotheses_en || mystery.alternative_hypotheses,
      politicalClimate:
        mystery.historical_context_en?.political_climate ||
        mystery.historical_context?.political_climate || "",
      storyHooks: mystery.story_hooks_en ?? mystery.story_hooks,
      confidenceRationale: mystery.confidence_rationale || "",
    };
  }

  const t: TranslatedContent | undefined = mystery.translations?.[lang];

  if (lang === "ja") {
    return {
      title: t?.title || mystery.title_ja || mystery.title,
      summary: t?.summary || mystery.summary_ja || mystery.summary,
      narrativeContent:
        t?.narrative_content || mystery.narrative_content_ja || mystery.narrative_content || "",
      discrepancyDetected:
        t?.discrepancy_detected || mystery.discrepancy_detected_ja || mystery.discrepancy_detected,
      hypothesis: t?.hypothesis || mystery.hypothesis_ja || mystery.hypothesis,
      alternativeHypotheses:
        t?.alternative_hypotheses || mystery.alternative_hypotheses_ja || mystery.alternative_hypotheses,
      politicalClimate:
        t?.historical_context?.political_climate ||
        mystery.historical_context_ja?.political_climate ||
        mystery.historical_context?.political_climate || "",
      storyHooks: t?.story_hooks ?? mystery.story_hooks_ja ?? mystery.story_hooks,
      confidenceRationale:
        t?.confidence_rationale || mystery.confidence_rationale || "",
    };
  }

  if (t) {
    return {
      title: t.title || mystery.title,
      summary: t.summary || mystery.summary,
      narrativeContent: t.narrative_content || mystery.narrative_content || "",
      discrepancyDetected: t.discrepancy_detected || mystery.discrepancy_detected,
      hypothesis: t.hypothesis || mystery.hypothesis,
      alternativeHypotheses: t.alternative_hypotheses || mystery.alternative_hypotheses,
      politicalClimate:
        t.historical_context?.political_climate ||
        mystery.historical_context?.political_climate || "",
      storyHooks: t.story_hooks ?? mystery.story_hooks,
      confidenceRationale:
        t.confidence_rationale || mystery.confidence_rationale || "",
    };
  }

  return {
    title: mystery.title,
    summary: mystery.summary,
    narrativeContent: mystery.narrative_content || "",
    discrepancyDetected: mystery.discrepancy_detected,
    hypothesis: mystery.hypothesis,
    alternativeHypotheses: mystery.alternative_hypotheses,
    politicalClimate: mystery.historical_context?.political_climate || "",
    storyHooks: mystery.story_hooks,
    confidenceRationale: mystery.confidence_rationale || "",
  };
}

/**
 * 証拠の翻訳済み抜粋テキストを取得
 */
export function getTranslatedExcerpt(
  mystery: FirestoreMystery,
  evidenceKey: "a" | "b" | number,
  lang: string
): string | undefined {
  if (lang === "en") return undefined;

  const t = mystery.translations?.[lang];
  if (!t) return undefined;

  if (evidenceKey === "a") return t.evidence_a_excerpt;
  if (evidenceKey === "b") return t.evidence_b_excerpt;
  if (typeof evidenceKey === "number") {
    return t.additional_evidence_excerpts?.[evidenceKey];
  }
  return undefined;
}
