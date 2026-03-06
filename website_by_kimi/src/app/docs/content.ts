import { 
  Book, Rocket, Video, Brain, Eye, Sparkles, Shield, Lock, 
  FileCheck, Terminal, Code, CheckCircle, AlertTriangle 
} from 'lucide-react'

// Generate static params for all doc pages
export function generateStaticParams() {
  return [
    { slug: [] },
    { slug: ['introduction'] },
    { slug: ['quickstart'] },
    { slug: ['demo-script'] },
    { slug: ['autonomy-philosophy'] },
    { slug: ['visual-verification'] },
    { slug: ['self-evaluation'] },
    { slug: ['security-checklist'] },
    { slug: ['accessibility'] },
    { slug: ['audit-report'] },
    { slug: ['final-status'] },
    { slug: ['architecture'] },
    { slug: ['api'] },
  ]
}

// Documentation metadata
export const docMetadata: Record<string, {
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}> = {
  introduction: {
    title: 'Introduction',
    description: 'What is Agentxploitor and key concepts',
    icon: Book,
  },
  quickstart: {
    title: 'Quick Start',
    description: 'Get Agentxploitor running in under 5 minutes',
    icon: Rocket,
  },
  'demo-script': {
    title: 'Demo Script',
    description: 'Recording guide for video demos',
    icon: Video,
  },
  'autonomy-philosophy': {
    title: 'Autonomy Philosophy',
    description: 'Agent vs Bot — understanding true autonomy',
    icon: Brain,
  },
  'visual-verification': {
    title: 'Visual Verification',
    description: 'How browser perception enables proof',
    icon: Eye,
  },
  'self-evaluation': {
    title: 'Self-Evaluation',
    description: 'AI judging its own success',
    icon: Sparkles,
  },
  'security-checklist': {
    title: 'Security Checklist',
    description: 'Pre-deployment security audit',
    icon: Lock,
  },
  accessibility: {
    title: 'Accessibility',
    description: 'Testing guide for screen readers',
    icon: FileCheck,
  },
  'audit-report': {
    title: 'Academic Audit Report',
    description: 'Security evaluation by HexStrike AI',
    icon: Shield,
  },
  'final-status': {
    title: 'Final Status',
    description: 'Production readiness assessment',
    icon: CheckCircle,
  },
  architecture: {
    title: 'Architecture',
    description: 'System design and components',
    icon: Terminal,
  },
  api: {
    title: 'API Reference',
    description: 'Agent and model interfaces',
    icon: Code,
  },
}

export const indexMetadata = {
  title: 'Documentation',
  description: 'Everything you need to know about Agentxploitor',
  icon: Book,
}
