"use client"

import { useCallback, useEffect, useRef, useState } from "react"
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
          <a
            href={`#${section.id}`}
            onClick={(e) => {
              e.preventDefault()
              onClick(section.id)
            }}
            className={`block text-sm font-mono py-1.5 pl-3 border-l-2 transition-colors ${
              activeId === section.id
                ? "text-gold border-gold"
                : "text-muted-foreground border-transparent hover:text-parchment hover:border-muted-foreground/30"
            }`}
          >
            {section.label}
          </a>
        </li>
      ))}
    </ul>
  )
}

export function TableOfContents({ sections, heading, variant }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string | null>(null)
  const rafRef = useRef<number>(0)

  // ビューポート上部 30% 以内に入っているセクションを下からスキャンして検出
  const findActiveSection = useCallback(() => {
    const threshold = window.innerHeight * 0.3
    for (let i = sections.length - 1; i >= 0; i--) {
      const el = document.getElementById(sections[i].id)
      if (el && el.getBoundingClientRect().top <= threshold) {
        return sections[i].id
      }
    }
    // どのセクションもまだ閾値に達していない場合は最初のセクション
    return sections.length > 0 ? sections[0].id : null
  }, [sections])

  // scroll イベント + requestAnimationFrame でスクロールスパイ
  useEffect(() => {
    // 初期検出
    setActiveId(findActiveSection())

    const onScroll = () => {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(() => {
        setActiveId(findActiveSection())
      })
    }

    window.addEventListener("scroll", onScroll, { passive: true })
    return () => {
      window.removeEventListener("scroll", onScroll)
      cancelAnimationFrame(rafRef.current)
    }
  }, [findActiveSection])

  // ページロード時に URL フラグメントがあれば該当セクションにスクロール
  useEffect(() => {
    const hash = window.location.hash.slice(1)
    if (!hash) return
    // DOM レンダリング完了を待つ
    const timer = setTimeout(() => {
      const el = document.getElementById(hash)
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" })
        setActiveId(hash)
      }
    }, 100)
    return () => clearTimeout(timer)
  }, [])

  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      setActiveId(id)
      el.scrollIntoView({ behavior: "smooth", block: "start" })
      history.replaceState(null, "", `#${id}`)
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
