"use client"

import { useEffect, useState } from "react"
import { List } from "lucide-react"

export const SECTION_IDS = {
  narrative: "section-narrative",
  discrepancy: "section-discrepancy",
  evidence: "section-evidence",
  hypothesis: "section-hypothesis",
  historicalContext: "section-historical-context",
} as const

export interface TocSection {
  id: string
  label: string
}

interface TableOfContentsProps {
  sections: TocSection[]
  heading: string
  variant: "mobile" | "desktop"
}

function TocLinks({
  sections,
  activeId,
  onClick,
}: {
  sections: TocSection[]
  activeId: string | null
  onClick: (id: string) => void
}) {
  return (
    <ul className="space-y-1">
      {sections.map((section, index) => (
        <li key={`${section.id}-${index}`}>
          <button
            onClick={() => onClick(section.id)}
            className={`w-full text-left text-sm font-mono py-1.5 pl-3 border-l-2 transition-colors ${
              activeId === section.id
                ? "text-gold border-gold"
                : "text-muted-foreground border-transparent hover:text-parchment hover:border-muted-foreground/30"
            }`}
          >
            {section.label}
          </button>
        </li>
      ))}
    </ul>
  )
}

export function TableOfContents({ sections, heading, variant }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string | null>(null)

  // 初期表示時: 現在スクロール位置に基づいて activeId を設定
  useEffect(() => {
    const findActiveSection = () => {
      for (let i = sections.length - 1; i >= 0; i--) {
        const el = document.getElementById(sections[i].id)
        if (el && el.getBoundingClientRect().top <= window.innerHeight * 0.3) {
          setActiveId(sections[i].id)
          return
        }
      }
      if (sections.length > 0) setActiveId(sections[0].id)
    }
    findActiveSection()
  }, [sections])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        }
      },
      { rootMargin: "-10% 0px -60% 0px", threshold: 0 }
    )

    for (const section of sections) {
      const el = document.getElementById(section.id)
      if (el) observer.observe(el)
    }

    return () => observer.disconnect()
  }, [sections])

  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      setActiveId(id)
      el.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  if (variant === "desktop") {
    return (
      <div className="aged-card letterpress-border rounded-sm p-5">
        <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
          <List className="w-3.5 h-3.5" />
          {heading}
        </h3>
        <TocLinks sections={sections} activeId={activeId} onClick={scrollTo} />
      </div>
    )
  }

  // variant === "mobile"
  return (
    <div className="lg:hidden mb-8">
      <details className="aged-card letterpress-border rounded-sm">
        <summary className="px-5 py-3 cursor-pointer font-mono text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <List className="w-3.5 h-3.5" />
          {heading}
        </summary>
        <div className="px-5 pb-4">
          <TocLinks sections={sections} activeId={activeId} onClick={scrollTo} />
        </div>
      </details>
    </div>
  )
}
