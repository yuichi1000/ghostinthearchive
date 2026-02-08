/**
 * Extract and separate the trailing "Sources" section from narrative_content.
 *
 * Storyteller appends a markdown section like:
 *   ---
 *   **Sources:**
 *   * Source A...
 *
 * We split it from the narrative body so it can be rendered inside the
 * "Sources & Evidence" section instead of at the end of the article text.
 */

const SOURCES_PATTERN = /\n---\n\s*\*{0,2}Sources:\*{0,2}([\s\S]*)$/;

/**
 * Remove the trailing Sources section from narrative_content.
 */
export function stripSourcesSection(content: string): string {
  return content.replace(SOURCES_PATTERN, "").trimEnd();
}

/**
 * Extract the Sources citation list from narrative_content.
 * Returns the citation text (without the "Sources:" heading) or null if not found.
 */
export function extractSourcesSection(content: string): string | null {
  const match = content.match(SOURCES_PATTERN);
  if (!match) return null;
  return match[1].trim() || null;
}
