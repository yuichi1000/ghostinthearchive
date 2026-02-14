import React from "react"
import type { Metadata } from 'next'
import { GoogleTagManager } from '@next/third-parties/google'
import { Playfair_Display, Inter, Noto_Sans_JP } from 'next/font/google'
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
}

const gtmId = process.env.NEXT_PUBLIC_GTM_ID

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html className="dark" suppressHydrationWarning>
      {gtmId && <GoogleTagManager gtmId={gtmId} />}
      <body className={`${playfair.variable} ${inter.variable} ${notoSansJP.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
