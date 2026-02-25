"use client"

import { useState } from "react"

// 4言語のアーカイブ画像ラベル
const IMAGE_LABEL: Record<string, string> = {
  en: "Archival Image",
  ja: "アーカイブ資料",
  es: "Imagen de archivo",
  de: "Archivbild",
}

interface ArchiveImageProps {
  src?: string
  alt?: string
  lang: string
}

export function ArchiveImage({ src, alt, lang }: ArchiveImageProps) {
  const [hasError, setHasError] = useState(false)

  if (!src || hasError) return null

  const label = IMAGE_LABEL[lang] || IMAGE_LABEL.en

  return (
    <figure className="not-prose my-8 mx-auto w-fit max-w-3xl">
      <img
        src={src}
        alt={alt || label}
        loading="lazy"
        onError={() => setHasError(true)}
        className="h-auto max-w-full"
      />
      {alt && (
        <figcaption className="mt-2 text-center text-xs font-mono text-muted-foreground/70 leading-relaxed">
          <span className="uppercase tracking-wider text-gold/60">{label}</span>
          {" — "}
          {alt}
        </figcaption>
      )}
    </figure>
  )
}
