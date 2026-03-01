import { Button } from "@ghost/shared/src/components/ui/button"
import {
  Check,
  Loader2,
  Search,
  Sparkles,
  X,
} from "lucide-react"

const STORYTELLER_OPTIONS = [
  { value: "claude", label: "Claude Sonnet 4.6" },
  { value: "gemini", label: "Gemini 3 Pro" },
  { value: "gpt", label: "GPT-4.1" },
  { value: "llama", label: "Llama 4 Maverick" },
  { value: "deepseek", label: "DeepSeek V3.2" },
  { value: "mistral", label: "Mistral Large" },
] as const

// API キー → 表示名マッピング
const API_DISPLAY_NAMES: Record<string, string> = {
  us_archives: "US Archives",
  europeana: "Europeana",
  internet_archive: "Internet Archive",
  ndl: "NDL",
  delpher: "Delpher",
  trove: "Trove",
}

// カバレッジスコアの色分け
const COVERAGE_BADGE_STYLES: Record<string, string> = {
  HIGH: "bg-emerald-900/40 text-emerald-400 border-emerald-700/50",
  MEDIUM: "bg-amber-900/40 text-amber-400 border-amber-700/50",
  LOW: "bg-red-900/40 text-red-400 border-red-700/50",
}

interface ThemeSuggestion {
  theme: string
  description: string
  theme_ja?: string
  description_ja?: string
  coverage_score?: "HIGH" | "MEDIUM" | "LOW"
  primary_apis?: string[]
  probe_hits?: Record<string, boolean>
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
              <div className="flex items-center gap-2 mb-1">
                <p className="text-sm font-medium text-parchment flex-1">{s.theme}</p>
                {s.coverage_score && (
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${COVERAGE_BADGE_STYLES[s.coverage_score]}`}>
                    {s.coverage_score}
                  </span>
                )}
              </div>
              {s.theme_ja && (
                <p className="text-xs text-muted-foreground mb-1">{s.theme_ja}</p>
              )}
              <p className="text-xs text-muted-foreground mb-1.5">{s.description_ja || s.description}</p>
              {s.probe_hits && Object.keys(s.probe_hits).length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {Object.entries(s.probe_hits).map(([api, found]) => (
                    <span
                      key={api}
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded inline-flex items-center gap-1 ${
                        found
                          ? "bg-border/30 text-muted-foreground"
                          : "bg-border/10 text-muted-foreground/40"
                      }`}
                    >
                      {API_DISPLAY_NAMES[api] || api}
                      {found
                        ? <Check className="w-3 h-3 text-emerald-400" />
                        : <X className="w-3 h-3 text-red-400/50" />
                      }
                    </span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
