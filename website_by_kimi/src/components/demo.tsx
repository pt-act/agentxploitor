'use client'

import { motion } from 'framer-motion'
import { ExternalLink, Github, FileText } from 'lucide-react'
import { LiveTerminalDemo } from './live-terminal-demo'

export function Demo() {
  return (
    <section id="demo" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-3xl text-center mb-16"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            See It In <span className="text-gradient">Action</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Watch a live autonomous security audit. The terminal below shows actual agent output 
            from discovery to visual verification.
          </p>
        </motion.div>

        {/* Live Terminal Demo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="relative"
        >
          <LiveTerminalDemo />

          {/* Decorative Elements */}
          <div className="absolute -top-4 -right-4 w-24 h-24 bg-accent/20 rounded-full blur-2xl" />
          <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-primary/20 rounded-full blur-2xl" />
        </motion.div>

        {/* Demo Links */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-12 flex flex-wrap justify-center gap-4"
        >
          <a
            href="/docs/quickstart"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/30 px-6 py-3 text-sm font-medium transition-colors hover:bg-secondary/50"
          >
            <FileText className="h-4 w-4" />
            Read Documentation
          </a>
          <a
            href="https://github.com/agentxploitor/agentxploitor"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/30 px-6 py-3 text-sm font-medium transition-colors hover:bg-secondary/50"
          >
            <Github className="h-4 w-4" />
            View on GitHub
          </a>
        </motion.div>

        {/* Code Preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 mx-auto max-w-3xl"
        >
          <div className="rounded-xl border border-border bg-secondary/30 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-border bg-background/50 px-4 py-2">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs text-muted-foreground font-mono">demo.py</span>
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="text-sm font-mono">
                <code className="text-muted-foreground">
                  <span className="text-purple-400">async def</span>{' '}
                  <span className="text-accent">autonomous_audit</span>():
                  {'\n'}  agent = <span className="text-yellow-400">AgentxploiTorAgent</span>()
                  {'\n'}  
                  {'\n'}  <span className="text-green-400"># 1. Discover</span>
                  {'\n'}  vulns = <span className="text-purple-400">await</span> agent.scan_target(url)
                  {'\n'}  
                  {'\n'}  <span className="text-green-400"># 2. Exploit & Verify</span>
                  {'\n'}  proof = <span className="text-purple-400">await</span> agent.verify_exploit(vuln)
                  {'\n'}  
                  {'\n'}  <span className="text-green-400"># 3. Submit</span>
                  {'\n'}  <span className="text-purple-400">await</span> agent.submit_bounty(proof)
                </code>
              </pre>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
