'use client'

import { motion } from 'framer-motion'
import { steps } from '@/lib/utils'

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-24 sm:py-32 bg-secondary/10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-3xl text-center mb-16"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            How It <span className="text-gradient">Works</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            From target input to independent report — autonomous, transparent, and smarter every time.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Connecting Line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-primary via-accent to-primary hidden lg:block" />

          <div className="space-y-12 lg:space-y-0">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`relative lg:grid lg:grid-cols-2 lg:gap-16 lg:items-center ${
                  i !== 0 ? 'lg:mt-16' : ''
                }`}
              >
                {/* Content */}
                <div className={`${i % 2 === 1 ? 'lg:order-2' : ''}`}>
                  <div className="relative rounded-2xl border border-border bg-secondary/30 p-8">
                    <div className="absolute -top-4 -left-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-lg font-bold text-white">
                      {step.number}
                    </div>
                    <h3 className="mt-4 text-2xl font-bold mb-2">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                </div>

                {/* Visual */}
                <div className={`mt-8 lg:mt-0 ${i % 2 === 1 ? 'lg:order-1' : ''}`}>
                  <div className="relative aspect-video rounded-2xl border border-border bg-secondary/20 overflow-hidden">
                    <StepVisual step={i} />
                  </div>
                </div>

                {/* Center Dot */}
                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-accent hidden lg:block" />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function StepVisual({ step }: { step: number }) {
  const visuals = [
    // Step 1: Scan
    <div key="scan" className="absolute inset-0 flex items-center justify-center p-8">
      <div className="w-full space-y-3">
        <div className="h-2 w-3/4 bg-primary/30 rounded animate-pulse" />
        <div className="h-2 w-1/2 bg-primary/20 rounded animate-pulse" style={{ animationDelay: '0.2s' }} />
        <div className="h-2 w-2/3 bg-primary/20 rounded animate-pulse" style={{ animationDelay: '0.4s' }} />
        <div className="mt-4 p-3 rounded-lg bg-green-500/20 border border-green-500/30">
          <div className="text-xs text-green-400 font-mono">Scanning target...</div>
        </div>
      </div>
    </div>,
    // Step 2: Discover
    <div key="discover" className="absolute inset-0 flex items-center justify-center p-8">
      <div className="space-y-2">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/20 border border-red-500/30">
          <span className="text-xs text-red-400 font-mono">CRITICAL: Reentrancy</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-500/20 border border-yellow-500/30">
          <span className="text-xs text-yellow-400 font-mono">HIGH: Access Control</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500/20 border border-orange-500/30">
          <span className="text-xs text-orange-400 font-mono">MEDIUM: Oracle</span>
        </div>
      </div>
    </div>,
    // Step 3: Exploit
    <div key="exploit" className="absolute inset-0 flex items-center justify-center p-8">
      <div className="font-mono text-xs space-y-1">
        <div className="text-muted-foreground">function exploit() {'{'}</div>
        <div className="text-accent pl-4">await target.withdraw();</div>
        <div className="text-accent pl-4">await target.deposit();</div>
        <div className="text-accent pl-4">// Reentrancy triggered</div>
        <div className="text-muted-foreground">{'}'}</div>
        <div className="mt-2 text-green-400">Payload generated ✓</div>
      </div>
    </div>,
    // Step 4: Verify
    <div key="verify" className="absolute inset-0 flex items-center justify-center p-4">
      <div className="grid grid-cols-2 gap-2 w-full">
        <div className="rounded-lg bg-secondary p-2">
          <div className="text-[10px] text-muted-foreground mb-1">BEFORE</div>
          <div className="text-xs font-mono text-green-400">Balance: 1000</div>
        </div>
        <div className="rounded-lg bg-secondary p-2">
          <div className="text-[10px] text-muted-foreground mb-1">AFTER</div>
          <div className="text-xs font-mono text-red-400">Balance: 0</div>
        </div>
        <div className="col-span-2 rounded-lg bg-accent/20 border border-accent/30 p-2 text-center">
          <div className="text-xs font-mono text-accent">Visual Diff: 45.3%</div>
        </div>
      </div>
    </div>,
    // Step 5: Evaluate
    <div key="evaluate" className="absolute inset-0 flex items-center justify-center p-8">
      <div className="text-center space-y-3">
        <div className="text-4xl font-bold text-accent">92%</div>
        <div className="text-sm text-muted-foreground">Confidence Score</div>
        <div className="flex gap-1 justify-center">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="w-8 h-1 rounded-full bg-accent" />
          ))}
        </div>
        <div className="text-xs text-green-400">✓ Satisfactory</div>
      </div>
    </div>,
    // Step 6: Submit
    <div key="submit" className="absolute inset-0 flex items-center justify-center p-8">
      <div className="w-full space-y-2">
        <div className="flex items-center gap-2 text-xs">
          <div className="w-4 h-4 rounded-full bg-green-500/20 flex items-center justify-center">
            <span className="text-green-400 text-[8px]">✓</span>
          </div>
          <span className="text-muted-foreground">Report generated</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-4 h-4 rounded-full bg-green-500/20 flex items-center justify-center">
            <span className="text-green-400 text-[8px]">✓</span>
          </div>
          <span className="text-muted-foreground">Proof attached</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-4 h-4 rounded-full bg-accent/20 flex items-center justify-center">
            <span className="text-accent text-[8px]">→</span>
          </div>
          <span className="text-accent">Submitting to bounty platform...</span>
        </div>
      </div>
    </div>,
  ]

  return visuals[step] || null
}
