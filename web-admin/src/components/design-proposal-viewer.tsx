"use client"

import type { ProductDesignProposal } from "@ghost/shared/src/types/mystery"
import { Shirt, Coffee, Type, Paintbrush } from "lucide-react"

interface DesignProposalViewerProps {
  products: ProductDesignProposal[]
}

const productIcons: Record<string, React.ReactNode> = {
  tshirt: <Shirt className="w-5 h-5" />,
  mug: <Coffee className="w-5 h-5" />,
}

const productLabels: Record<string, string> = {
  tshirt: "T-Shirt",
  mug: "Mug",
}

export function DesignProposalViewer({ products }: DesignProposalViewerProps) {
  return (
    <div className="space-y-6">
      {products.map((product, index) => (
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
            <p className="text-sm text-foreground/80 mt-1 leading-relaxed">
              {product.composition}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
