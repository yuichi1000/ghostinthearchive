import React from "react"
import type { Metadata } from 'next'
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
  title: 'Ghost in the Archive - Admin',
  description: 'Administration dashboard for Ghost in the Archive',
  robots: 'noindex, nofollow',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${playfair.variable} ${inter.variable} ${notoSansJP.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
