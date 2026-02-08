"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import type { PipelineRun } from "@/types/mystery"
import { getRunningPipelineRuns } from "@/lib/firestore/pipeline-runs"

const POLL_INTERVAL_MS = 5000

interface UsePipelinePollingOptions {
  onPipelineCompleted?: () => void
}

export function usePipelinePolling(options: UsePipelinePollingOptions = {}) {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [isPolling, setIsPolling] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const prevRunIdsRef = useRef<Set<string>>(new Set())
  const onPipelineCompletedRef = useRef(options.onPipelineCompleted)

  // Keep callback ref up to date
  onPipelineCompletedRef.current = options.onPipelineCompleted

  const fetchRuns = useCallback(async () => {
    try {
      const runningRuns = await getRunningPipelineRuns()
      const currentIds = new Set(runningRuns.map((r) => r.id))

      // Detect completed pipelines (was running, now gone)
      const prevIds = prevRunIdsRef.current
      if (prevIds.size > 0) {
        const completedIds = [...prevIds].filter((id) => !currentIds.has(id))
        if (completedIds.length > 0 && onPipelineCompletedRef.current) {
          onPipelineCompletedRef.current()
        }
      }

      prevRunIdsRef.current = currentIds
      setRuns(runningRuns)

      // Stop polling if no more running pipelines
      if (runningRuns.length === 0 && prevIds.size > 0) {
        stopPolling()
      }
    } catch (error) {
      console.error("Failed to fetch pipeline runs:", error)
    }
  }, [])

  const startPolling = useCallback(() => {
    if (intervalRef.current) return // already polling
    setIsPolling(true)
    // Fetch immediately
    fetchRuns()
    intervalRef.current = setInterval(fetchRuns, POLL_INTERVAL_MS)
  }, [fetchRuns])

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsPolling(false)
  }, [])

  // Check for running pipelines on mount
  useEffect(() => {
    const checkInitial = async () => {
      try {
        const runningRuns = await getRunningPipelineRuns()
        if (runningRuns.length > 0) {
          setRuns(runningRuns)
          prevRunIdsRef.current = new Set(runningRuns.map((r) => r.id))
          startPolling()
        }
      } catch (error) {
        console.error("Failed initial pipeline check:", error)
      }
    }
    checkInitial()
    return () => stopPolling()
  }, [startPolling, stopPolling])

  return { runs, isPolling, startPolling, stopPolling }
}
