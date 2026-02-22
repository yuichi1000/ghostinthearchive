import Link from "next/link"
import {
  Scroll,
  TreePine,
  Users,
  Eye,
  Building2,
  Search,
  Flame,
  MapPin,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import type { Dictionary } from "@/lib/i18n/dictionaries"
import type { SupportedLang } from "@/lib/i18n/config"

type ClassificationCode = "HIS" | "FLK" | "ANT" | "OCC" | "URB" | "CRM" | "REL" | "LOC"

const CODES: ClassificationCode[] = ["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"]

const iconMap: Record<ClassificationCode, LucideIcon> = {
  HIS: Scroll,
  FLK: TreePine,
  ANT: Users,
  OCC: Eye,
  URB: Building2,
  CRM: Search,
  REL: Flame,
  LOC: MapPin,
}

const colorMap: Record<ClassificationCode, { icon: string; border: string }> = {
  HIS: { icon: "text-amber-400", border: "border-amber-900/30" },
  FLK: { icon: "text-teal-400", border: "border-teal-900/30" },
  ANT: { icon: "text-orange-400", border: "border-orange-900/30" },
  OCC: { icon: "text-purple-400", border: "border-purple-900/30" },
  URB: { icon: "text-slate-400", border: "border-slate-700/30" },
  CRM: { icon: "text-red-400", border: "border-red-900/30" },
  REL: { icon: "text-indigo-400", border: "border-indigo-900/30" },
  LOC: { icon: "text-emerald-400", border: "border-emerald-900/30" },
}

interface ClassificationGuideProps {
  lang: SupportedLang
  dict: Dictionary
}

export function ClassificationGuide({ lang, dict }: ClassificationGuideProps) {
  return (
    <section className="py-12 md:py-16">
      <div className="container mx-auto px-4">
        <h2 className="font-serif text-2xl md:text-3xl text-parchment text-center mb-8">
          {dict.classificationGuide.heading}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {CODES.map((code) => {
            const Icon = iconMap[code]
            const colors = colorMap[code]
            return (
              <Link
                key={code}
                href={`/${lang}/archive?c=${code}`}
                className={`group block rounded-lg border ${colors.border} bg-card p-4 transition-transform hover:scale-[1.02] no-underline`}
              >
                <Icon className={`w-6 h-6 ${colors.icon} mb-2`} aria-hidden="true" />
                <p className="font-mono uppercase text-xs tracking-wider text-muted-foreground group-hover:text-gold transition-colors">
                  {code}
                </p>
                <p className="font-serif text-sm text-parchment mt-1">
                  {dict.classification[code]}
                </p>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                  {dict.classificationGuide.descriptions[code]}
                </p>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
