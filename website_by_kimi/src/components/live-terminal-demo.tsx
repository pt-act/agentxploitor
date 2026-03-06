'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, RotateCcw, Terminal, CheckCircle, AlertTriangle, Shield } from 'lucide-react'

interface LogLine {
  id: number
  text: string
  type: 'info' | 'success' | 'warning' | 'error' | 'command'
  delay: number
}

const demoLogs: LogLine[] = [
  { id: 1, text: 'AgentxploiTor v1.0.0 - Autonomous Security Agent', type: 'info', delay: 0 },
  { id: 2, text: 'Initializing with browser perception...', type: 'info', delay: 500 },
  { id: 3, text: '✓ Browser automation ready', type: 'success', delay: 800 },
  { id: 4, text: '✓ Visual verification enabled', type: 'success', delay: 1000 },
  { id: 5, text: '', type: 'info', delay: 1200 },
  { id: 6, text: 'Target: https://defi-protocol.example.com', type: 'command', delay: 1500 },
  { id: 7, text: 'Scanning for vulnerabilities...', type: 'info', delay: 2000 },
  { id: 8, text: '  → Checking entry points', type: 'info', delay: 2500 },
  { id: 9, text: '  → Analyzing smart contracts', type: 'info', delay: 3000 },
  { id: 10, text: '  → Testing access controls', type: 'info', delay: 3500 },
  { id: 11, text: '', type: 'info', delay: 3800 },
  { id: 12, text: '🔴 CRITICAL: Reentrancy vulnerability found in withdraw()', type: 'warning', delay: 4000 },
  { id: 13, text: '   CVSS Score: 9.8/10', type: 'info', delay: 4200 },
  { id: 14, text: '   Impact: Unauthorized fund withdrawal', type: 'info', delay: 4400 },
  { id: 15, text: '', type: 'info', delay: 4600 },
  { id: 16, text: 'Generating exploit payload...', type: 'info', delay: 5000 },
  { id: 17, text: '✓ Exploit created: ReentrancyAttack.sol', type: 'success', delay: 5500 },
  { id: 18, text: '', type: 'info', delay: 5800 },
  { id: 19, text: 'Executing visual verification...', type: 'info', delay: 6000 },
  { id: 20, text: '  → Capturing BEFORE state', type: 'info', delay: 6500 },
  { id: 21, text: '  → Executing exploit', type: 'info', delay: 7000 },
  { id: 22, text: '  → Capturing AFTER state', type: 'info', delay: 8000 },
  { id: 23, text: '', type: 'info', delay: 8500 },
  { id: 24, text: '✓ EXPLOIT VERIFIED', type: 'success', delay: 9000 },
  { id: 25, text: '   Visual diff: 98.5% state change', type: 'info', delay: 9200 },
  { id: 26, text: '   Balance: 1,000 ETH → 0 ETH', type: 'info', delay: 9400 },
  { id: 27, text: '   Proof saved: /proofs/exploit-vuln-001.png', type: 'info', delay: 9600 },
  { id: 28, text: '', type: 'info', delay: 9800 },
  { id: 29, text: 'Self-evaluation...', type: 'info', delay: 10000 },
  { id: 30, text: '✓ Confidence: 96% - Satisfactory', type: 'success', delay: 10500 },
  { id: 31, text: '', type: 'info', delay: 10800 },
  { id: 32, text: 'Generating bounty report...', type: 'info', delay: 11000 },
  { id: 33, text: '✓ Report ready for submission', type: 'success', delay: 11500 },
  { id: 34, text: '', type: 'info', delay: 11800 },
  { id: 35, text: '═══════════════════════════════════════════════════', type: 'info', delay: 12000 },
  { id: 36, text: 'DEMO COMPLETE', type: 'success', delay: 12200 },
  { id: 37, text: '═══════════════════════════════════════════════════', type: 'info', delay: 12400 },
]

export function LiveTerminalDemo() {
  const [logs, setLogs] = useState<LogLine[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isPlaying) return

    if (currentIndex >= demoLogs.length) {
      setIsComplete(true)
      setIsPlaying(false)
      return
    }

    const log = demoLogs[currentIndex]
    const timer = setTimeout(() => {
      setLogs(prev => [...prev, log])
      setCurrentIndex(prev => prev + 1)
    }, currentIndex === 0 ? 0 : log.delay - demoLogs[currentIndex - 1].delay)

    return () => clearTimeout(timer)
  }, [currentIndex, isPlaying])

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs])

  const handlePlay = () => {
    if (isComplete) {
      handleReset()
    }
    setIsPlaying(true)
  }

  const handlePause = () => {
    setIsPlaying(false)
  }

  const handleReset = () => {
    setIsPlaying(false)
    setLogs([])
    setCurrentIndex(0)
    setIsComplete(false)
  }

  const getLogColor = (type: LogLine['type']) => {
    switch (type) {
      case 'success': return 'text-green-400'
      case 'warning': return 'text-yellow-400'
      case 'error': return 'text-red-400'
      case 'command': return 'text-accent'
      default: return 'text-muted-foreground'
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Terminal Window */}
      <div className="rounded-xl border border-border bg-secondary/30 overflow-hidden shadow-2xl">
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-secondary/50">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
            </div>
            <span className="ml-3 text-xs text-muted-foreground font-mono flex items-center gap-2">
              <Terminal className="h-3 w-3" />
              agentxploitor-demo
            </span>
          </div>
          
          {/* Controls */}
          <div className="flex items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={handlePlay}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors"
              >
                <Play className="h-3 w-3" fill="currentColor" />
                {isComplete ? 'Replay' : 'Play Demo'}
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-secondary text-foreground text-xs font-medium hover:bg-secondary/80 transition-colors"
              >
                <Pause className="h-3 w-3" />
                Pause
              </button>
            )}
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-secondary text-muted-foreground text-xs font-medium hover:text-foreground transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </button>
          </div>
        </div>

        {/* Terminal Content */}
        <div 
          ref={terminalRef}
          className="h-96 overflow-y-auto p-4 font-mono text-sm bg-background/50"
        >
          <AnimatePresence>
            {logs.map((log, index) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`${getLogColor(log.type)} ${log.text === '' ? 'h-4' : ''}`}
              >
                {log.text}
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Blinking cursor */}
          {isPlaying && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
              className="inline-block w-2 h-4 bg-accent mt-1"
            />
          )}
        </div>

        {/* Terminal Footer */}
        <div className="px-4 py-2 border-t border-border bg-secondary/30 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Shield className="h-3 w-3 text-accent" />
              Status: {isComplete ? 'Complete' : isPlaying ? 'Running...' : 'Ready'}
            </span>
            <span>Lines: {logs.length}</span>
          </div>
          <div className="flex items-center gap-1">
            {isComplete && (
              <>
                <CheckCircle className="h-3 w-3 text-green-400" />
                <span className="text-green-400">Verified</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="rounded-lg border border-border bg-secondary/20 p-4 text-center">
          <div className="text-2xl font-bold text-accent">6</div>
          <div className="text-xs text-muted-foreground mt-1">Steps Automated</div>
        </div>
        <div className="rounded-lg border border-border bg-secondary/20 p-4 text-center">
          <div className="text-2xl font-bold text-accent">12s</div>
          <div className="text-xs text-muted-foreground mt-1">Avg. Execution</div>
        </div>
        <div className="rounded-lg border border-border bg-secondary/20 p-4 text-center">
          <div className="text-2xl font-bold text-accent">96%</div>
          <div className="text-xs text-muted-foreground mt-1">Confidence</div>
        </div>
      </div>
    </div>
  )
}
