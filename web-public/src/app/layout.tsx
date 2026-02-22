import React from "react"
import type { Metadata } from 'next'
import { GoogleTagManager } from '@next/third-parties/google'
import { Playfair_Display, Inter, Noto_Sans_JP } from 'next/font/google'
import { getSiteUrl } from '@/lib/site-url'
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
  metadataBase: new URL(getSiteUrl()),
  title: 'Ghost in the Archive',
  description: 'Unearthing the Ghosts in the world\'s records — multi-lingual cross-analysis of public digital archives through five academic disciplines.',
  keywords: ["history", "folklore", "cultural anthropology", "linguistics", "archival science", "digital archives", "AI", "OSINT", "mystery", "歴史", "民俗学", "文化人類学", "言語学", "文書館学"],
  openGraph: {
    siteName: 'Ghost in the Archive',
  },
  twitter: {
    card: 'summary_large_image',
  },
  alternates: {
    types: {
      'application/atom+xml': '/feed.xml',
    },
  },
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
