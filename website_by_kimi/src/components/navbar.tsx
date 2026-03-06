'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronRight, Menu, X } from 'lucide-react'
import { siteConfig } from '@/lib/utils'

const navItems = [
  { label: 'Features', href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Demo', href: '#demo' },
  { label: 'Docs', href: '/docs' },
  { label: 'Waitlist', href: '#waitlist' },
]

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl"
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <a href="/" className="flex items-center gap-3">
          <img 
            src="/logo.png" 
            alt={siteConfig.name} 
            className="h-8 w-auto"
          />
        </a>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {item.label}
            </a>
          ))}
          <a
            href="#waitlist"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Get Early Access
            <ChevronRight className="h-4 w-4" />
          </a>
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden p-2 text-muted-foreground hover:text-foreground"
        >
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {/* Mobile Navigation */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden border-t border-border bg-background"
        >
          <div className="px-4 py-4 space-y-2">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className="block px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
              >
                {item.label}
              </a>
            ))}
            <a
              href="#waitlist"
              onClick={() => setIsOpen(false)}
              className="block px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-lg text-center"
            >
              Get Early Access
            </a>
          </div>
        </motion.div>
      )}
    </motion.header>
  )
}
