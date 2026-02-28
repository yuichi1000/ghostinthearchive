"use client"

import { useEffect } from "react"
import { pushEvent } from "@/lib/analytics"

interface MysteryPageTrackerProps {
  mysteryId: string
  classification: string
  confidenceLevel: string
  lang: string
}

export function MysteryPageTracker({
  mysteryId,
  classification,
  confidenceLevel,
  lang,
}: MysteryPageTrackerProps) {
  useEffect(() => {
    pushEvent({
      event: "view_mystery",
      mystery_id: mysteryId,
      classification,
      confidence_level: confidenceLevel,
      content_language: lang,
    })
  }, [mysteryId, classification, confidenceLevel, lang])

  return null
}
