import React from "react"
import type { Metadata } from 'next'
import { Playfair_Display, Inter, Noto_Sans_JP } from 'next/font/google'
import { SessionProvider } from "@/components/providers/SessionProvider"
import './globals.css'

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: '--font-playfair',
  display: 'swap',
})

const inter = Inter({
  subsets: ["latin"],
  variable: '--font-inter',
  display: 'swap',
})

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  variable: '--font-noto-jp',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Ghost in the Archive',
  description: 'AI がアーカイブの闇から発掘する、歴史の亡霊たち — Unearthing historical mysteries and folkloric anomalies from public digital archives.',
  keywords: ["歴史", "ミステリー", "民俗学", "フォークロア", "デジタルアーカイブ", "AI"],
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${playfair.variable} ${inter.variable} ${notoSansJP.variable} font-sans antialiased`}>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
