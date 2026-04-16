'use client'

import { motion } from 'framer-motion'
import { 
  Book, Rocket, Video, Brain, Eye, Sparkles, Shield, Lock, 
  FileCheck, Terminal, Code, CheckCircle, AlertTriangle 
} from 'lucide-react'

interface DocsClientProps {
  slug: string
  title: string
  description: string
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  'Introduction': Book,
  'Quick Start': Rocket,
  'Demo Script': Video,
  'Autonomy Philosophy': Brain,
  'Visual Verification': Eye,
  'Self-Evaluation': Sparkles,
  'Security Checklist': Lock,
  'Accessibility': FileCheck,
  'Academic Audit Report': Shield,
  'Final Status': CheckCircle,
  'Architecture': Terminal,
  'API Reference': Code,
  'Documentation': Book,
}

export default function DocsClient({ slug, title, description }: DocsClientProps) {
  const Icon = iconMap[title] || Book

  const renderContent = () => {
    switch (slug) {
      case 'introduction':
        return <IntroductionContent />
      case 'quickstart':
        return <QuickstartContent />
      case 'demo-script':
        return <DemoScriptContent />
      case 'autonomy-philosophy':
        return <AutonomyContent />
      case 'visual-verification':
        return <VisualVerificationContent />
      case 'self-evaluation':
        return <SelfEvaluationContent />
      case 'security-checklist':
        return <SecurityChecklistContent />
      case 'accessibility':
        return <AccessibilityContent />
      case 'audit-report':
        return <AuditReportContent />
      case 'final-status':
        return <FinalStatusContent />
      case 'architecture':
        return <ArchitectureContent />
      case 'api':
        return <ApiContent />
      default:
        return <IndexContent />
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="prose prose-invert max-w-none"
    >
      {/* Header */}
      <div className="mb-8 border-b border-border pb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20">
            <Icon className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight m-0">{title}</h1>
            <p className="text-muted-foreground mt-1 m-0">{description}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      {renderContent()}

      {/* Navigation Footer */}
      <div className="mt-16 pt-8 border-t border-border flex justify-between items-center">
        <a
          href="/"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          ← Back to website
        </a>
        <span className="text-sm text-muted-foreground">
          Agentxploitor Documentation
        </span>
      </div>
    </motion.article>
  )
}

function Section({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <section className="scroll-mt-20 mb-12">
      <h2 className="text-xl font-semibold tracking-tight mb-4 flex items-center gap-2">
        <span className="w-1.5 h-6 bg-gradient-to-b from-primary to-accent rounded-full" />
        {heading}
      </h2>
      <div className="text-muted-foreground leading-relaxed">
        {children}
      </div>
    </section>
  )
}

function IndexContent() {
  return (
    <>
      <Section heading="Welcome">
        <p className="mb-4">
          Welcome to the Agentxploitor documentation. Here you&apos;ll find comprehensive guides 
          and documentation to help you start working with the first autonomous AI security 
          agent with visual exploit verification.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 my-6">
          {[ 
            { href: '/docs/introduction', icon: Book, title: 'Introduction', desc: 'Learn what Agentxploitor is' },
            { href: '/docs/quickstart', icon: Rocket, title: 'Quick Start', desc: 'Get running in 5 minutes' },
            { href: '/docs/autonomy-philosophy', icon: Brain, title: 'Autonomy', desc: 'Understanding true autonomy' },
            { href: '/docs/visual-verification', icon: Eye, title: 'Visual Proof', desc: 'Browser perception' },
            { href: '/docs/security-checklist', icon: Shield, title: 'Security', desc: 'Pre-deployment checklist' },
            { href: '/docs/api', icon: Code, title: 'API Reference', desc: 'Agent interfaces' },
          ].map((item) => (
            <a key={item.href} href={item.href} className="group rounded-xl border border-border bg-secondary/20 p-6 transition-all hover:border-primary/50 hover:bg-secondary/30">
              <item.icon className="h-8 w-8 text-accent mb-4 transition-transform group-hover:scale-110" />
              <h3 className="font-semibold mb-1">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </a>
          ))}
        </div>
      </Section>
    </>
  )
}

function IntroductionContent() {
  return (
    <>
      <Section heading="What is Agentxploitor?">
        <p className="mb-4">
          <strong>Agentxploitor</strong> is the first autonomous AI security agent with visual exploit verification. 
          The name combines &quot;Agent&quot; + &quot;Exploit&quot; + &quot;Tor&quot; (viewer in Latin) — an agent that exploits vulnerabilities 
          and sees/verifies the results.
        </p>
        <div className="rounded-lg border border-border bg-secondary/30 p-4 my-6">
          <h4 className="font-semibold mb-2">Core Philosophy</h4>
          <p className="text-muted-foreground">
            &quot;Technology as a tool for enlightenment, not just engagement.&quot; Agentxploitor embodies this by 
            creating transparency in security — proving vulnerabilities exist rather than just reporting them.
          </p>
        </div>
      </Section>
      <Section heading="The Problem We Solve">
        <p className="mb-4">
          Traditional security tools can find vulnerabilities, but they cannot prove they work. 
          This creates several critical gaps:
        </p>
        <ul className="list-disc list-inside space-y-2 text-muted-foreground mb-4">
          <li>Security reports without proof of exploitability</li>
          <li>Manual verification required for each finding</li>
          <li>No visual evidence of successful exploitation</li>
          <li>Human bottleneck in the security workflow</li>
        </ul>
      </Section>
      <Section heading="The Solution">
        <p className="mb-4">
          Agentxploitor changes this paradigm by operating completely autonomously:
        </p>
        <div className="grid gap-4 sm:grid-cols-2 my-6">
          {[
            { label: 'Autonomous Discovery', desc: 'Finds vulnerabilities without human prompting' },
            { label: 'Exploit Generation', desc: 'Creates working exploits automatically' },
            { label: 'Visual Verification', desc: 'Captures before/after proof' },
            { label: 'Self-Evaluation', desc: 'AI judges its own success' },
          ].map((item, i) => (
            <div key={i} className="rounded-lg border border-border bg-secondary/20 p-4">
              <div className="font-medium text-accent mb-1">{item.label}</div>
              <div className="text-sm text-muted-foreground">{item.desc}</div>
            </div>
          ))}
        </div>
      </Section>
      <Section heading="Target Use Cases">
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li><strong>DeFi Protocols:</strong> Smart contract security auditing (Base, Ethereum, BSC, Polygon, Solana)</li>
          <li><strong>NFT Projects:</strong> Minting and marketplace vulnerability detection</li>
          <li><strong>DAO Treasuries:</strong> Governance and fund protection</li>
          <li><strong>Farcaster Miniapps:</strong> UI-based security auditing with visual proof</li>
          <li><strong>Bug Bounty:</strong> Autonomous submission to platforms like Immunefi</li>
        </ul>
      </Section>
    </>
  )
}

function QuickstartContent() {
  return (
    <>
      <Section heading="Prerequisites">
        <ul className="list-disc list-inside space-y-2 text-muted-foreground mb-4">
          <li>Python 3.8+</li>
          <li>Node.js (for agent-browser and Farcaster miniapp)</li>
          <li>Git</li>
        </ul>
      </Section>
      <Section heading="Installation">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm">
          <div className="text-muted-foreground"># Clone the repository</div>
          <div className="text-foreground">git clone https://github.com/agentxploitor/agentxploitor.git</div>
          <div className="text-foreground">cd agentxploitor</div>
          <div className="text-muted-foreground mt-2"># Install Python dependencies</div>
          <div className="text-foreground">pip install -r requirements.txt</div>
          <div className="text-muted-foreground mt-2"># Install miniapp dependencies</div>
          <div className="text-foreground">cd miniapp &amp;&amp; npm install</div>
          <div className="text-muted-foreground mt-2"># Copy environment config</div>
          <div className="text-foreground">cp .env.example .env.local</div>
          <div className="text-green-400 mt-1"># Fill in your API keys in .env.local</div>
        </div>
      </Section>
      <Section heading="Quick Demo (30 seconds)">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm">
          <div className="text-foreground">python3 examples/demo.py --quick</div>
        </div>
        <p className="text-muted-foreground">Expected output:</p>
        <div className="rounded-lg bg-secondary/30 p-4 my-2 font-mono text-sm text-muted-foreground">
          <div>🚀 Agentxploitor Quick Demo</div>
          <div className="mt-2">✅ Found 2 vulnerabilities</div>
          <div>✅ Generated exploit: Authorization Bypass</div>
          <div>✅ Verification: True/False</div>
          <div>   Visual proof: /tmp/agentxploitor-proof-VULN-001.png</div>
        </div>
      </Section>
      <Section heading="Farcaster Miniapp">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm">
          <div className="text-muted-foreground"># Run the miniapp locally</div>
          <div className="text-foreground">cd miniapp</div>
          <div className="text-foreground">npm run dev</div>
          <div className="text-green-400 mt-1"># Opens at http://localhost:3000</div>
        </div>
        <p className="text-muted-foreground">
          The miniapp runs on Base chain and integrates with Farcaster for authentication. 
          Users can request audits directly from their Farcaster feed.
        </p>
      </Section>
      <Section heading="Basic Usage">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm overflow-x-auto">
          <pre>{`import asyncio
from src.agentxploitor import AgentxploiTorAgent

async def audit_target():
    agent = AgentxploiTorAgent(
        browser_perception=True,
        auto_submit=False
    )
    
    # Scan for vulnerabilities
    vulnerabilities = await agent.scan_target("https://your-target.com")
    
    # Generate exploit for highest severity
    vuln = max(vulnerabilities, key=lambda v: v.cvss_score)
    exploit = await agent.generate_exploit(vuln)
    
    # Verify with visual proof
    verification = await agent.verify_exploit(
        vulnerability=vuln,
        exploit=exploit,
        capture_visual=True
    )
    
    if verification.success:
        print(f"✅ Exploit verified!")
        print(f"   Proof: {verification.proof_path}")

asyncio.run(audit_target())`}</pre>
        </div>
      </Section>
    </>
  )
}

function DemoScriptContent() {
  return (
    <>
      <Section heading="Pre-Recording Checklist">
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li>Close unnecessary applications</li>
          <li>Clean up desktop/background</li>
          <li>Set terminal to full screen</li>
          <li>Font size 14-16pt minimum</li>
          <li>Test screen recorder</li>
        </ul>
      </Section>
      <Section heading="Recording Script (2-3 minutes)">
        <div className="space-y-4 my-4">
          <div className="rounded-lg border border-border p-4">
            <div className="font-semibold text-accent mb-1">0:00-0:15 — Opening</div>
            <p className="text-sm text-muted-foreground">
              Title: &quot;Agentxploitor — The First AI Security Agent with Visual Exploit Verification&quot;
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-semibold text-accent mb-1">0:15-0:30 — Problem</div>
            <p className="text-sm text-muted-foreground">
              Traditional tools find bugs but cannot prove they work. Humans must manually verify.
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-semibold text-accent mb-1">0:30-2:30 — Live Demo</div>
            <div className="rounded-lg bg-secondary/30 p-2 mt-2 font-mono text-xs">
              python3 examples/demo.py --quick
            </div>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-semibold text-accent mb-1">2:30-3:00 — Key Differentiators</div>
            <p className="text-sm text-muted-foreground">
              Visual verification, self-evaluation, fully autonomous operation
            </p>
          </div>
        </div>
      </Section>
      <Section heading="Editing Tips">
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li>Keep under 3 minutes total</li>
          <li>Show the actual terminal output (not mocks)</li>
          <li>Open the screenshot proof file</li>
          <li>Use text overlays for key points</li>
          <li>Export as MP4, H.264, 1920x1080</li>
        </ul>
      </Section>
    </>
  )
}

function AutonomyContent() {
  return (
    <>
      <Section heading="The Critical Distinction">
        <div className="grid gap-4 sm:grid-cols-2 my-6">
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
            <div className="font-semibold text-red-400 mb-2">A Bot</div>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Executes scripted actions</li>
              <li>• &quot;If X then Y&quot; logic</li>
              <li>• No decision-making</li>
              <li>• No learning</li>
            </ul>
          </div>
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
            <div className="font-semibold text-green-400 mb-2">An Agent</div>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Evaluates options</li>
              <li>• Chooses strategies</li>
              <li>• Learns from feedback</li>
              <li>• Adapts to results</li>
            </ul>
          </div>
        </div>
        <p className="text-center font-semibold text-accent">
          Agentxploitor is an AGENT, not a bot.
        </p>
      </Section>
      <Section heading="The Autonomy Model">
        <h4 className="font-semibold mb-2">Human-in-the-Loop for SETUP (One-Time)</h4>
        <p className="text-muted-foreground mb-4">
          Human provides identity (email), resources (wallet), permissions (browser access), 
          and constraints (what&apos;s allowed). This is proper agent design — even human security 
          researchers need these basics.
        </p>
        <h4 className="font-semibold mb-2">Agent-in-Charge for OPERATIONS (Fully Autonomous)</h4>
        <p className="text-muted-foreground">
          The agent decides WHAT to audit, HOW to exploit, WHEN exploits succeed, 
          and WHETHER to continue. No human intervention required.
        </p>
      </Section>
      <Section heading="Level 3 Operational Autonomy">
        <div className="rounded-lg border border-border bg-secondary/20 p-4 my-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-muted" />
              <span className="text-muted-foreground">Level 0: Manual Tool — Human does everything</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-muted" />
              <span className="text-muted-foreground">Level 1: Semi-Autonomous — Tool scans on schedule</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-muted" />
              <span className="text-muted-foreground">Level 2: Task Autonomy — Tool chooses how to scan</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              <span className="font-medium text-accent">Level 3: Operational Autonomy ← Agentxploitor</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-muted" />
              <span className="text-muted-foreground">Level 4: Strategic Autonomy — Agent sets own goals</span>
            </div>
          </div>
        </div>
        <p className="text-sm text-muted-foreground text-center">
          Level 3 is the optimal balance — accountable yet independent.
        </p>
      </Section>
    </>
  )
}

function VisualVerificationContent() {
  return (
    <>
      <Section heading="Why Visual Perception Matters">
        <p className="mb-4">
          Traditional agents are <strong>blind</strong>. They cannot see if an exploit worked, 
          so they need humans to verify. This breaks the autonomy loop.
        </p>
        <p className="mb-4">
          <strong>Agentxploitor can SEE</strong>:
        </p>
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li>Opens browser (like a human would)</li>
          <li>Captures screenshots (visual proof)</li>
          <li>Compares before/after (sees changes)</li>
          <li>Evaluates results (judges success)</li>
        </ul>
      </Section>
      <Section heading="The Verification Flow">
        <div className="space-y-3 my-4">
          <div className="flex items-center gap-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary font-mono text-sm">1</div>
            <span>Navigate to target application</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary font-mono text-sm">2</div>
            <span>Capture BEFORE state (screenshot)</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary font-mono text-sm">3</div>
            <span>Execute exploit payload</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary font-mono text-sm">4</div>
            <span>Capture AFTER state (screenshot)</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent font-mono text-sm">5</div>
            <span>Compare and evaluate success</span>
          </div>
        </div>
      </Section>
    </>
  )
}

function SelfEvaluationContent() {
  return (
    <>
      <Section heading="How Self-Evaluation Works">
        <p className="mb-4">
          After executing an exploit, Agentxploitor evaluates its own work using visual 
          perception and confidence scoring:
        </p>
        <div className="rounded-lg bg-secondary/30 p-4 my-4 font-mono text-sm">
          <div className="text-purple-400">evaluation</div>
          <div className="text-foreground ml-2">= await agent.self_evaluate(</div>
          <div className="text-foreground ml-4">perception=verification.after_state,</div>
          <div className="text-foreground ml-4">intent=critical_vuln.expected_outcome</div>
          <div className="text-foreground ml-2">)</div>
          <div className="mt-2 text-green-400"># Returns:</div>
          <div className="text-foreground ml-2">{'{'}</div>
          <div className="text-foreground ml-4">satisfactory: true,</div>
          <div className="text-foreground ml-4">confidence: 0.92,</div>
          <div className="text-foreground ml-4">evidence: &quot;Balance changed from 1000 to 0&quot;</div>
          <div className="text-foreground ml-2">{'}'}</div>
        </div>
      </Section>
      <Section heading="Confidence Scoring">
        <p className="text-muted-foreground mb-4">
          The agent assigns confidence scores based on visual evidence:
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-center">
            <div className="text-2xl font-bold text-green-400">≥90%</div>
            <div className="text-xs text-muted-foreground">High Confidence</div>
          </div>
          <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">70-89%</div>
            <div className="text-xs text-muted-foreground">Medium Confidence</div>
          </div>
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-center">
            <div className="text-2xl font-bold text-red-400">&lt;70%</div>
            <div className="text-xs text-muted-foreground">Low Confidence</div>
          </div>
        </div>
      </Section>
    </>
  )
}

function SecurityChecklistContent() {
  return (
    <>
      <Section heading="Pre-Deployment">
        <ul className="space-y-2 text-muted-foreground">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Copy <code>.env.local.example</code> to <code>.env.local</code></span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Set <code>AGENT_WEBHOOK_SECRET</code> to secure random value (32+ bytes)</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Never commit <code>.env.local</code> to version control</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Verify SSRF validation blocks internal IPs</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Test rate limiting on <code>/api/*</code> endpoints</span>
          </li>
        </ul>
      </Section>
      <Section heading="API Security">
        <ul className="space-y-2 text-muted-foreground">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>All user inputs validated with Zod schemas</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Audit IDs validated against regex pattern</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Request body size limits enforced</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>JWT tokens redacted from logs</span>
          </li>
        </ul>
      </Section>
      <Section heading="Quick Security Audit">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm">
          <div className="text-muted-foreground"># Check for exposed secrets</div>
          <div className="text-foreground">grep -r &quot;SECRET\|KEY\|TOKEN&quot; --include=&quot;*.ts&quot; --include=&quot;*.tsx&quot;</div>
          <div className="text-muted-foreground mt-2"># Verify .env.local in .gitignore</div>
          <div className="text-foreground">grep &quot;.env.local&quot; .gitignore</div>
          <div className="text-muted-foreground mt-2"># Type check</div>
          <div className="text-foreground">npx tsc --noEmit</div>
        </div>
      </Section>
    </>
  )
}

function AccessibilityContent() {
  return (
    <>
      <Section heading="Screen Reader Testing">
        <h4 className="font-semibold mb-2">VoiceOver (macOS)</h4>
        <ol className="list-decimal list-inside space-y-1 text-muted-foreground mb-4">
          <li>Enable VoiceOver: <kbd>Cmd + F5</kbd></li>
          <li>Navigate: <kbd>VO + Arrow Keys</kbd></li>
          <li>Test landmarks, headings, form labels</li>
        </ol>
        <h4 className="font-semibold mb-2">NVDA (Windows)</h4>
        <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
          <li>Start NVDA: <kbd>Ctrl + Alt + N</kbd></li>
          <li>Navigate: <kbd>Tab</kbd>, <kbd>Shift + Tab</kbd></li>
          <li>Verify focus indicators and ARIA roles</li>
        </ol>
      </Section>
      <Section heading="Keyboard Navigation Checklist">
        <ul className="space-y-2 text-muted-foreground">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>All interactive elements focusable</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Focus order is logical</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Escape closes modals</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 mt-1 text-green-400" />
            <span>Arrow keys navigate menus</span>
          </li>
        </ul>
      </Section>
    </>
  )
}

function AuditReportContent() {
  return (
    <>
      <Section heading="Cross-Validation Results">
        <p className="mb-4">
          Agentxploitor was audited using HexStrike AI MCP + CryptoAgents Security Agent, 
          testing both the security posture and auditing capabilities.
        </p>
        <div className="rounded-lg border border-border overflow-hidden my-4">
          <table className="w-full text-sm">
            <thead className="bg-secondary/50">
              <tr>
                <th className="px-4 py-2 text-left">Aspect</th>
                <th className="px-4 py-2 text-center">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="px-4 py-2">Infrastructure</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Good</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">API Security</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Parameterized queries</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">Secrets Management</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Environment-based</span></td>
              </tr>
              <tr>
                <td className="px-4 py-2">Code Quality</td>
                <td className="px-4 py-2 text-center"><span className="text-yellow-400">⚠ 1 bug found & fixed</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
      <Section heading="Bug Fixed">
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 my-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5" />
            <div>
              <div className="font-semibold text-yellow-400">Dataclass Ordering Issue</div>
              <p className="text-sm text-muted-foreground mt-1">
                In <code>src/security/audit_log.py</code>: Fields with defaults were placed before 
                required fields. Fixed by reordering to comply with Python dataclass rules.
              </p>
            </div>
          </div>
        </div>
      </Section>
    </>
  )
}

function FinalStatusContent() {
  return (
    <>
      <Section heading="Completion Status: 100%">
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4 my-4">
          <div className="font-semibold text-green-400 mb-2">✅ PRODUCTION READY</div>
          <p className="text-sm text-muted-foreground">
            AgentxploiTor is deployed as a Farcaster miniapp on Base chain. 
            Multi-chain QuickNode integration complete.
          </p>
        </div>
        <h4 className="font-semibold mb-2">Completed Components</h4>
        <ul className="space-y-2 text-muted-foreground">
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            Farcaster miniapp (Next.js 15, Base chain)
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            QuickNode multi-chain integration (Base, ETH, BSC, Polygon, Solana)
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            On-chain state analysis (proxy detection, admin roles, bytecode verification)
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            Transaction tracing (reentrancy detection, exploit path reconstruction)
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            Browser Perception integrated (visual exploit verification)
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            HexStrike 12-agent security pipeline
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            Marketing website (agentxploitor.netlify.app)
          </li>
        </ul>
      </Section>
    </>
  )
}

function ArchitectureContent() {
  return (
    <>
      <Section heading="System Overview">
        <div className="rounded-lg bg-secondary/30 p-4 my-4 font-mono text-xs overflow-x-auto">
          <pre>{`
┌─────────────────────────────────────────────────────────────┐
│              AgentxploiTor — Farcaster Miniapp              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Security Intelligence Core                    │  │
│  │  • Vulnerability scanner (Slither + Mythril)          │  │
│  │  • Exploit generator (HexStrike 12 agents)            │  │
│  │  • Risk assessor (CVE matching + scoring)             │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────┴────────────────────────────────────┐  │
│  │         On-Chain Data Layer (QuickNode)               │  │
│  │  • Bytecode fetch via eth_getCode                     │  │
│  │  • State analysis via eth_getStorageAt                │  │
│  │  • Transaction tracing via debug_traceTransaction     │  │
│  │  • Multi-chain: Base, ETH, BSC, Polygon, Solana       │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────┴────────────────────────────────────┐  │
│  │         Browser Perception Skill                      │  │
│  │  • Navigate to targets (miniapp auditing)             │  │
│  │  • Capture screenshots (visual proof)                 │  │
│  │  • Extract DOM/accessibility tree                     │  │
│  │  • Visual state comparison                            │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────┴────────────────────────────────────┐  │
│  │         Autonomous Workflow Engine                    │  │
│  │  1. Scan → 2. Discover → 3. Exploit                   │  │
│  │  4. Verify → 5. Evaluate → 6. Report                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          `}</pre>
        </div>
      </Section>
      <Section heading="Core Components">
        <div className="grid gap-4 sm:grid-cols-2 my-4">
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">Security Intelligence Core</div>
            <p className="text-sm text-muted-foreground">HexStrike 12-agent pipeline: Slither, Mythril, CVE matching, attack chain discovery</p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">On-Chain Data Layer</div>
            <p className="text-sm text-muted-foreground">QuickNode RPC: bytecode fetching, state analysis, proxy detection, transaction tracing</p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">Browser Perception</div>
            <p className="text-sm text-muted-foreground">Navigation, screenshots, DOM extraction, visual exploit verification</p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">Multi-Chain Support</div>
            <p className="text-sm text-muted-foreground">Base, Ethereum, BSC, Polygon (EVM) + Solana programs</p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">Farcaster Integration</div>
            <p className="text-sm text-muted-foreground">Native miniapp with Quick Auth, wallet connect, Base payments</p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/20 p-4">
            <div className="font-semibold text-accent mb-1">Self-Evolving Intelligence</div>
            <p className="text-sm text-muted-foreground">SimpleMem stores findings. Code-Voyager writes new skills autonomously.</p>
          </div>
        </div>
      </Section>
      <Section heading="Supported Chains">
        <div className="rounded-lg border border-border overflow-hidden my-4">
          <table className="w-full text-sm">
            <thead className="bg-secondary/50">
              <tr>
                <th className="px-4 py-2 text-left">Chain</th>
                <th className="px-4 py-2 text-center">Status</th>
                <th className="px-4 py-2 text-left">Capabilities</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="px-4 py-2">Base</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Live</span></td>
                <td className="px-4 py-2 text-muted-foreground">Full audit + payments</td>
              </tr>
              <tr>
                <td className="px-4 py-2">Ethereum</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Live</span></td>
                <td className="px-4 py-2 text-muted-foreground">Full audit</td>
              </tr>
              <tr>
                <td className="px-4 py-2">BSC</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Live</span></td>
                <td className="px-4 py-2 text-muted-foreground">Full audit</td>
              </tr>
              <tr>
                <td className="px-4 py-2">Polygon</td>
                <td className="px-4 py-2 text-center"><span className="text-green-400">✓ Live</span></td>
                <td className="px-4 py-2 text-muted-foreground">Full audit</td>
              </tr>
              <tr>
                <td className="px-4 py-2">Solana</td>
                <td className="px-4 py-2 text-center"><span className="text-yellow-400">⚠ Beta</span></td>
                <td className="px-4 py-2 text-muted-foreground">Program analysis (static + on-chain)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
    </>
  )
}

function ApiContent() {
  return (
    <>
      <Section heading="AgentxploiTorAgent">
        <div className="rounded-lg bg-secondary/50 p-4 my-4 font-mono text-sm">
          <div className="text-purple-400">class</div>
          <div className="text-accent">AgentxploiTorAgent</div>
          <div className="text-muted-foreground mt-2"># Initialize</div>
          <div className="text-foreground">agent = AgentxploiTorAgent(</div>
          <div className="text-foreground ml-4">browser_perception=True,</div>
          <div className="text-foreground ml-4">auto_submit=False</div>
          <div className="text-foreground">)</div>
        </div>
      </Section>
      <Section heading="Core Methods">
        <div className="space-y-4">
          <div className="rounded-lg border border-border p-4">
            <div className="font-mono text-sm text-accent mb-2">scan_target(url, depth=&quot;deep&quot;)</div>
            <p className="text-sm text-muted-foreground">
              Scans target for vulnerabilities. Returns list of Vulnerability objects with CVSS scores.
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-mono text-sm text-accent mb-2">generate_exploit(vulnerability)</div>
            <p className="text-sm text-muted-foreground">
              Generates exploit payload for identified vulnerability. Returns Exploit object.
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-mono text-sm text-accent mb-2">verify_exploit(vuln, exploit, capture_visual=True)</div>
            <p className="text-sm text-muted-foreground">
              Executes exploit and captures visual proof. Returns VerificationResult.
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="font-mono text-sm text-accent mb-2">self_evaluate(perception, intent)</div>
            <p className="text-sm text-muted-foreground">
              Evaluates success using visual perception. Returns Evaluation with confidence score.
            </p>
          </div>
        </div>
      </Section>
    </>
  )
}
