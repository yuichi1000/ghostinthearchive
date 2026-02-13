"use client"

import { useRef, useState, useEffect, useCallback } from "react"
import { Play, Pause, Download } from "lucide-react"
import { Button } from "@ghost/shared/src/components/ui/button"

/**
 * 秒数を mm:ss 形式にフォーマットする
 */
function formatTime(seconds: number): string {
  if (!isFinite(seconds) || isNaN(seconds)) return "0:00"
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, "0")}`
}

interface AudioPlayerProps {
  src: string
  downloadUrl?: string
  className?: string
}

export function AudioPlayer({ src, downloadUrl, className }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => setCurrentTime(audio.currentTime)
    const onDurationChange = () => setDuration(audio.duration)
    const onEnded = () => setPlaying(false)

    audio.addEventListener("timeupdate", onTimeUpdate)
    audio.addEventListener("durationchange", onDurationChange)
    audio.addEventListener("ended", onEnded)

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate)
      audio.removeEventListener("durationchange", onDurationChange)
      audio.removeEventListener("ended", onEnded)
    }
  }, [])

  const togglePlay = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    if (playing) {
      audio.pause()
    } else {
      audio.play()
    }
    setPlaying(!playing)
  }, [playing])

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current
    const bar = progressRef.current
    if (!audio || !bar || !duration) return

    const rect = bar.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    audio.currentTime = ratio * duration
  }, [duration])

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className={className}>
      <audio ref={audioRef} src={src} preload="metadata" />

      <div className="aged-card letterpress-border rounded-sm p-4">
        <div className="flex items-center gap-4">
          {/* 再生/一時停止ボタン */}
          <button
            onClick={togglePlay}
            className="w-10 h-10 flex items-center justify-center rounded-full bg-gold/20 border border-gold/30 text-[#d4af37] hover:bg-gold/30 transition-colors flex-shrink-0"
          >
            {playing ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4 ml-0.5" />
            )}
          </button>

          {/* プログレスバー + 時間表示 */}
          <div className="flex-1 min-w-0">
            <div
              ref={progressRef}
              onClick={handleSeek}
              className="w-full h-2 bg-muted rounded-full cursor-pointer group"
            >
              <div
                className="h-full bg-gold/60 rounded-full transition-[width] duration-100 group-hover:bg-gold/80"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-xs font-mono text-muted-foreground">
                {formatTime(currentTime)}
              </span>
              <span className="text-xs font-mono text-muted-foreground">
                {formatTime(duration)}
              </span>
            </div>
          </div>

          {/* ダウンロードボタン */}
          {downloadUrl && (
            <Button
              variant="outline"
              size="sm"
              asChild
              className="border-gold/30 text-gold hover:bg-gold/20 bg-transparent flex-shrink-0"
            >
              <a href={downloadUrl} download>
                <Download className="w-4 h-4" />
              </a>
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
