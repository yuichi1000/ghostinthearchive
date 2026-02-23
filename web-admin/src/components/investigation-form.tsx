import { Button } from "@ghost/shared/src/components/ui/button"
import {
  Loader2,
  Search,
  Sparkles,
} from "lucide-react"

const STORYTELLER_OPTIONS = [
  { value: "claude", label: "Claude Sonnet 4.5" },
  { value: "gemini", label: "Gemini 3 Pro" },
  { value: "gpt", label: "GPT-4o" },
  { value: "llama", label: "Llama 4 Maverick" },
  { value: "deepseek", label: "DeepSeek V3" },
  { value: "mistral", label: "Mistral Large" },
] as const

interface ThemeSuggestion {
  theme: string
  description: string
  theme_ja?: string
  description_ja?: string
}

interface InvestigationFormProps {
  themeInput: string
  onThemeInputChange: (value: string) => void
  storyteller: string
  onStorytellerChange: (value: string) => void
  suggestions: ThemeSuggestion[]
  onSelectSuggestion: (theme: string) => void
  suggestLoading: boolean
  pipelineLoading: boolean
  onStartPipeline: () => void
  onSuggestThemes: () => void
}

export function InvestigationForm({
  themeInput,
  onThemeInputChange,
  storyteller,
  onStorytellerChange,
  suggestions,
  onSelectSuggestion,
  suggestLoading,
  pipelineLoading,
  onStartPipeline,
  onSuggestThemes,
}: InvestigationFormProps) {
  return (
    <div className="aged-card letterpress-border rounded-sm p-5 mb-8">
      <h2 className="font-serif text-xl text-parchment mb-4">
        新規調査
      </h2>
      <div className="flex gap-3 mb-3">
        <input
          type="text"
          value={themeInput}
          onChange={(e) => onThemeInputChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") onStartPipeline() }}
          placeholder="調査テーマを入力（例: 1840年代のボストンにおけるスペイン関連の歴史的矛盾を調査せよ）"
          className="flex-1 px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment placeholder:text-muted-foreground focus:outline-none focus:border-gold/50"
        />
        <select
          value={storyteller}
          onChange={(e) => onStorytellerChange(e.target.value)}
          className="px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment focus:outline-none focus:border-gold/50"
        >
          {STORYTELLER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <Button
          size="sm"
          onClick={onStartPipeline}
          disabled={!themeInput.trim() || pipelineLoading}
          className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
        >
          {pipelineLoading ? (
            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
          ) : (
            <Search className="w-4 h-4 mr-1" />
          )}
          調査開始
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onSuggestThemes}
          disabled={suggestLoading}
          className="border-gold/30 text-gold hover:bg-gold/20 hover:text-gold bg-transparent"
        >
          {suggestLoading ? (
            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 mr-1" />
          )}
          テーマ提案
        </Button>
      </div>
      {suggestions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-4">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSelectSuggestion(s.theme)}
              className="text-left p-3 border border-border/50 rounded-sm hover:border-gold/30 hover:bg-gold/5 transition-colors"
            >
              <p className="text-sm font-medium text-parchment mb-1">{s.theme}</p>
              {s.theme_ja && (
                <p className="text-xs text-muted-foreground mb-1">{s.theme_ja}</p>
              )}
              <p className="text-xs text-muted-foreground">{s.description_ja || s.description}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
