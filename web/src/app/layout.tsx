import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import { SessionProvider } from "@/components/providers/SessionProvider";
import "./globals.css";

/**
 * Playfair Display - 見出し用セリフフォント
 * 19世紀の新聞活字をイメージ
 */
const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
});

/**
 * Inter - 本文用サンセリフフォント
 * 可読性重視のモダンフォント
 */
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ghost in the Archive",
  description: "米公文書館から歴史的ミステリーと民俗学的怪異を発掘するAIシステム",
  keywords: ["歴史", "ミステリー", "民俗学", "フォークロア", "公文書館", "アーカイブ", "AI"],
};

/**
 * ルートレイアウト
 * 全ページ共通のフォント設定と背景スタイルを適用
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`${playfair.variable} ${inter.variable} bg-parchment antialiased`}
      >
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
