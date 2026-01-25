import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

/**
 * 管理画面レイアウト
 * 管理画面専用のヘッダー・フッターを適用
 */
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-ink/[0.02]">
      <Header isAdmin />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
