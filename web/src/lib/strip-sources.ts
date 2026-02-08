/**
 * Remove the trailing "Sources" section from narrative_content.
 *
 * Storyteller used to append a markdown section like:
 *   ---
 *   Sources: [list of citations]
 *
 * This is now redundant because the same information is displayed in the
 * structured "Sources & Evidence" block. For backward compatibility with
 * existing articles we strip it at render time rather than migrating
 * Firestore documents.
 */
export function stripSourcesSection(content: string): string {
  // Match a trailing HR (---) followed by a line starting with "Sources:"
  // and everything after it until end-of-string.
  return content.replace(/\n---\n\s*Sources:[\s\S]*$/, "").trimEnd();
}
