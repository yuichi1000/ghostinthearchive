"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { StatusBadge } from "@/components/status-badge"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { getAllMysteries, approveMystery, archiveMystery, requestPodcast } from "@/lib/firestore/mysteries"
import type { FirestoreMystery, MysteryStatus } from "@/types/mystery"
import { PipelineSummary } from "@/components/pipeline-summary"
import { PipelineTimeline } from "@/components/pipeline-timeline"
import {
  Shield,
  FileText,
  CheckCircle,
  XCircle,
  Eye,
  Clock,
  MapPin,
  Filter,
  RefreshCw,
  Inbox,
  ChevronDown,
  ChevronUp,
  Mic,
  Loader2,
  AlertCircle,
  Search,
  Sparkles,
} from "lucide-react"

type FilterStatus = "all" | MysteryStatus | "translating"

export default function AdminPage() {
  const [filter, setFilter] = useState<FilterStatus>("all")
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([])
  const [loading, setLoading] = useState(true)
  const [actionFeedback, setActionFeedback] = useState<string | null>(null)
  const [themeInput, setThemeInput] = useState("")
  const [suggestions, setSuggestions] = useState<{ theme: string; description: string }[]>([])
  const [suggestLoading, setSuggestLoading] = useState(false)
  const [pipelineLoading, setPipelineLoading] = useState(false)

  const fetchMysteries = useCallback(async () => {
    try {
      const data = await getAllMysteries(100)
      setMysteries(data)
    } catch (error) {
      console.error("Failed to fetch mysteries:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMysteries()
  }, [fetchMysteries])

  const filteredMysteries = filter === "all"
    ? mysteries
    : mysteries.filter((m) => m.status === filter)

  const counts = {
    all: mysteries.length,
    pending: mysteries.filter((m) => m.status === "pending").length,
    translating: mysteries.filter((m) => m.status === "translating").length,
    published: mysteries.filter((m) => m.status === "published").length,
    archived: mysteries.filter((m) => m.status === "archived").length,
    error: mysteries.filter((m) => m.status === "error").length,
  }

  const handleApprove = async (id: string) => {
    try {
      await approveMystery(id)
      // Trigger translation pipeline
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mysteryId: id }),
      })
      if (!res.ok) throw new Error("Translation API request failed")
      setActionFeedback(`Case ${id} approved - translation started`)
      fetchMysteries()
      setTimeout(() => setActionFeedback(null), 3000)
    } catch (error) {
      console.error("Failed to approve:", error)
      setActionFeedback(`Failed to start translation`)
      setTimeout(() => setActionFeedback(null), 3000)
    }
  }

  const handleArchive = async (id: string) => {
    try {
      await archiveMystery(id)
      setActionFeedback(`Case ${id} archived`)
      fetchMysteries()
      setTimeout(() => setActionFeedback(null), 3000)
    } catch (error) {
      console.error("Failed to archive:", error)
    }
  }

  const handlePodcast = async (id: string) => {
    try {
      await requestPodcast(id)
      const res = await fetch("/api/podcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mysteryId: id }),
      })
      if (!res.ok) throw new Error("API request failed")
      setActionFeedback(`Podcast generation started for Case ${id}`)
      fetchMysteries()
      setTimeout(() => setActionFeedback(null), 3000)
    } catch (error) {
      console.error("Failed to start podcast:", error)
      setActionFeedback(`Failed to start podcast generation`)
      setTimeout(() => setActionFeedback(null), 3000)
    }
  }

  const handleStartPipeline = async () => {
    if (!themeInput.trim()) return
    setPipelineLoading(true)
    try {
      const res = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: themeInput.trim() }),
      })
      if (!res.ok) throw new Error("API request failed")
      setActionFeedback("調査パイプラインを開始しました")
      setThemeInput("")
      setSuggestions([])
      setTimeout(() => setActionFeedback(null), 3000)
    } catch (error) {
      console.error("Failed to start pipeline:", error)
      setActionFeedback("パイプラインの開始に失敗しました")
      setTimeout(() => setActionFeedback(null), 3000)
    } finally {
      setPipelineLoading(false)
    }
  }

  const handleSuggestThemes = async () => {
    setSuggestLoading(true)
    setSuggestions([])
    try {
      const res = await fetch("/api/suggest-theme", { method: "POST" })
      if (!res.ok) throw new Error("API request failed")
      const data = await res.json()
      setSuggestions(Array.isArray(data.suggestions) ? data.suggestions : [])
    } catch (error) {
      console.error("Failed to get suggestions:", error)
      setActionFeedback("テーマ提案の取得に失敗しました")
      setTimeout(() => setActionFeedback(null), 3000)
    } finally {
      setSuggestLoading(false)
    }
  }

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        {/* Page header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="flex items-center gap-3 px-4 py-2 bg-blood-red/10 border border-blood-red/30 rounded-sm">
            <Shield className="w-5 h-5 text-[#ff6b6b]" />
            <span className="font-mono text-sm uppercase tracking-wider text-[#ff6b6b]">
              Admin Access
            </span>
          </div>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="mb-8">
          <h1 className="font-serif text-3xl md:text-4xl text-parchment mb-2">
            Research Review Dashboard
          </h1>
          <p className="text-muted-foreground">
            Review, approve, or archive pending mystery discoveries before publication.
          </p>
        </div>

        {/* New Investigation section */}
        <div className="aged-card letterpress-border rounded-sm p-5 mb-8">
          <h2 className="font-serif text-xl text-parchment mb-4">
            新規調査
          </h2>
          <div className="flex gap-3 mb-3">
            <input
              type="text"
              value={themeInput}
              onChange={(e) => setThemeInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleStartPipeline() }}
              placeholder="調査テーマを入力（例: 1840年代のボストンにおけるスペイン関連の歴史的矛盾を調査せよ）"
              className="flex-1 px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment placeholder:text-muted-foreground focus:outline-none focus:border-gold/50"
            />
            <Button
              size="sm"
              onClick={handleStartPipeline}
              disabled={!themeInput.trim() || pipelineLoading}
              className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
            >
              {pipelineLoading ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Search className="w-4 h-4 mr-1" />
              )}
              調査開始
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSuggestThemes}
              disabled={suggestLoading}
              className="border-gold/30 text-gold hover:bg-gold/20 hover:text-gold bg-transparent"
            >
              {suggestLoading ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-1" />
              )}
              テーマ提案
            </Button>
          </div>
          {suggestions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-4">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { setThemeInput(s.theme); setSuggestions([]) }}
                  className="text-left p-3 border border-border/50 rounded-sm hover:border-gold/30 hover:bg-gold/5 transition-colors"
                >
                  <p className="text-sm font-medium text-parchment mb-1">{s.theme}</p>
                  <p className="text-xs text-muted-foreground">{s.description}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Action feedback toast */}
        {actionFeedback && (
          <div className="fixed top-20 right-4 z-50 px-4 py-3 bg-teal/20 border border-teal/30 rounded-sm animate-in fade-in slide-in-from-right-5">
            <p className="text-sm text-[#5fb3a1] font-mono">
              {actionFeedback}
            </p>
          </div>
        )}

        {/* Filter tabs */}
        <div className="flex flex-wrap items-center gap-2 mb-8 pb-4 border-b border-border">
          <Filter className="w-4 h-4 text-muted-foreground mr-2" />
          {(["all", "pending", "translating", "published", "archived", "error"] as FilterStatus[]).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                "px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm border transition-colors",
                filter === status
                  ? "bg-gold/20 text-gold border-gold/30"
                  : "bg-transparent text-muted-foreground border-border hover:border-parchment/30 hover:text-parchment"
              )}
            >
              {status === "all" ? "All Cases" : status}
              <span className="ml-2 text-muted-foreground">({counts[status]})</span>
            </button>
          ))}
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Total Cases</p>
            <p className="text-2xl font-serif text-parchment">{counts.all}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#d4af37] mb-1">Pending Review</p>
            <p className="text-2xl font-serif text-[#d4af37]">{counts.pending}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#5fb3a1] mb-1">Published</p>
            <p className="text-2xl font-serif text-[#5fb3a1]">{counts.published}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#ff6b6b] mb-1">Archived</p>
            <p className="text-2xl font-serif text-[#ff6b6b]">{counts.archived}</p>
          </div>
        </div>

        {/* Loading */}
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="aged-card letterpress-border rounded-sm p-5 h-48 animate-pulse">
                <div className="h-4 bg-muted rounded w-1/4 mb-4" />
                <div className="h-5 bg-muted rounded w-3/4 mb-2" />
                <div className="h-4 bg-muted rounded w-full mb-4" />
                <div className="h-6 bg-muted rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : filteredMysteries.length === 0 ? (
          <div className="text-center py-16">
            <Inbox className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No cases match the selected filter.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredMysteries.map((mystery) => (
              <AdminMysteryCard
                key={mystery.mystery_id}
                mystery={mystery}
                onApprove={() => handleApprove(mystery.mystery_id)}
                onArchive={() => handleArchive(mystery.mystery_id)}
                onPodcast={() => handlePodcast(mystery.mystery_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface AdminMysteryCardProps {
  mystery: FirestoreMystery
  onApprove: () => void
  onArchive: () => void
  onPodcast: () => void
}

function AdminMysteryCard({ mystery, onApprove, onArchive, onPodcast }: AdminMysteryCardProps) {
  const [showPipeline, setShowPipeline] = useState(false)
  const isPending = mystery.status === "pending"
  const isTranslating = mystery.status === "translating"
  const location = mystery.historical_context?.geographic_scope?.[0] || ""
  const timePeriod = mystery.historical_context?.time_period || ""
  const hasPipelineLog = mystery.pipeline_log && mystery.pipeline_log.length > 0

  return (
    <article className="aged-card letterpress-border rounded-sm p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <FileText className="w-3.5 h-3.5 text-gold" />
          <span>Case #{mystery.mystery_id.slice(-3).padStart(4, '0')}</span>
        </div>
        <StatusBadge status={mystery.status} />
      </div>

      {/* Title */}
      <h3 className="font-serif text-lg text-parchment mb-1 leading-tight">
        {mystery.title}
      </h3>

      {/* Summary */}
      <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-2">
        {mystery.summary}
      </p>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4 pb-4 border-b border-border/50">
        {location && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {location}
          </span>
        )}
        {timePeriod && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timePeriod}
          </span>
        )}
      </div>

      {/* Pipeline log */}
      {hasPipelineLog && (
        <div className="mb-4 pb-4 border-b border-border/50">
          <button
            onClick={() => setShowPipeline(!showPipeline)}
            className="w-full flex items-center justify-between hover:bg-muted/50 transition-colors p-1 -mx-1 rounded-sm"
          >
            <PipelineSummary logs={mystery.pipeline_log!} />
            {showPipeline ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>

          {showPipeline && (
            <div className="mt-4 pt-4 border-t border-border/50">
              <PipelineTimeline logs={mystery.pipeline_log!} />
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between gap-4">
        {mystery.status === "published" ? (
          <div className="flex items-center gap-3">
            <Link
              href={`/mystery/${mystery.mystery_id}`}
              className="inline-flex items-center gap-2 text-sm text-gold hover:text-parchment transition-colors no-underline"
            >
              <Eye className="w-4 h-4" />
              View Published
            </Link>
            {mystery.podcast_status === "generating" ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Generating...
              </span>
            ) : mystery.podcast_status === "error" ? (
              <Button
                variant="outline"
                size="sm"
                onClick={onPodcast}
                className="border-blood-red/30 text-[#ff6b6b] hover:bg-blood-red/20 hover:text-[#ff6b6b] bg-transparent"
              >
                <AlertCircle className="w-4 h-4 mr-1" />
                Retry Podcast
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={onPodcast}
                className="border-gold/30 text-gold hover:bg-gold/20 hover:text-gold bg-transparent"
              >
                <Mic className="w-4 h-4 mr-1" />
                {mystery.podcast_status === "completed" ? "Podcast 再生成" : "Podcast 作成"}
              </Button>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Link
              href={`/admin/preview/${mystery.mystery_id}`}
              className="inline-flex items-center gap-2 text-sm text-gold hover:text-parchment transition-colors no-underline"
            >
              <Eye className="w-4 h-4" />
              Preview
            </Link>
            <span className="text-xs text-muted-foreground">
              Created: {mystery.createdAt.toLocaleDateString()}
            </span>
          </div>
        )}

        {isPending && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onArchive}
              className="border-blood-red/30 text-[#ff6b6b] hover:bg-blood-red/20 hover:text-[#ff6b6b] bg-transparent"
            >
              <XCircle className="w-4 h-4 mr-1" />
              Archive
            </Button>
            <Button
              size="sm"
              onClick={onApprove}
              className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Approve
            </Button>
          </div>
        )}

        {isTranslating && (
          <span className="inline-flex items-center gap-1.5 text-xs text-gold font-mono">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Translating...
          </span>
        )}

        {mystery.status === "archived" && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-parchment"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Reconsider
          </Button>
        )}

        {mystery.status === "error" && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onArchive}
              className="border-blood-red/30 text-[#ff6b6b] hover:bg-blood-red/20 hover:text-[#ff6b6b] bg-transparent"
            >
              <XCircle className="w-4 h-4 mr-1" />
              Archive
            </Button>
            <Button
              size="sm"
              onClick={onApprove}
              className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Retry Translation
            </Button>
          </div>
        )}
      </div>
    </article>
  )
}
