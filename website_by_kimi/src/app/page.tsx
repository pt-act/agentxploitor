import { Navbar } from '@/components/navbar'
import { Hero } from '@/components/hero'
import { Features } from '@/components/features'
import { HowItWorks } from '@/components/how-it-works'
import { IntelligenceStats } from '@/components/intelligence-stats'
import { Demo } from '@/components/demo'
import { Waitlist } from '@/components/waitlist'
import { Footer } from '@/components/footer'

export default function Home() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <IntelligenceStats />
      <Demo />
      <Waitlist />
      <Footer />
    </main>
  )
}
