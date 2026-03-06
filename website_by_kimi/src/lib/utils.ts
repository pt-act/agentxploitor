import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const siteConfig = {
  name: 'Agentxploitor',
  tagline: 'Independent. Intelligent. Unstoppable.',
  description: 'The first autonomous AI security platform powered by 19 specialist agents that discover, exploit, and visually verify vulnerabilities in smart contracts and Farcaster miniapps — and gets smarter with every audit.',
  url: 'https://agentxploitor.xyz',
  twitter: '@agentxploitor',
  telegram: '@R1cal',
}

export const features = [
  {
    title: '19 Specialist AI Agents',
    description: 'A coordinated team of 19 AI agents — 12 deep security specialists and 7 intelligence agents — working in concert on every audit. Not a tool. A team.',
    icon: 'Brain',
  },
  {
    title: 'Visual Exploit Verification',
    description: 'Captures before/after screenshots and visual diffs. The agent sees what it created and proves the exploit works — not just reports it.',
    icon: 'Eye',
  },
  {
    title: 'Self-Evolving Intelligence',
    description: 'SimpleMem (academic-grade memory) stores every finding across sessions. Code-Voyager autonomously writes new skills from every audit transcript — no human intervention. Audit 1 vs Audit 1000 are incomparably different.',
    icon: 'Search',
  },
  {
    title: 'Smart Contract Evaluation',
    description: 'Deep static and dynamic analysis for EVM (Base, Ethereum, Arbitrum) and Solana contracts. CVE matching, attack chain discovery, exploit generation.',
    icon: 'Shield',
  },
  {
    title: 'Miniapp Security Auditing',
    description: 'Browser-based auditing of Farcaster miniapps — XSS vectors, wallet connector hijacking, phishing indicators — with visual proof of every finding.',
    icon: 'Globe',
  },
  {
    title: 'Truly Independent',
    description: 'Every report carries a verifiable independence declaration and your Farcaster ID. No relationship with the audited project. No conflict of interest. Ever.',
    icon: 'Send',
  },
]

export const steps = [
  {
    number: '01',
    title: 'Target',
    description: 'Input any smart contract address, GitHub repo, or Farcaster miniapp URL. The agent resolves and confirms the target before proceeding.',
  },
  {
    number: '02',
    title: 'Discover',
    description: '19 AI agents coordinate: CVE matching, attack chain discovery, static and dynamic analysis — EVM and Solana supported.',
  },
  {
    number: '03',
    title: 'Exploit',
    description: 'Generates working exploit payloads in an isolated sandbox. Proves vulnerabilities are real, not theoretical.',
  },
  {
    number: '04',
    title: 'Verify',
    description: 'Captures before/after screenshots with pixel-level diffs. Visual proof that the exploit works — attached to every finding.',
  },
  {
    number: '05',
    title: 'Learn',
    description: 'Code-Voyager mines the transcript and autonomously writes new SKILL files — the agent writes its own improvement plan. SimpleMem stores findings for delta analysis. Next audit of the same target begins with full historical context.',
  },
  {
    number: '06',
    title: 'Report',
    description: 'Severity-ranked findings, CVE references, fix recommendations, visual proof, and an independence declaration — all in one downloadable report.',
  },
]
