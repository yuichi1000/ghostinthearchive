"use client"

import { useState, useCallback, useEffect } from "react"
import Link from "next/link"
import { Button } from "@ghost/shared/src/components/ui/button"
import { useDesign } from "@/hooks/use-design"
import { usePipelineRun } from "@/hooks/use-pipeline-run"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import { DesignStatusBadge } from "@/components/design-status-badge"
import { DesignProposalViewer } from "@/components/design-proposal-viewer"
import { DesignAssetGallery } from "@/components/design-asset-gallery"
import { ActionToast } from "@/components/action-toast"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import {
  ArrowLeft,
  Image,
  Loader2,
  RefreshCw,
  AlertTriangle,
} from "lucide-react"

interface DesignDetailProps {
  designId: string
}

export function DesignDetail({ designId }: DesignDetailProps) {
  const design = useDesign(designId)
  const pipelineRun = usePipelineRun(design?.pipeline_run_id ?? null)

  const [rendering, setRendering] = useState(false)
  const feedback = useActionFeedback()

  // design のステータスが rendering に変わったらローカルフラグをリセット
  useEffect(() => {
    if (design?.status === "rendering") {
      setRendering(false)
    }
  }, [design?.status])

  const handleRenderAssets = useCallback(async () => {
    if (!design) return
    setRendering(true)
    try {
      const res = await fetch("/api/design/render-assets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ design_id: designId }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      feedback.showSuccess("レンダリングを開始しました")
    } catch (error) {
      console.error("Failed to start rendering:", error)
      setRendering(false)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`レンダリングの開始に失敗しました: ${message}`)
    }
  }, [design, designId])

  const handleRetry = useCallback(async () => {
    if (!design) return
    try {
      const res = await fetch("/api/design/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mystery_id: design.mystery_id }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()
      if (data.design_id) {
        window.location.href = `/designs/${data.design_id}`
      }
    } catch (error) {
      console.error("Failed to retry:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`再試行に失敗しました: ${message}`)
    }
  }, [design])

  // ローディング中
  if (!design) {
    return (
      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-4 mb-8">
            <Link
              href="/designs"
              className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
            >
              <ArrowLeft className="w-4 h-4" />
              Designs 一覧
            </Link>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-8 animate-pulse">
            <div className="h-6 bg-muted rounded w-1/3 mb-4" />
            <div className="h-4 bg-muted rounded w-2/3 mb-2" />
            <div className="h-4 bg-muted rounded w-1/2" />
          </div>
        </div>
      </div>
    )
  }

  const isProcessing = design.status === "designing" || design.status === "rendering"
  const canRender = design.status === "design_ready"
  const isRenderReady = design.status === "render_ready"

  // render_ready 時: アセットが存在するプロダクトのみ表示
  const assetsForViewer = isRenderReady ? (design.assets ?? []) : undefined
  const productsForViewer = (() => {
    const allProducts = design.proposal?.products ?? []
    if (!isRenderReady || !design.assets || design.assets.length === 0) {
      return allProducts
    }
    // アセットが存在する product_type のみフィルタ
    const assetProductTypes = new Set(design.assets.map((a) => a.product_type))
    return allProducts.filter((p) => assetProductTypes.has(p.product_type))
  })()

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        <ActionToast message={feedback.message} isError={feedback.isError} />

        {/* パンくずリスト */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/designs"
            className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Designs 一覧
          </Link>
        </div>

        {/* ヘッダー */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="font-serif text-2xl md:text-3xl text-parchment mb-2">
              {design.mystery_title}
            </h1>
            <p className="text-sm text-muted-foreground">
              {design.region && `Region: ${design.region} | `}
              作成: {design.created_at.toLocaleDateString()}
            </p>
          </div>
          <DesignStatusBadge status={design.status} />
        </div>

        {/* パイプライン進捗表示 */}
        {isProcessing && pipelineRun && (
          <div className="mb-6">
            <ActivePipelinePanel
              run={pipelineRun}
              onDismiss={() => {}}
            />
          </div>
        )}

        {/* スケルトン: デザイン生成中 */}
        {design.status === "designing" && !pipelineRun && (
          <div className="aged-card letterpress-border rounded-sm p-8 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 text-[#d4af37] animate-spin" />
              <span className="font-mono text-sm text-[#d4af37]">
                デザインを生成中...
              </span>
            </div>
            <div className="space-y-3 animate-pulse">
              <div className="h-4 bg-muted rounded w-2/3" />
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-4 bg-muted rounded w-3/4" />
            </div>
          </div>
        )}

        {/* エラー表示 */}
        {design.status === "error" && (
          <div className="aged-card letterpress-border rounded-sm p-6 mb-6 border-blood-red/30">
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="w-5 h-5 text-[#ff6b6b]" />
              <span className="font-mono text-sm text-[#ff6b6b]">
                エラーが発生しました
              </span>
            </div>
            {design.error_message && (
              <div className="bg-blood-red/10 border border-blood-red/20 rounded-sm p-3 mb-4">
                <p className="text-xs text-[#ff6b6b] font-mono">
                  {design.error_message}
                </p>
              </div>
            )}
            <Button
              size="sm"
              onClick={handleRetry}
              className="bg-gold/20 border border-gold/30 text-[#d4af37] hover:bg-gold/30"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              再試行
            </Button>
          </div>
        )}

        {/* デザイン提案ビューアー（render_ready 時は統合カード表示） */}
        {design.proposal?.products && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-mono text-sm uppercase tracking-wider text-parchment">
                Design Proposals
              </h2>

              {/* レンダリングボタン */}
              {canRender && (
                <Button
                  size="sm"
                  onClick={handleRenderAssets}
                  disabled={rendering}
                  className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
                >
                  {rendering ? (
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <Image className="w-4 h-4 mr-1" />
                  )}
                  アセット生成
                </Button>
              )}
            </div>

            {/* render_ready でアセットが全て失敗した場合 */}
            {isRenderReady && productsForViewer.length === 0 && (
              <div className="aged-card letterpress-border rounded-sm p-6">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-[#ff6b6b]" />
                  <span className="text-sm text-[#ff6b6b]">
                    アセットの生成に失敗しました
                  </span>
                </div>
              </div>
            )}

            {productsForViewer.length > 0 && (
              <DesignProposalViewer
                products={productsForViewer}
                assets={assetsForViewer}
              />
            )}
          </div>
        )}

        {/* アセットギャラリー（render_ready 時は統合カードで表示するため非表示） */}
        {!isRenderReady && design.assets && design.assets.length > 0 && (
          <div className="mb-6">
            <h2 className="font-mono text-sm uppercase tracking-wider text-parchment mb-4">
              Generated Assets
            </h2>
            <DesignAssetGallery assets={design.assets} />
          </div>
        )}

        {/* レンダリング中スケルトン */}
        {design.status === "rendering" && !pipelineRun && (
          <div className="aged-card letterpress-border rounded-sm p-8 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 text-[#d4af37] animate-spin" />
              <span className="font-mono text-sm text-[#d4af37]">
                アセットをレンダリング中...
              </span>
            </div>
            <div className="space-y-3 animate-pulse">
              <div className="h-32 bg-muted rounded w-full" />
              <div className="h-32 bg-muted rounded w-full" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
