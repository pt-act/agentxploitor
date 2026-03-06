'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronRight, Search, Book, Zap, Code, Terminal, FileText, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

const docSections = [
  {
    title: 'Getting Started',
    icon: Book,
    items: [
      { title: 'Introduction', slug: 'introduction', description: 'What is Agentxploitor and key concepts' },
      { title: 'Quick Start', slug: 'quickstart', description: 'Get running in under 5 minutes' },
      { title: 'Demo Script', slug: 'demo-script', description: 'Recording guide for video demos' },
    ],
  },
  {
    title: 'Core Concepts',
    icon: Zap,
    items: [
      { title: 'Autonomy Philosophy', slug: 'autonomy-philosophy', description: 'Agent vs Bot - understanding true autonomy' },
      { title: 'Visual Verification', slug: 'visual-verification', description: 'How browser perception enables proof' },
      { title: 'Self-Evaluation', slug: 'self-evaluation', description: 'AI judging its own success' },
    ],
  },
  {
    title: 'Security',
    icon: Lock,
    items: [
      { title: 'Security Checklist', slug: 'security-checklist', description: 'Pre-deployment security audit' },
      { title: 'Accessibility', slug: 'accessibility', description: 'Testing guide for screen readers' },
      { title: 'Audit Report', slug: 'audit-report', description: 'Academic security evaluation' },
    ],
  },
  {
    title: 'Development',
    icon: Code,
    items: [
      { title: 'Final Status', slug: 'final-status', description: 'Production readiness assessment' },
      { title: 'Architecture', slug: 'architecture', description: 'System design and components' },
      { title: 'API Reference', slug: 'api', description: 'Agent and model interfaces' },
    ],
  },
]

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const filteredSections = docSections.map(section => ({
    ...section,
    items: section.items.filter(item =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter(section => section.items.length > 0)

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center justify-between px-4">
          <a href="/" className="flex items-center gap-2">
            <img src="/icon.png" alt="Agentxploitor" className="h-7 w-7 rounded-lg" />
            <span className="font-bold">Agentxploitor</span>
          </a>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 text-muted-foreground hover:text-foreground"
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar - Desktop (always visible) */}
        <aside className="hidden lg:block fixed inset-y-0 left-0 z-40 w-72 border-r border-border bg-secondary/20 backdrop-blur-xl">
          <div className="flex h-full flex-col">
            {/* Logo */}
            <div className="flex h-16 items-center border-b border-border px-6">
              <a href="/" className="flex items-center gap-2">
                <img src="/logo.png" alt="Agentxploitor" className="h-8 w-auto" />
              </a>
            </div>

            {/* Search */}
            <div className="p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search docs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-9 py-2 text-sm outline-none focus:border-primary transition-colors"
                />
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto px-4 pb-8">
              <div className="space-y-6">
                {filteredSections.map((section) => (
                  <div key={section.title}>
                    <div className="flex items-center gap-2 mb-2">
                      <section.icon className="h-4 w-4 text-muted-foreground" />
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        {section.title}
                      </h3>
                    </div>
                    <ul className="space-y-1">
                      {section.items.map((item) => (
                        <li key={item.slug}>
                          <a
                            href={`/docs/${item.slug}`}
                            className="group flex items-start gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                          >
                            <ChevronRight className="h-4 w-4 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                            <div>
                              <div className="font-medium">{item.title}</div>
                              <div className="text-xs text-muted-foreground/70 line-clamp-1">{item.description}</div>
                            </div>
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </nav>

            {/* Back to site */}
            <div className="border-t border-border p-4">
              <a
                href="/"
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                ← Back to website
              </a>
            </div>
          </div>
        </aside>

        {/* Sidebar - Mobile (conditional) */}
        {mounted && (
          <AnimatePresence>
            {isSidebarOpen && (
              <motion.aside
                initial={{ x: -100, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -100, opacity: 0 }}
                className="fixed inset-y-0 left-0 z-40 w-72 border-r border-border bg-secondary/20 backdrop-blur-xl lg:hidden"
              >
                <div className="flex h-full flex-col">
                  {/* Mobile Logo */}
                  <div className="flex h-14 items-center border-b border-border px-4 lg:hidden">
                    <a href="/" className="flex items-center gap-2">
                      <img src="/icon.png" alt="Agentxploitor" className="h-7 w-7 rounded-lg" />
                      <span className="font-bold">Agentxploitor</span>
                    </a>
                    <button
                      onClick={() => setIsSidebarOpen(false)}
                      className="ml-auto p-2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Search */}
                  <div className="p-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <input
                        type="text"
                        placeholder="Search docs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full rounded-lg border border-border bg-background px-9 py-2 text-sm outline-none focus:border-primary transition-colors"
                      />
                    </div>
                  </div>

                  {/* Navigation */}
                  <nav className="flex-1 overflow-y-auto px-4 pb-8">
                    <div className="space-y-6">
                      {filteredSections.map((section) => (
                        <div key={section.title}>
                          <div className="flex items-center gap-2 mb-2">
                            <section.icon className="h-4 w-4 text-muted-foreground" />
                            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              {section.title}
                            </h3>
                          </div>
                          <ul className="space-y-1">
                            {section.items.map((item) => (
                              <li key={item.slug}>
                                <a
                                  href={`/docs/${item.slug}`}
                                  onClick={() => setIsSidebarOpen(false)}
                                  className="group flex items-start gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                                >
                                  <ChevronRight className="h-4 w-4 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                  <div>
                                    <div className="font-medium">{item.title}</div>
                                    <div className="text-xs text-muted-foreground/70 line-clamp-1">{item.description}</div>
                                  </div>
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </nav>

                  {/* Back to site */}
                  <div className="border-t border-border p-4">
                    <a
                      href="/"
                      className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      ← Back to website
                    </a>
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0 lg:pl-72 pt-14 lg:pt-0">
          <div className="mx-auto max-w-4xl px-4 py-8 lg:px-8 lg:py-12">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
