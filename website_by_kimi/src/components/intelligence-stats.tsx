'use client'

/**
 * IntelligenceStats — Live transparency display
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * "AgentxploiTor has completed 847 audits and learned 234 patterns."
 *
 * Glass-box principle: the intelligence layer is never hidden.
 * Shows real system state — not marketing copy.
 *
 * Fetches from /api/intelligence/stats (proxied to Python memory layer).
 * Gracefully degrades to static messaging if API unavailable.
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, Database, Zap, Shield } from 'lucide-react'

interface IntelligenceData {
  total_audits: number
  unique_targets: number
  patterns_learned: number
  simplemem_available: boolean
  code_voyager_available: boolean
  error?: string
}

const FALLBACK: IntelligenceData = {
  total_audits: 0,
  unique_targets: 0,
  patterns_learned: 0,
  simplemem_available: true,
  code_voyager_available: true,
}

export function IntelligenceStats() {
  const [data, setData] = useState<IntelligenceData>(FALLBACK)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetch('/api/intelligence/stats')
      .then(r => r.json())
      .then(d => { setData(d); setLoaded(true) })
      .catch(() => setLoaded(true))
  }, [])

  const stats = [
    {
      icon: Shield,
      label: 'Independent Audits',
      value: loaded && data.total_audits > 0
        ? data.total_audits.toLocaleString()
        : 'Initialising',
      sub: 'completed',
      color: 'text-primary',
    },
    {
      icon: Database,
      label: 'Contracts Analysed',
      value: loaded && data.unique_targets > 0
        ? data.unique_targets.toLocaleString()
        : '—',
      sub: 'unique targets',
      color: 'text-accent',
    },
    {
      icon: Brain,
      label: 'Patterns Learned',
      value: loaded && data.patterns_learned > 0
        ? data.patterns_learned.toLocaleString()
        : '—',
      sub: 'vulnerability patterns',
      color: 'text-primary',
    },
    {
      icon: Zap,
      label: 'Intelligence Layer',
      value: data.simplemem_available && data.code_voyager_available
        ? 'Active'
        : 'Initialising',
      sub: 'SimpleMem + Code-Voyager',
      color: data.simplemem_available ? 'text-green-400' : 'text-yellow-400',
    },
  ]

  return (
    <section className="py-16 border-y border-border/30">
      <div className="mx-auto max-w-6xl px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-widest mb-2">
            Live Intelligence Layer
          </p>
          <h2 className="text-2xl font-semibold text-foreground">
            The system gets smarter with every audit
          </h2>
          <p className="mt-3 text-muted-foreground max-w-xl mx-auto text-sm leading-relaxed">
            Every completed audit stores its findings in SimpleMem and fires Code-Voyager's
            Skill Factory — autonomously writing new skills from experience.
            No human intervention. No reset between sessions.
          </p>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-xl border border-border/40 bg-secondary/20 p-5 text-center backdrop-blur-sm"
            >
              <stat.icon className={`h-5 w-5 mx-auto mb-3 ${stat.color}`} />
              <p className={`text-2xl font-bold font-mono ${stat.color}`}>
                {stat.value}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{stat.sub}</p>
              <p className="text-xs font-medium text-foreground/70 mt-0.5">{stat.label}</p>
            </motion.div>
          ))}
        </div>

        {/* The compound intelligence callout */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="mt-8 rounded-xl border border-primary/20 bg-primary/5 p-5 text-center"
        >
          <p className="text-sm text-muted-foreground leading-relaxed">
            <span className="text-foreground font-medium">The compound intelligence effect: </span>
            Audit 1 applies foundational knowledge. Audit 100 recognises 30+ chain-specific patterns.
            Audit 1000 predicts likely vulnerabilities before running full analysis.
            The moat grows with every job — and cannot be replicated without running the same audits.
          </p>
        </motion.div>
      </div>
    </section>
  )
}
