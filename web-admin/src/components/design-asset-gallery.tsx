"use client"

import { useState } from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { DesignAsset, ProductType } from "@ghost/shared/src/types/mystery"
import { Download, Image, Shirt, Coffee } from "lucide-react"

interface DesignAssetGalleryProps {
  assets: DesignAsset[]
}

const productIcons: Record<string, React.ReactNode> = {
  tshirt: <Shirt className="w-4 h-4" />,
  mug: <Coffee className="w-4 h-4" />,
}

const productLabels: Record<string, string> = {
  tshirt: "T-Shirt",
  mug: "Mug",
}

export function DesignAssetGallery({ assets }: DesignAssetGalleryProps) {
  // 製品タイプごとにグループ化
  const productTypes = [...new Set(assets.map((a) => a.product_type))]
  const [activeTab, setActiveTab] = useState<ProductType>(productTypes[0] || "tshirt")

  const filteredAssets = assets.filter((a) => a.product_type === activeTab)

  return (
    <div>
      {/* タブ */}
      {productTypes.length > 1 && (
        <div className="flex items-center gap-2 mb-4">
          {productTypes.map((type) => (
            <button
              key={type}
              onClick={() => setActiveTab(type)}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm border transition-colors",
                activeTab === type
                  ? "bg-gold/20 text-gold border-gold/30"
                  : "bg-transparent text-muted-foreground border-border hover:border-parchment/30 hover:text-parchment"
              )}
            >
              {productIcons[type]}
              {productLabels[type] || type}
              <span className="ml-1 text-muted-foreground">
                ({assets.filter((a) => a.product_type === type).length})
              </span>
            </button>
          ))}
        </div>
      )}

      {/* アセットグリッド */}
      {filteredAssets.length === 0 ? (
        <div className="text-center py-8">
          <Image className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            このタイプのアセットはまだ生成されていません。
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAssets.map((asset, index) => (
            <div
              key={`${asset.product_type}-${asset.layer}-${index}`}
              className="aged-card letterpress-border rounded-sm overflow-hidden"
            >
              {/* 画像プレビュー */}
              <div className="relative bg-muted/20 aspect-video">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={asset.public_url}
                  alt={`${asset.product_type} ${asset.layer}`}
                  className="w-full h-full object-contain"
                />
              </div>

              {/* メタデータ + ダウンロード */}
              <div className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono text-parchment uppercase">
                    {asset.layer}
                  </p>
                  <p className="text-xs text-muted-foreground">
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
    </div>
  )
}
