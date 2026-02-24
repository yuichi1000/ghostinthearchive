"use client"

import type { ProductDesignProposal, DesignAsset } from "@ghost/shared/src/types/mystery"
import { Shirt, Coffee, Type, Paintbrush, Download } from "lucide-react"

interface DesignProposalViewerProps {
  products: ProductDesignProposal[]
  assets?: DesignAsset[]
}

const productIcons: Record<string, React.ReactNode> = {
  tshirt: <Shirt className="w-5 h-5" />,
  mug: <Coffee className="w-5 h-5" />,
}

const productLabels: Record<string, string> = {
  tshirt: "T-Shirt",
  mug: "Mug",
}

export function DesignProposalViewer({ products, assets }: DesignProposalViewerProps) {
  return (
    <div className="space-y-6">
      {products.map((product, index) => {
        // このプロダクトに対応するアセットをフィルタ
        const productAssets = assets?.filter(
          (a) => a.product_type === product.product_type
        ) ?? []

        return (
          <div
            key={`${product.product_type}-${index}`}
            className="aged-card letterpress-border rounded-sm p-5"
          >
            {/* 製品ヘッダー */}
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-10 h-10 bg-gold/10 border border-gold/30 rounded-sm text-[#d4af37]">
                {productIcons[product.product_type] || <Paintbrush className="w-5 h-5" />}
              </div>
              <div>
                <h3 className="font-mono text-sm uppercase tracking-wider text-parchment">
                  {productLabels[product.product_type] || product.product_type}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {product.aspect_ratio} | {product.style_reference}
                </p>
              </div>
            </div>

            {/* アセット画像（ある場合のみ） */}
            {productAssets.length > 0 && (
              <div className="grid grid-cols-2 gap-3 mb-4">
                {productAssets.map((asset, i) => (
                  <div
                    key={`${asset.product_type}-${asset.layer}-${i}`}
                    className="border border-border/50 rounded-sm overflow-hidden bg-muted/20"
                  >
                    {/* 画像プレビュー */}
                    <div className="relative aspect-video">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={asset.public_url}
                        alt={`${asset.product_type} ${asset.layer}`}
                        className="w-full h-full object-contain"
                      />
                    </div>
                    {/* レイヤー名 + DL ボタン */}
                    <div className="p-2 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-mono text-parchment uppercase">
                          {asset.layer}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {asset.aspect_ratio}
                        </p>
                      </div>
                      <a
                        href={asset.public_url}
                        download
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-gold border border-gold/30 rounded-sm hover:bg-gold/20 transition-colors no-underline"
                      >
                        <Download className="w-3.5 h-3.5" />
                        DL
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* キャッチフレーズ */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Type className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  Catchphrase
                </span>
              </div>
              <div className="space-y-1 pl-6">
                <p className="text-sm font-serif text-parchment italic">
                  &ldquo;{product.catchphrase_en}&rdquo;
                </p>
                <p className="text-sm text-foreground/80">
                  {product.catchphrase_ja}
                </p>
              </div>
            </div>

            {/* カラーパレット */}
            <div className="mb-4">
              <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                Color Palette
              </span>
              <p className="text-xs text-muted-foreground/70 mt-1">
                記事のトーンと地域性に基づく推奨配色。印刷発注・Canva/Adobe でのテキスト配置に使用。
              </p>
              <div className="flex items-center gap-2 mt-2">
                {product.color_palette.map((color, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <div
                      className="w-8 h-8 rounded-sm border border-border/50"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                    <span className="text-xs font-mono text-muted-foreground">
                      {color}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* フォント提案 */}
            <div className="mb-4">
              <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                Font
              </span>
              <p className="text-sm text-foreground/80 mt-1">
                {product.font_suggestion}
              </p>
            </div>

            {/* 構図 */}
            <div>
              <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                Composition
              </span>
              <p className="text-xs text-muted-foreground/70 mt-1">
                レンダリング画像の空間構成・視覚的レイアウトの設計意図。
              </p>
              <p className="text-sm text-foreground/80 mt-1 leading-relaxed">
                {product.composition}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
