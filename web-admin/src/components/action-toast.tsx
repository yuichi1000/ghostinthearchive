import { cn } from "@ghost/shared/src/lib/utils"

interface ActionToastProps {
  message: string | null
  isError: boolean
}

export function ActionToast({ message, isError }: ActionToastProps) {
  if (!message) return null

  return (
    <div className={cn(
      "fixed top-20 right-4 z-50 px-4 py-3 rounded-sm animate-in fade-in slide-in-from-right-5",
      isError
        ? "bg-blood-red/10 border border-blood-red/30"
        : "bg-teal/20 border border-teal/30"
    )}>
      <p className={cn(
        "text-sm font-mono",
        isError ? "text-[#ff6b6b]" : "text-[#5fb3a1]"
      )}>
        {message}
      </p>
    </div>
  )
}
