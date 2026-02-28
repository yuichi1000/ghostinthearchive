// GA4 カスタムイベント送信ユーティリティ
// GTM の dataLayer.push を型安全にラップする

interface ViewMysteryEvent {
  event: "view_mystery"
  mystery_id: string
  classification: string
  confidence_level: string
  content_language: string
}

interface ViewArchiveEvent {
  event: "view_archive"
  page_number: number
  content_language: string
}

type GA4Event = ViewMysteryEvent | ViewArchiveEvent

export function pushEvent(event: GA4Event): void {
  if (typeof window !== "undefined" && Array.isArray(window.dataLayer)) {
    window.dataLayer.push(event)
  }
}

// GTM の dataLayer は任意のオブジェクトを受け付ける
declare global {
  interface Window {
    dataLayer?: unknown[]
  }
}
