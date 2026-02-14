"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { PodcastScript, PodcastSegment } from "@ghost/shared/src/types/mystery"
import { FileText, Music } from "lucide-react"

const segmentTypeConfig: Record<PodcastSegment["type"], { label: string; className: string }> = {
  overview: {
    label: "OVERVIEW",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  act_i: {
    label: "ACT I",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  act_ii: {
    label: "ACT II",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  act_iii: {
    label: "ACT III",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  act_iiii: {
    label: "ACT IIII",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  // レガシー（後方互換）
  intro: {
    label: "INTRO",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  body: {
    label: "BODY",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  outro: {
    label: "OUTRO",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
}

interface ScriptEditorProps {
  script: PodcastScript
  scriptJa?: string
  readOnly?: boolean
  onChange?: (script: PodcastScript) => void
}

export function ScriptEditor({ script, scriptJa, readOnly = false, onChange }: ScriptEditorProps) {
  const [localScript, setLocalScript] = useState<PodcastScript>(script)
  // 外部から script が変わった場合（例: onSnapshot 更新）、
  // ユーザーが編集中でなければ追従する
  const hasUserEdited = useRef(false)

  useEffect(() => {
    if (!hasUserEdited.current) {
      setLocalScript(script)
    }
  }, [script])

  const handleSegmentChange = useCallback(
    (index: number, field: "label" | "text", value: string) => {
      hasUserEdited.current = true
      setLocalScript((prev) => {
        const newSegments = [...prev.segments]
        newSegments[index] = { ...newSegments[index], [field]: value }
        const updated = { ...prev, segments: newSegments }
        onChange?.(updated)
        return updated
      })
    },
    [onChange]
  )

  const handleTitleChange = useCallback(
    (value: string) => {
      hasUserEdited.current = true
      setLocalScript((prev) => {
        const updated = { ...prev, episode_title: value }
        onChange?.(updated)
        return updated
      })
    },
    [onChange]
  )

  // 日本語訳を段落ごとに分割
  const jaParagraphs = scriptJa?.split("\n").filter((line) => line.trim()) || []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 左: 英語脚本（編集可能） */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-4 h-4 text-gold" />
          <h3 className="font-mono text-sm uppercase tracking-wider text-parchment">
            English Script
          </h3>
        </div>

        {/* エピソードタイトル */}
        <div className="mb-4">
          <label className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1 block">
            Episode Title
          </label>
          {readOnly ? (
            <p className="text-sm text-parchment font-serif">
              {localScript.episode_title}
            </p>
          ) : (
            <input
              type="text"
              value={localScript.episode_title}
              onChange={(e) => handleTitleChange(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment focus:outline-none focus:border-gold/50"
            />
          )}
          {localScript.estimated_duration_minutes > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              {localScript.estimated_duration_minutes} min
            </p>
          )}
        </div>

        {/* セグメント一覧 */}
        <div className="space-y-4">
          {localScript.segments.map((segment, index) => (
            <div
              key={index}
              className="aged-card letterpress-border rounded-sm p-4"
            >
              {/* セグメント種別バッジ + ラベル */}
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={cn(
                    "inline-flex items-center text-[10px] px-2 py-0.5 rounded-sm border font-mono uppercase tracking-wider",
                    segmentTypeConfig[segment.type].className
                  )}
                >
                  {segmentTypeConfig[segment.type].label}
                </span>
                {readOnly ? (
                  <span className="text-xs font-mono text-muted-foreground">
                    {segment.label}
                  </span>
                ) : (
                  <input
                    type="text"
                    value={segment.label}
                    onChange={(e) => handleSegmentChange(index, "label", e.target.value)}
                    className="flex-1 px-2 py-1 bg-background border border-border rounded-sm text-xs font-mono text-parchment focus:outline-none focus:border-gold/50"
                  />
                )}
              </div>

              {/* セグメントテキスト */}
              {readOnly ? (
                <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">
                  {segment.text}
                </p>
              ) : (
                <AutoResizeTextarea
                  value={segment.text}
                  onChange={(value) => handleSegmentChange(index, "text", value)}
                />
              )}

              {/* SFX notes（読み取り専用） */}
              {segment.notes && (
                <div className="flex items-center gap-1.5 mt-2 text-xs text-muted-foreground">
                  <Music className="w-3 h-3" />
                  <span className="italic">{segment.notes}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 右: 日本語訳（読み取り専用） */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-4 h-4 text-gold" />
          <h3 className="font-mono text-sm uppercase tracking-wider text-parchment">
            日本語訳
          </h3>
        </div>

        {jaParagraphs.length > 0 ? (
          <div className="aged-card letterpress-border rounded-sm p-4">
            <div className="space-y-3">
              {jaParagraphs.map((paragraph, index) => (
                <p
                  key={index}
                  className="text-sm text-foreground/80 leading-relaxed"
                >
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        ) : (
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-sm text-muted-foreground italic">
              日本語訳はまだ生成されていません
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 自動リサイズ textarea
 */
function AutoResizeTextarea({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${el.scrollHeight}px`
  }, [value])

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={3}
      className="w-full px-3 py-2 bg-background border border-border rounded-sm text-sm text-foreground/80 leading-relaxed resize-none focus:outline-none focus:border-gold/50"
    />
  )
}
