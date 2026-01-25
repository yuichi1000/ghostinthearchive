import { AdminHeader } from "@/components/layout/AdminHeader";
import { Footer } from "@/components/layout/Footer";

/**
 * 管理画面レイアウト
 * 認証状態を表示するヘッダーを含む
 */
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-ink/[0.02]">
      <AdminHeader />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
