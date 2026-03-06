# Requirements — EntityHex-Powered AgentxploiTor
> Repurposed: 2026-03-04
> Original purpose: Unified audit platform (AgentxploiTor + HexStrike + CryptoAgents)
> New purpose: AgentxploiTor Farcaster miniapp powered by EntityHex as backend intelligence

---

## Why This Was Repurposed

The original spec proposed making AgentxploiTor the orchestration hub for the entire EntityHex
ecosystem. After strategic review, the relationship is clearer and more elegant:

- **EntityHex** (CryptoAgents + HexStrike) = B2B enterprise intelligence platform, production-ready,
  serving compliance officers, exchanges, DeFi protocols across 6 domains
- **AgentxploiTor** = focused security auditing agent + Farcaster consumer distribution layer
- **The relationship**: AgentxploiTor miniapp calls EntityHex's Security Agent as its backend,
  adding visual proof and Farcaster-native UX on top of HexStrike's 12-agent intelligence

EntityHex is NOT being reduced to "a backend for AgentxploiTor." It remains a full B2B platform.
AgentxploiTor is the community-facing trust-building product that will, over time, open the door
to the full EntityHex ecosystem.

---

## Problem Statement

The Farcaster/Base ecosystem has no accessible, independent security auditing infrastructure.

- Developers ship contracts without audits (can't afford $20K–$100K firms)
- End users invest capital into platforms with no independent verification
- Traditional audits are commissioned by the project itself (conflict of interest)
- Audit reports are static — done once at launch, never updated as code evolves
- Platforms get contract updates post-launch with no re-audit

**The consequence**: Capital flows into unverified, potentially vulnerable systems. When exploits
happen, trust collapses — not just in the exploited project, but in the ecosystem.

---

## Strategic Context

AgentxploiTor's Farcaster miniapp is the **trust infrastructure** for the EntityHex ecosystem.

```
Phase 1 (Now): Two features, real trust
  → Smart Contract Evaluator (powered by HexStrike 12 agents)
  → Miniapp Auditor (powered by agent-browser + HexStrike)
  → Community: "This actually works. These people know security."

Phase 2 (3-6 months): Continuous monitoring
  → Subscribe to watch any contract/miniapp for updates
  → Auto-audit triggered on changes
  → "EXIT NOW" alerts on critical findings
  → Protocol subscriptions (early warning, B2B revenue)

Phase 3 (6-12 months): EntityHex full reveal
  → Community already trusts AgentxploiTor
  → 7 CryptoAgents unlock to an established, trusting user base
  → Trading, DeFi, Compliance, Arbitrage, Market Making, NFT domains
```

---

## User Personas

### Persona 1: End User / Investor
**The most important persona.** Capital at risk, wants independent validation.

- Has found a DeFi protocol, NFT project, or miniapp they want to use
- Cannot afford or access a traditional audit firm
- Does not trust the project's own audit claims (conflict of interest)
- Needs: independent, on-demand audit they can run themselves
- Willingness to pay: HIGH — it's insurance before committing capital
- Success: "0 critical findings. I can invest with confidence."
  OR: "2 critical vulnerabilities. I'm not touching this."

### Persona 2: Miniapp Developer (Pre-Launch)
- Building a Farcaster miniapp, wants to audit before publishing
- Has frontend URL + smart contract address or GitHub repo
- Needs: comprehensive report covering UI and contract surfaces
- Success: "I know my app is safe to launch, or I have a fix list."

### Persona 3: Smart Contract Developer
- Writing contracts for a miniapp integration on Base/Farcaster
- Has contract address (testnet/mainnet) or GitHub repo with Solidity/Rust
- Needs: Slither + Mythril + HexStrike deep analysis, severity ranking
- Success: "I have a professional audit report before deployment."

### Persona 4: Security Researcher
- Hunting bugs in Farcaster miniapps for responsible disclosure or bounties
- Brings a target URL, GitHub repo, or contract address
- Needs: deep analysis, exploit patterns, visual proof for bug reports
- Success: "I found a real vulnerability with proof I can disclose."

---

## Functional Requirements

### FR-1: Smart Contract Evaluator
- Accept: EVM contract address (0x...), Solana program address, GitHub repo URL with contracts
- Chain auto-detection: Base, Ethereum, Arbitrum, Optimism, Polygon, BSC, Solana
- Source code fetch: Basescan/Etherscan API for verified contracts; GitHub clone for repos
- Analysis: Slither + Mythril (static) + HexStrike full 12-agent deep analysis
- HexStrike agents in play: CVEIntelligenceManager, VulnerabilityCorrelator,
  AIExploitGenerator, BugBountyWorkflowManager, IntelligentDecisionEngine
- Persistent memory: HexStrike's SimpleMem means each audit improves future ones
- Output: severity-ranked findings (CRITICAL → INFO), CVE matches, attack chains,
  confidence scores, downloadable JSON + markdown report

### FR-2: Miniapp Auditor
- Accept: Farcaster miniapp URL (HTTPS only), plain miniapp name (with discovery)
- Target resolution for plain names: Warpcast API search → GitHub search → ask user
- Analysis: agent-browser UI surface audit + any detected contracts audited via FR-1
- UI checks: XSS vectors, wallet connector hijacking, phishing indicators,
  insecure iframe sources, script injection points, CSP header analysis
- Visual proof: before/after screenshots on each finding, pixel diff highlighting
- Output: severity-ranked findings, visual proof viewer, responsible disclosure template

### FR-3: Payment — No Free Tier
- Pay per audit: ETH/USDC on Base (primary), BNKR 20% discount (optional)
- Pricing (indicative, to be confirmed):
  - Smart Contract Basic (Slither + Mythril): ~$15
  - Smart Contract Deep (+ HexStrike 12 agents): ~$35
  - Miniapp Audit (frontend): ~$15
  - Full Stack (frontend + contracts): ~$35
- No refunds: user pays for the process, not a guaranteed finding
  A clean report IS the product — peace of mind has value regardless of outcome
- E2B sandbox costs absorbed into pricing margin (~$1–3/audit compute cost)

### FR-4: Auth — Farcaster Only
- Farcaster Quick Auth (JWT) — already implemented in miniapp
- FID recorded on every audit for attribution and rate limiting
- Audit reports carry reporter FID for independent verification

### FR-5: Sandbox Execution — E2B
- All HexStrike dynamic analysis runs inside E2B sandboxes
- Browser analysis runs in agent-browser isolated sessions (already sandboxed)
- Static analysis (Slither/Mythril) runs safely in-process (no execution risk)
- SSRF protection: existing URL validator blocks private IPs (already implemented)

### FR-6: Reasoning Stream
- Agent thinking visible in real-time during entire job lifecycle
- Shows: discovery phase, analysis phase, finding generation, confidence scoring
- Existing ReasoningStream component + WebSocket server to be wired

### FR-7: Audit Report
- Severity-ranked vulnerability list (CRITICAL → INFO)
- Per-finding: description, location, CVE/CWE if applicable, recommended fix
- Visual proof for UI findings (screenshots with diff)
- Confidence score per finding and overall
- Independence declaration: "Independently requested. No affiliation with audited project."
- Reporter FID + timestamp (immutable, verifiable)
- Download: JSON (machine-readable) + Markdown (human-readable)

### FR-8: Responsible Disclosure (Research mode)
- Auto-generated disclosure template after audit with significant findings
- Pre-filled Farcaster cast composer with non-sensitive finding summary
- Contact developer section (Farcaster FID lookup for miniapp creator)

---

## Learning & Evolution Requirements

### LR-1: SimpleMem — Persistent Audit Memory
- Every completed audit MUST store an AuditMemoryRecord in SimpleMem
- Record includes: target ID, findings, tools used, techniques applied,
  contract version hash, source hash, reporter FID, timestamp
- `get_audit_history(target_id)` MUST return all past audits for a target in chronological order
- `find_similar(target)` MUST return semantically similar past audits to seed new analysis
- `get_delta(target_id, v1, v2)` MUST return what changed between two audit versions
- SimpleMem is the foundation of continuous monitoring — without it, Phase 2 cannot exist

### LR-2: Code-Voyager — Self-Evolving Skills
- Code-Voyager Brain MUST be loaded at SessionStart for every audit
  — injects relevant historical context, custom project skills, past findings
- Code-Voyager Brain MUST be updated at SessionEnd from audit transcript
  — extracts what was learned, updates project profile
- Skill Factory MUST run after every audit transcript is complete
  — autonomously proposes new SKILL.md files from techniques used
  — no human intervention required or permitted in skill creation
- Skills MUST be scored and refined over time based on audit outcomes
- For subscribers: project-specific skill profiles MUST be maintained per target

### LR-3: Intelligence Transparency (Glass-Box)
- System-wide learning stats MUST be displayed in miniapp UI:
  total audits completed, patterns learned, skills created
- Per-target audit history MUST be accessible to the user who requested audits on that target
- Users MUST be able to see: "Your contract matches N previously audited patterns"
- The intelligence layer is NEVER hidden — it is a feature, not infrastructure

### LR-4: Continuous Monitoring Intelligence (Phase 2 Foundation)
- Per-subscriber project profiles MUST persist across monitoring cycles
- When a contract update is detected, the system MUST:
  a) Load full audit history for that target from SimpleMem
  b) Load project-specific brain context from Code-Voyager
  c) Load custom skills built for this project
  d) Begin new audit with complete historical context
  e) Focus analysis on what changed, not what was already verified
- The delta between versions MUST be explicitly surfaced in the monitoring report:
  "These findings are NEW since your last audit. These were present before."

---

## Non-Functional Requirements

- All frontend components <400 lines (Orion-OS non-negotiable)
- No free tier — every audit has real compute cost, pricing must cover it
- No refunds — peace of mind is the product regardless of outcome
- No engagement hooks — pull model, user requests audits, no push/notifications in v1
- Agent reasoning always visible (glass-box, not black-box)
- Audit reports are immutable once generated
- HTTPS-only for all external targets
- Rate limiting per FID to prevent abuse

---

## Out of Scope (Phase 1)

- Continuous monitoring subscriptions (Phase 2)
- Protocol B2B subscriptions (Phase 2)
- Vulnerability marketplace (Phase 2)
- On-chain audit registry (Phase 2)
- Farcaster DM notifications (Phase 2)
- Docker self-hosted sandbox (E2B covers Phase 1)
- CryptoAgents domain reveal (Phase 3)
