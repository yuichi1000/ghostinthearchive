import { Suspense } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Hero } from "@/components/hero"
import { MysteryCard } from "@/components/mystery-card"
import { MysteryCardSkeleton } from "@/components/mystery-card-skeleton"
import { getPublishedMysteries } from "@/lib/firestore/mysteries"
import { HOMEPAGE_MYSTERY_LIMIT } from "@/lib/constants"
import { FileStack, Search, ShieldAlert } from "lucide-react"

async function MysteryList() {
  let mysteries: Awaited<ReturnType<typeof getPublishedMysteries>> = []
  try {
    mysteries = await getPublishedMysteries(HOMEPAGE_MYSTERY_LIMIT)
  } catch (error) {
    console.error("[MysteryList] Failed to fetch mysteries:", error)
  }

  if (mysteries.length === 0) {
    return (
      <div className="text-center py-16">
        <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
        <h2 className="font-serif text-xl text-parchment mb-2">
          No Mysteries Yet
        </h2>
        <p className="text-muted-foreground">
          No published mysteries at this time. Check back for new discoveries.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {mysteries.map((mystery) => (
        <MysteryCard key={mystery.mystery_id} mystery={mystery} />
      ))}
    </div>
  )
}

function MysteryListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <MysteryCardSkeleton key={i} />
      ))}
    </div>
  )
}

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header />

      <main className="flex-1">
        <Hero />

        {/* Operational Disclosure */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <div className="border border-gold/20 bg-gold/5 rounded-sm p-6 md:p-8">
                <div className="flex items-center gap-3 mb-6 justify-center">
                  <ShieldAlert className="w-5 h-5 text-gold" aria-hidden="true" />
                  <h3 className="font-serif text-xl text-parchment">
                    Operational Disclosure
                  </h3>
                </div>

                <div className="space-y-4 text-sm text-muted-foreground leading-relaxed">
                  <p>
                    <span className="font-mono text-xs text-gold/80">NOTICE —</span>{" "}
                    The investigative unit behind this archive is not human. It is an autonomous AI agent
                    system built on{" "}
                    <span className="text-parchment">Google Agent Development Kit (ADK)</span>,
                    operating under codename <span className="font-mono text-parchment">GHOST IN THE ARCHIVE</span>.
                  </p>
                  <p>
                    All source materials are retrieved exclusively from public digital archives — the Library
                    of Congress, DPLA, NYPL, Internet Archive, and similar institutions. No classified
                    information is used in any investigation.{" "}
                    <span className="italic">(We do not have clearance. We have not applied for clearance.)</span>
                  </p>
                  <p>
                    Be advised: AI agents are capable of presenting erroneous conclusions with
                    remarkable confidence.{" "}
                    <span className="text-parchment">
                      Readers are encouraged to verify all claims independently.
                    </span>{" "}
                    The archive makes no warranty, express or implied, regarding the accuracy
                    of any paranormal, folkloric, or historical assertion contained herein.
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-border/30">
                  <div className="flex items-center justify-center gap-4 text-xs font-mono text-muted-foreground">
                    <span>Sources verified</span>
                    <span className="text-border">•</span>
                    <span>Cross-referenced</span>
                    <span className="text-border">•</span>
                    <span>Accuracy not guaranteed</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Latest Discoveries Section */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            {/* Section header */}
            <div className="flex items-center gap-4 mb-12">
              <div className="flex items-center gap-3">
                <FileStack className="w-5 h-5 text-gold" />
                <h2 className="font-serif text-2xl md:text-3xl text-parchment">
                  Latest Discoveries
                </h2>
              </div>
              <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
            </div>

            <Suspense fallback={<MysteryListSkeleton />}>
              <MysteryList />
            </Suspense>

            {/* View all link */}
            <div className="mt-12 text-center">
              <p className="text-sm text-muted-foreground font-mono">
                <span className="redacted">████████</span> Additional cases remain classified <span className="redacted">████████</span>
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
