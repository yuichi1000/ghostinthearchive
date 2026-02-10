import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"

/**
 * Extracts English display fields from a mystery document.
 *
 * English-first convention:
 * - New documents: base fields (title, summary, etc.) are already in English
 * - Legacy documents: English content is in *_en fields
 *
 * The *_en || base fallback handles both cases correctly.
 */
export function localizeMystery(mystery: FirestoreMystery) {
  return {
    title: mystery.title_en || mystery.title,
    summary: mystery.summary_en || mystery.summary,
    narrativeContent: mystery.narrative_content_en || mystery.narrative_content,
    discrepancyDetected: mystery.discrepancy_detected_en || mystery.discrepancy_detected,
    hypothesis: mystery.hypothesis_en || mystery.hypothesis,
    alternativeHypotheses: mystery.alternative_hypotheses_en || mystery.alternative_hypotheses,
    politicalClimate:
      mystery.historical_context_en?.political_climate ||
      mystery.historical_context?.political_climate,
    storyHooks: mystery.story_hooks_en ?? mystery.story_hooks,
  }
}
