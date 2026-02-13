import { Header } from "@/components/header"
import { LanguageProvider } from "@/contexts/language-context"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <LanguageProvider>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
      </div>
    </LanguageProvider>
  )
}
