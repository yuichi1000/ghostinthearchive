"use client"

import { useEffect, useRef } from "react"

export function Hero() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resizeCanvas()
    window.addEventListener("resize", resizeCanvas)

    interface Particle {
      x: number
      y: number
      size: number
      speedX: number
      speedY: number
      opacity: number
    }

    const particles: Particle[] = []
    const particleCount = 50

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        speedX: (Math.random() - 0.5) * 0.3,
        speedY: (Math.random() - 0.5) * 0.2,
        opacity: Math.random() * 0.3 + 0.1,
      })
    }

    let animationId: number

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      particles.forEach((particle) => {
        particle.x += particle.speedX
        particle.y += particle.speedY

        if (particle.x < 0) particle.x = canvas.width
        if (particle.x > canvas.width) particle.x = 0
        if (particle.y < 0) particle.y = canvas.height
        if (particle.y > canvas.height) particle.y = 0

        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(212, 197, 160, ${particle.opacity})`
        ctx.fill()
      })

      animationId = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener("resize", resizeCanvas)
      cancelAnimationFrame(animationId)
    }
  }, [])

  return (
    <section className="relative min-h-[70vh] flex items-center justify-center overflow-hidden">
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        aria-hidden="true"
      />

      <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-background/50 via-transparent to-background/50 pointer-events-none" />

      <div className="relative z-10 container mx-auto px-4 text-center">
        <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 border border-blood-red/30 bg-blood-red/10 rounded-sm">
          <span className="w-2 h-2 bg-blood-red rounded-full animate-pulse" />
          <span className="text-xs font-mono uppercase tracking-widest text-[#ff6b6b]">
            Active Research Protocol
          </span>
        </div>

        <h1 className="font-serif text-5xl md:text-7xl lg:text-8xl text-parchment mb-4 tracking-tight text-balance">
          Ghost in the Archive
        </h1>

        <p className="text-lg md:text-xl text-muted-foreground mb-6">
          AI-driven excavation of historical ghosts from the depths of the archives
        </p>

        <p className="text-base md:text-lg text-foreground/70 max-w-2xl mx-auto leading-relaxed mb-8 text-pretty">
          Unearthing contradictions, anomalies, and unexplained patterns buried in the depths of public digital archives.
          Where historical record meets folkloric mystery.
        </p>

        <div className="flex items-center justify-center gap-4 text-muted-foreground">
          <div className="h-px w-16 bg-gradient-to-r from-transparent to-border" />
          <span className="text-xs font-mono uppercase tracking-widest">
            LOC • DPLA • NYPL • Internet Archive
          </span>
          <div className="h-px w-16 bg-gradient-to-l from-transparent to-border" />
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none" />
    </section>
  )
}
