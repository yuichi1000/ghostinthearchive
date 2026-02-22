"use client"

import { useState, useRef, useCallback } from "react"

export interface ActionFeedback {
  message: string | null
  isError: boolean
  showSuccess: (msg: string) => void
  showError: (msg: string) => void
  clear: () => void
}

export function useActionFeedback(): ActionFeedback {
  const [message, setMessage] = useState<string | null>(null)
  const [isError, setIsError] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const clear = useCallback(() => {
    clearTimer()
    setMessage(null)
    setIsError(false)
  }, [clearTimer])

  const showSuccess = useCallback((msg: string) => {
    clearTimer()
    setMessage(msg)
    setIsError(false)
    timerRef.current = setTimeout(() => setMessage(null), 3000)
  }, [clearTimer])

  const showError = useCallback((msg: string) => {
    clearTimer()
    setMessage(msg)
    setIsError(true)
    timerRef.current = setTimeout(() => setMessage(null), 5000)
  }, [clearTimer])

  return { message, isError, showSuccess, showError, clear }
}
