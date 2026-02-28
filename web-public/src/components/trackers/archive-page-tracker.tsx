"use client"

import { useEffect } from "react"
import { pushEvent } from "@/lib/analytics"

interface ArchivePageTrackerProps {
  pageNumber: number
  lang: string
}

export function ArchivePageTracker({ pageNumber, lang }: ArchivePageTrackerProps) {
  useEffect(() => {
    pushEvent({
      event: "view_archive",
      page_number: pageNumber,
      content_language: lang,
    })
  }, [pageNumber, lang])

  return null
}
