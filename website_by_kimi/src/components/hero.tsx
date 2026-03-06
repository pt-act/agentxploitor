'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Eye, Sparkles } from 'lucide-react'
import { siteConfig } from '@/lib/utils'

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary/20 via-transparent to-accent/20 blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-accent/10 via-transparent to-primary/20 blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMzMzMiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0aDR2NGgtNHpNMjAgMjBoNHY0aC00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-20" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/50 px-4 py-2 backdrop-blur-sm"
        >
          <Sparkles className="h-4 w-4 text-accent" />
          <span className="text-sm font-medium text-muted-foreground">
            Powered by 19 AI Agents · Coming to Farcaster & Base
          </span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-6 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
        >
          <span className="block">Autonomous AI</span>
          <span className="block mt-2">
            <span className="text-gradient">Security Agent</span>
          </span>
        </motion.h1>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mx-auto mb-8 max-w-2xl text-xl text-muted-foreground sm:text-2xl"
        >
          {siteConfig.tagline}
        </motion.p>

        {/* Description */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mx-auto mb-12 max-w-xl text-base text-muted-foreground/80"
        >
          The first autonomous AI security platform that discovers, exploits, and{' '}
          <span className="text-accent font-medium">visually verifies</span>{' '}
          vulnerabilities in smart contracts and Farcaster miniapps — powered by 19 specialist AI agents that learn and improve with every audit.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="#waitlist"
            className="group inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-primary-foreground transition-all hover:bg-primary/90 hover:scale-105 glow-primary"
          >
            Join the Waitlist
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </a>
          <a
            href="#demo"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-8 py-4 text-lg font-semibold text-foreground transition-all hover:bg-secondary hover:scale-105"
          >
            <Eye className="h-5 w-5" />
            Watch Demo
          </a>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-20 grid grid-cols-2 gap-8 sm:grid-cols-4"
        >
          {[
            { value: '100%', label: 'Autonomous' },
            { value: '24/7', label: 'Always On' },
            { value: '19', label: 'AI Agents' },
            { value: 'Visual', label: 'Proof' },
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl font-bold text-gradient sm:text-4xl">{stat.value}</div>
              <div className="mt-1 text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </motion.div>

        {/* Hero Image */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.6 }}
          className="mt-20 mx-auto max-w-5xl"
        >
          <div className="relative rounded-2xl border border-border bg-secondary/30 p-2 backdrop-blur-sm overflow-hidden">
            <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-primary/20 to-accent/20 opacity-50" />
            <div className="relative rounded-xl overflow-hidden">
              <img 
                src="/hero.png" 
                alt="Agentxploitor Dashboard - Autonomous Security Agent Interface"
                className="w-full h-auto"
              />
              {/* Overlay gradient for better text contrast if needed */}
              <div className="absolute inset-0 bg-gradient-to-t from-background/20 to-transparent pointer-events-none" />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
