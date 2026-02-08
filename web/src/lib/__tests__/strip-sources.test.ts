import { describe, it, expect } from "vitest"
import { stripSourcesSection, extractSourcesSection } from "../strip-sources"

describe("stripSourcesSection", () => {
  it("removes a trailing Sources section with single-line list", () => {
    const input = `# Title

Some content here.

---
Sources: Library of Congress, DPLA`

    expect(stripSourcesSection(input)).toBe(
      `# Title

Some content here.`
    )
  })

  it("removes a trailing Sources section with multi-line list", () => {
    const input = `# Title

Content.

---
Sources:
- Library of Congress Digital Archive
- DPLA: Boston Historical Society
- Internet Archive: Newspaper Collection`

    expect(stripSourcesSection(input)).toBe(
      `# Title

Content.`
    )
  })

  it("returns content unchanged when there is no Sources section", () => {
    const input = `# Title

Some content without sources.`

    expect(stripSourcesSection(input)).toBe(input)
  })

  it("handles English narrative content with Sources", () => {
    const input = `# The Vanishing of Elijah Blackwood

In the depths of the Library of Congress digital archive...

---
Sources: LOC Manuscript Division, NYPL Schomburg Center`

    expect(stripSourcesSection(input)).toBe(
      `# The Vanishing of Elijah Blackwood

In the depths of the Library of Congress digital archive...`
    )
  })

  it("does not remove a mid-content HR that is not followed by Sources", () => {
    const input = `# Title

Part 1.

---

Part 2.`

    expect(stripSourcesSection(input)).toBe(input)
  })

  it("removes bold markdown **Sources:** format", () => {
    const input = `# Title

Content here.

---
**Sources:**

*   Source A. Library of Congress.
*   Source B. NYPL Digital Collections.`

    expect(stripSourcesSection(input)).toBe(
      `# Title

Content here.`
    )
  })

  it("handles empty string", () => {
    expect(stripSourcesSection("")).toBe("")
  })
})

describe("extractSourcesSection", () => {
  it("extracts citation list from bold Sources format", () => {
    const input = `# Title

Content here.

---
**Sources:**

*   Source A. Library of Congress.
*   Source B. NYPL Digital Collections.`

    expect(extractSourcesSection(input)).toBe(
      `*   Source A. Library of Congress.
*   Source B. NYPL Digital Collections.`
    )
  })

  it("extracts citation list from plain Sources format", () => {
    const input = `# Title

Content.

---
Sources:
- Library of Congress Digital Archive
- DPLA: Boston Historical Society`

    expect(extractSourcesSection(input)).toBe(
      `- Library of Congress Digital Archive
- DPLA: Boston Historical Society`
    )
  })

  it("returns null when no Sources section exists", () => {
    const input = `# Title

Some content without sources.`

    expect(extractSourcesSection(input)).toBeNull()
  })

  it("returns null for empty string", () => {
    expect(extractSourcesSection("")).toBeNull()
  })
})
