import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export const METADATA = {
  name: "AgentxploiTor",
  description: "First AI Security Agent with Visual Exploit Verification - Autonomous Solana security audits on BASE",
  bannerImageUrl: 'https://i.imgur.com/2bsV8mV.png', // TODO: Replace with AgentxploiTor banner
  iconImageUrl: 'https://i.imgur.com/brcnijg.png', // TODO: Replace with AgentxploiTor icon
  homeUrl: process.env.NEXT_PUBLIC_URL ?? "http://localhost:3000",
  splashBackgroundColor: "#0a0e27" // Dark blue security theme
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
