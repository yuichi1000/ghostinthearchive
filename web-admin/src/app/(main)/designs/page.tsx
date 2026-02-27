import { Suspense } from "react"
import DesignsContent from "./designs-content"

// useSearchParams() を使用するクライアントコンポーネントは
// Suspense バウンダリで包む必要がある（Docker ビルド時のプリレンダリングエラー回避）
export default function DesignsPage() {
  return (
    <Suspense>
      <DesignsContent />
    </Suspense>
  )
}
