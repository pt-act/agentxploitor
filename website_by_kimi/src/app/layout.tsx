import type { Metadata } from 'next'
import './globals.css'

const SITE_URL = process.env.NEXT_PUBLIC_URL || 'https://agentxploitor.netlify.app'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: 'Agentxploitor - Autonomous AI Security Agent with Visual Exploit Verification',
  description: 'The first autonomous AI security agent that discovers, exploits, and visually verifies vulnerabilities in smart contracts and Web3 protocols. See what others only report.',
  keywords: ['AI security', 'smart contract audit', 'Web3 security', 'autonomous agent', 'exploit verification', 'bug bounty'],
  openGraph: {
    title: 'Agentxploitor - Autonomous AI Security Agent',
    description: 'The first autonomous AI security agent with visual exploit verification. See what others only report.',
    type: 'website',
    url: SITE_URL,
    images: [{ url: '/hero.png', width: 1200, height: 630, alt: 'Agentxploitor Dashboard' }],
    siteName: 'Agentxploitor',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Agentxploitor - Autonomous AI Security Agent',
    description: 'The first autonomous AI security agent with visual exploit verification. See what others only report.',
    images: ['/hero.png'],
  },
  icons: {
    icon: '/icon.png',
    shortcut: '/icon.png',
    apple: '/icon.png',
  },
  alternates: {
    canonical: SITE_URL,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  )
}
