'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, ArrowRight, Check, Shield, Users, Zap } from 'lucide-react'
import { siteConfig } from '@/lib/utils'

export function Waitlist() {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !role) return

    setIsLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsLoading(false)
    setIsSubmitted(true)
  }

  return (
    <section id="waitlist" className="relative py-24 sm:py-32 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
              Get Early <span className="text-gradient">Access</span>
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Join the waitlist to be among the first to experience autonomous AI security auditing. 
              Early adopters receive 50% off their first audit.
            </p>

            {/* Benefits */}
            <div className="space-y-4">
              {[
                { icon: Shield, text: 'Priority access to the platform' },
                { icon: Users, text: 'Direct channel to the founding team' },
                { icon: Zap, text: '50% discount on first audit' },
              ].map((benefit, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <benefit.icon className="h-5 w-5 text-primary" />
                  </div>
                  <span className="text-muted-foreground">{benefit.text}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right Form */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <div className="rounded-2xl border border-border bg-secondary/30 p-8 backdrop-blur-sm">
              {!isSubmitted ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        required
                        className="w-full rounded-lg border border-border bg-background px-10 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="role" className="block text-sm font-medium mb-2">
                      I am a...
                    </label>
                    <select
                      id="role"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      required
                      className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors appearance-none cursor-pointer"
                    >
                      <option value="">Select your role</option>
                      <option value="security-researcher">Security Researcher</option>
                      <option value="defi-protocol">DeFi Protocol Team</option>
                      <option value="auditor">Security Auditor</option>
                      <option value="bug-bounty-hunter">Bug Bounty Hunter</option>
                      <option value="founder">Founder/Builder</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="group w-full inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-4 text-base font-semibold text-primary-foreground transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    ) : (
                      <>
                        Join the Waitlist
                        <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                      </>
                    )}
                  </button>

                  <p className="text-xs text-muted-foreground text-center">
                    No spam, ever. Unsubscribe anytime.
                  </p>
                </form>
              ) : (
                <div className="py-12 text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20"
                  >
                    <Check className="h-8 w-8 text-green-400" />
                  </motion.div>
                  <h3 className="text-xl font-semibold mb-2">You are on the list!</h3>
                  <p className="text-muted-foreground">
                    We will be in touch soon with early access details.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
