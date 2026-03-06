'use client'

import { motion } from 'framer-motion'
import { Search, Eye, Brain, Send, Globe, Shield, AlertTriangle, FileCheck } from 'lucide-react'
import { features } from '@/lib/utils'

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Search,
  Eye,
  Brain,
  Send,
  Globe,
  Shield,
}

export function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-3xl text-center mb-16"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            What Makes Us <span className="text-gradient">Different</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            While other tools generate reports, Agentxploitor proves vulnerabilities work — powered by 19 specialist AI agents that learn from every audit, remember every finding, and improve autonomously.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => {
            const Icon = iconMap[feature.icon] || Shield
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group relative rounded-2xl border border-border bg-secondary/30 p-8 transition-all hover:border-primary/50 hover:bg-secondary/50"
              >
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 text-accent transition-transform group-hover:scale-110">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 transition-opacity group-hover:opacity-100" />
              </motion.div>
            )
          })}
        </div>

        {/* Comparison Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-24 rounded-2xl border border-border bg-secondary/20 overflow-hidden"
        >
          <div className="p-6 sm:p-8 border-b border-border">
            <h3 className="text-2xl font-bold text-center">
              Agentxploitor vs <span className="text-muted-foreground">Traditional Tools</span>
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-secondary/30">
                  <th className="px-6 py-4 text-left text-sm font-medium text-muted-foreground">Capability</th>
                  <th className="px-6 py-4 text-center text-sm font-medium text-accent">Agentxploitor</th>
                  <th className="px-6 py-4 text-center text-sm font-medium text-muted-foreground">Traditional</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { feature: 'Code Analysis', agent: true, traditional: true },
                  { feature: 'Vulnerability Detection', agent: true, traditional: true },
                  { feature: 'Exploit Generation', agent: true, traditional: false, highlight: true },
                  { feature: 'Visual Proof of Exploit', agent: true, traditional: false, highlight: true },
                  { feature: 'Miniapp UI Auditing', agent: true, traditional: false, highlight: true },
                  { feature: 'Learns From Every Audit', agent: true, traditional: false, highlight: true },
                  { feature: 'Project-Specific Memory', agent: true, traditional: false, highlight: true },
                  { feature: 'Self-Evolving Skills', agent: true, traditional: false, highlight: true },
                  { feature: 'Independent Declaration', agent: true, traditional: false, highlight: true },
                  { feature: 'Farcaster Native', agent: true, traditional: false },
                ].map((row, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0">
                    <td className={`px-6 py-4 text-sm ${row.highlight ? 'font-medium text-foreground' : 'text-muted-foreground'}`}>
                      {row.feature}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {row.agent ? (
                        <FileCheck className="mx-auto h-5 w-5 text-accent" />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {row.traditional ? (
                        <FileCheck className="mx-auto h-5 w-5 text-muted-foreground" />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
