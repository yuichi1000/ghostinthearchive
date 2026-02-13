import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * マークダウン先頭の H1 見出し（# Title）を除去する。
 * CaseFileHeader の <h1> と narrative_content の H1 が重複するのを防ぐ。
 * H2 以下（## Subtitle 等）は除去しない。
 */
export function stripLeadingH1(markdown: string): string {
  return markdown.replace(/^\s*#\s+[^\n]*\n*/, "")
}
