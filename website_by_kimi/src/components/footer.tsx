'use client'

import { Github, Twitter, Send, Mail } from 'lucide-react'
import { siteConfig } from '@/lib/utils'

export function Footer() {
  return (
    <footer className="border-t border-border bg-secondary/10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <a href="/" className="flex items-center gap-2 mb-4">
              <img 
                src="/icon.png" 
                alt={siteConfig.name} 
                className="h-8 w-8 rounded-lg object-contain bg-secondary/50"
                width={32}
                height={32}
              />
              <span className="text-xl font-bold">{siteConfig.name}</span>
            </a>
            <p className="text-sm text-muted-foreground mb-4">
              The first autonomous AI security agent with visual exploit verification.
            </p>
            <div className="flex gap-3">
              <a
                href="#"
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/50 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              >
                <Twitter className="h-4 w-4" />
              </a>
              <a
                href="#"
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/50 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              >
                <Github className="h-4 w-4" />
              </a>
              <a
                href="#"
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/50 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              >
                <Send className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="#features" className="hover:text-foreground transition-colors">Features</a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
              </li>
              <li>
                <a href="#demo" className="hover:text-foreground transition-colors">Demo</a>
              </li>
              <li>
                <a href="#waitlist" className="hover:text-foreground transition-colors">Waitlist</a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="#" className="hover:text-foreground transition-colors">Documentation</a>
              </li>
              <li>
                <a href="#" className="hover:text-foreground transition-colors">API Reference</a>
              </li>
              <li>
                <a href="#" className="hover:text-foreground transition-colors">Security</a>
              </li>
              <li>
                <a href="#" className="hover:text-foreground transition-colors">Blog</a>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                <a href="mailto:racore88.ai@gmail.com" className="hover:text-foreground transition-colors">
                  racore88.ai@gmail.com
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Send className="h-4 w-4" />
                <span>{siteConfig.telegram}</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
