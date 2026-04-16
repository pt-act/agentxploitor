import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export const METADATA = {
  name: "AgentxploiTor",
  description: "Autonomous AI Security Agent — discovers, exploits, and visually verifies vulnerabilities in smart contracts and Web3 protocols on Base.",
  bannerImageUrl: '/api/og', // OG image generated dynamically
  iconImageUrl: '/icon.png', // Serve from public/ or website assets
  homeUrl: process.env.NEXT_PUBLIC_URL ?? "http://localhost:3000",
  splashBackgroundColor: "#0a0e27"
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
