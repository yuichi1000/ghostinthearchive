import Image from "next/image"

interface ImageVariants {
  sm?: string
  md?: string
  lg?: string
  xl?: string
}

interface ResponsiveHeroImageProps {
  hero: string
  variants?: ImageVariants
  alt: string
  priority?: boolean
  className?: string
}

export function ResponsiveHeroImage({
  hero,
  variants,
  alt,
  priority = false,
  className,
}: ResponsiveHeroImageProps) {
  const hasVariants = variants && Object.keys(variants).length > 0

  if (!hasVariants) {
    return (
      <Image
        src={hero}
        alt={alt}
        width={1200}
        height={675}
        className={className ?? "w-full h-auto"}
        priority={priority}
        unoptimized={hero.includes("localhost")}
      />
    )
  }

  // Build the largest available variant as the default src
  const src = variants.xl || variants.lg || hero
  const isLocal = src.includes("localhost")

  return (
    <picture>
      {variants.sm && (
        <source
          media="(max-width: 640px)"
          srcSet={variants.sm}
          type="image/webp"
        />
      )}
      {variants.md && (
        <source
          media="(max-width: 828px)"
          srcSet={variants.md}
          type="image/webp"
        />
      )}
      {variants.lg && (
        <source
          media="(max-width: 1200px)"
          srcSet={variants.lg}
          type="image/webp"
        />
      )}
      {variants.xl && (
        <source
          media="(min-width: 1201px)"
          srcSet={variants.xl}
          type="image/webp"
        />
      )}
      <Image
        src={src}
        alt={alt}
        width={1200}
        height={675}
        className={className ?? "w-full h-auto"}
        priority={priority}
        unoptimized={isLocal}
      />
    </picture>
  )
}
