# Requirements — Farcaster Miniapp Auditor
> Updated: 2026-03-04

---

## Problem Statement

The Farcaster / Base miniapp ecosystem is growing rapidly, but has **no accessible security tooling**. Developers ship contracts and frontends without audits. Researchers have no structured way to hunt bugs. The ecosystem is accumulating security debt.

AgentxploiTor already has the core engine. The opportunity is to expose it as a **first-class Farcaster miniapp** — so any Farcaster user can audit any miniapp from inside their feed.

---

## User Personas & Their Jobs-to-Be-Done

### Persona 1: Security Researcher
- **Goal**: Find exploitable vulnerabilities in Farcaster miniapps and report them for bounties
- **Brings**: A miniapp name, URL, or public GitHub repo they want to investigate
- **Needs**: Autonomous discovery, exploit generation, visual proof to attach to bug report
- **Success**: "I found a real vulnerability with proof. I can submit this to the developer or a bounty platform."

### Persona 2: Miniapp Developer (Pre-Launch)
- **Goal**: Audit their own miniapp before publishing to catch issues early
- **Brings**: Their own frontend URL + smart contract address/repo
- **Needs**: Comprehensive report covering UI and contract, actionable findings, confidence score
- **Success**: "I know my app is safe to launch, or I have a prioritised list of things to fix."

### Persona 3: Smart Contract Developer
- **Goal**: Audit a contract they're writing for a miniapp integration
- **Brings**: Contract address (testnet or mainnet) or GitHub repo containing Solidity/Rust source
- **Needs**: Static analysis (Slither/Mythril), vulnerability classification, severity ranking
- **Success**: "I have a detailed contract audit report I can act on before deployment."

---

## Functional Requirements

### FR-1: Target Input
- Accept any of: miniapp name (plain text), frontend URL (HTTPS), GitHub repo URL, EVM contract address (0x...), Solana program address
- Validate and resolve input to concrete audit targets
- Show resolved target preview with confirmation step before running

### FR-2: Target Discovery (name → target)
- Tier 1: If explicit URL/address → use directly
- Tier 2: If GitHub URL → clone + analyse
- Tier 3: If plain name → search Warpcast API for frames/miniapps, then GitHub search API
- Always confirm with user before proceeding ("We found X — is this the right target?")

### FR-3: Persona & Mode Selection
- User selects persona (or system infers from input type)
- Mode: Self-audit (own app) vs Research (public app)
- Self-audit: No extra permission needed
- Research mode: Target must be open-source or publicly deployed

### FR-4: Audit Execution
- Smart contract targets → Slither + Mythril static analysis
- Frontend URL targets → agent-browser navigation + UI analysis
- GitHub repo → both contract and frontend analysis if applicable
- Agent reasoning stream visible in real-time during execution

### FR-5: Sandbox Isolation
- Phase 1: agent-browser provides browser isolation; Slither/Mythril are static (safe)
- Phase 2: Docker container per job for dynamic analysis
- SSRF protection: block private IPs, internal network ranges (already implemented)

### FR-6: Results & Visual Proof
- Vulnerability list with severity (CRITICAL → INFO)
- For each finding: description, location, recommended fix
- Visual proof for UI findings: before/after screenshots with diff
- Confidence score per finding and overall
- Downloadable JSON report

### FR-7: Payment & Auth
- Farcaster Quick Auth required (already implemented)
- BNKR token payment on Base (already implemented)
- Pricing TBD: flat rate or tiered by mode (open question Q2)

### FR-8: Responsible Disclosure
- Research mode includes auto-generated responsible disclosure template
- Links to Farcaster cast composer pre-filled with disclosure
- Optionally notify developer via Farcaster DM (Phase 2)

---

## Non-Functional Requirements

- All frontend components <400 lines
- Agent reasoning always visible (glass-box)
- No auto-polling or push notifications (pull model)
- Audit jobs are idempotent (same target + same config = same job ID)
- Rate limiting on research mode (prevent abuse)
- HTTPS-only targets in research mode
