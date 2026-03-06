# Spec: Farcaster Miniapp Auditor
> Feature: AgentxploiTor as a Farcaster miniapp that audits other miniapps
> Status: Ready for Implementation
> Updated: 2026-03-04
> Consciousness Gate 1: ✅ PASSED (8.5/10)

---

## Overview

AgentxploiTor is published as a Farcaster miniapp. Users can audit any Farcaster miniapp — or their own — by supplying a name, URL, GitHub repo, or contract address. The agent autonomously discovers the target, analyses it across three attack surfaces (smart contracts, frontend UI, backend APIs), and delivers a report with visual proof.

**Three user personas**:
1. **Security Researchers** — find bugs in other miniapps for bounties
2. **Miniapp Developers** — audit their own app before launch
3. **Smart Contract Developers** — audit contracts they're building for miniapp integrations

---

## User Flows

### Flow A: Security Researcher

```
Open AgentxploiTor miniapp in Farcaster
  → Select "Research" mode
  → Input: miniapp name / URL / GitHub repo
  → Agent resolves target (3-tier discovery)
  → Confirmation step: "Is this the right target?"
  → Select analysis type: [Smart Contract] [Frontend UI] [Full Stack]
  → Pay BNKR → Audit queued
  → Watch reasoning stream in real-time
  → View report with severity-ranked findings + visual proof
  → Download report / copy responsible disclosure template
```

### Flow B: Miniapp Developer (Self-Audit)

```
Open AgentxploiTor miniapp in Farcaster
  → Select "Self-Audit" mode
  → Input: their own frontend URL + contract address or GitHub repo
  → No discovery needed — direct to analysis type selection
  → Pay BNKR (lower rate) → Audit queued
  → Watch reasoning stream
  → View comprehensive report: UI findings + contract findings
  → Prioritised fix list with severity scores
```

### Flow C: Smart Contract Developer

```
Open AgentxploiTor miniapp in Farcaster
  → Select "Contract Audit" mode
  → Input: contract address (testnet/mainnet) OR GitHub repo URL with Solidity/Rust
  → Agent identifies chain (EVM vs Solana) automatically
  → Pay BNKR → Audit queued
  → Slither + Mythril analysis runs
  → View contract audit report: vulnerability list, severity, fix recommendations
  → Download JSON report for team review
```

---

## Architecture

### New Components Required

#### Frontend (miniapp/)

```
miniapp/src/components/audit-request/
├── TargetInputForm.tsx        # Unified input: URL/repo/address/name
├── PersonaSelector.tsx        # Researcher / Dev / Contract Dev cards
├── ModeSelector.tsx           # Self-audit vs Research vs Contract
├── TargetPreview.tsx          # Shows resolved target before confirming
├── AnalysisTypeSelector.tsx   # Smart Contract / Frontend UI / Full Stack
└── AuditConfirmation.tsx      # Final confirm before payment

miniapp/src/components/discovery/
└── TargetResolutionStatus.tsx # Shows discovery progress (3-tier)

miniapp/src/components/audit-results/
├── VulnerabilityList.tsx      # Severity-ranked findings (already exists, extend)
├── VisualProofViewer.tsx      # Before/after screenshots with diff
├── ContractAuditView.tsx      # Contract-specific findings layout
├── ReasoningStream.tsx        # Already exists — reuse
└── ReportDownload.tsx         # JSON + human-readable download
```

#### Backend (miniapp/src/app/api/)

```
/api/audit/discover            POST  — resolve name/URL to concrete targets
/api/audit/request             POST  — extend existing (add persona, mode, analysis_type)
/api/audit/status/[id]         GET   — existing, no change
/api/audit/results/[id]        GET   — existing, extend with contract findings
/api/disclosure/[id]           GET   — generate responsible disclosure template
```

#### Python Agent Layer (src/)

```
src/discovery/
├── __init__.py
├── warpcast_resolver.py       # Search Warpcast API for miniapp by name
├── github_resolver.py         # Search GitHub API + clone repo analysis
└── target_resolver.py         # Orchestrates 3-tier resolution

src/analyzers/
├── contract_analyzer.py       # Wraps Slither + Mythril (mostly exists)
└── frontend_analyzer.py       # Wraps agent-browser perception (mostly exists)
```

---

## Target Resolution: Three-Tier Discovery

```
User input
    │
    ├─ Is it a contract address? (0x... or base58)
    │   └─ Tier 1: Resolve via chain explorer → get source code → analyse
    │
    ├─ Is it a GitHub URL?
    │   └─ Tier 1: Clone repo → detect contracts + frontend → analyse
    │
    ├─ Is it an HTTPS URL?
    │   └─ Tier 1: Use directly as frontend target → browser analysis
    │
    └─ Is it a plain name?
        └─ Tier 3a: Search Warpcast API for frames/miniapps matching name
            └─ Found? → Show candidate list for user confirmation
            └─ Not found? → Tier 3b: Search GitHub for matching repos
                └─ Found? → Show candidate list
                └─ Not found? → Ask user to provide direct URL/address
```

---

## Analysis Surfaces

| Surface | Tools | Phase |
|---------|-------|-------|
| Smart contracts (EVM) | Slither, Mythril | Phase 1 |
| Smart contracts (Solana) | Static analysis (custom) | Phase 1 |
| Frontend UI | agent-browser (Playwright) | Phase 1 |
| Backend API | Black-box endpoint testing | Phase 2 |
| Dynamic exploit execution | Docker sandbox | Phase 2 |

---

## Permission Model

| Mode | Who uses it | Target requirement | Rate limit |
|------|-------------|-------------------|------------|
| Self-Audit | Devs auditing own app | None (user supplies) | Generous |
| Research | Researchers auditing others | Open-source / public deployment | Moderate |
| Contract | Contract devs | Any address or repo | Generous |
| Registry (Phase 2) | Bounty hunters | Opted-in targets | None |

---

## Sandbox Strategy (Phase 1)

- **Browser analysis**: agent-browser daemon provides full browser isolation already
- **Static analysis**: Slither/Mythril are static — zero execution risk — run safely in process
- **SSRF protection**: existing URL validator blocks private IPs (already implemented)
- **No dynamic exploit execution in Phase 1** — deferred to Phase 2 with Docker sandbox

Phase 1 is safe to ship without additional containerisation.

---

## Responsible Disclosure Flow

After audit completes in Research mode:
1. Report generated with findings
2. "Share findings responsibly" CTA appears
3. System generates a disclosure template:
   - Vulnerability summary (non-exploitable description)
   - Severity assessment
   - Recommended fix
   - Reporter attribution (Farcaster FID)
4. Pre-fills Farcaster cast composer OR generates shareable link
5. Developer notification via Farcaster DM (Phase 2)

---

## Data Model Extensions

```python
# Extend existing AuditRequest model
@dataclass
class AuditRequest:
    # existing fields...
    persona: Literal["researcher", "developer", "contract_dev"]
    mode: Literal["self_audit", "research", "contract"]
    analysis_type: Literal["contract", "frontend", "full_stack"]
    raw_input: str                    # what user typed
    resolved_targets: list[Target]   # what agent resolved to
    discovery_tier: int              # 1, 2, or 3 (which tier found it)

@dataclass
class Target:
    type: Literal["contract_evm", "contract_solana", "frontend_url", "github_repo"]
    value: str                        # address, URL, or repo path
    chain: str | None                 # "ethereum", "base", "solana", etc.
    source_available: bool            # can we get source code?
    confirmed_by_user: bool           # did user confirm this is the right target?
```

---

## Consciousness Assessment

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Consciousness Expansion | 9/10 | Makes security expertise accessible to all three personas; empowers without replacing judgment |
| Glass-Box Transparency | 8/10 | Reasoning stream shows agent thinking; visual proof is inherently transparent |
| Elegant Systems | 8/10 | Reuses 70% of existing infrastructure; new components are focused and small |
| Truth Over Theater | 9/10 | Visual proof requirement prevents fake results; responsible disclosure enforces honesty |

**Average: 8.5/10 ✅**

---

## Implementation Phases

### Phase 1: Core Auditor (This Spec)
- Target input + 3-tier discovery
- Persona + mode selection
- Contract audit (Slither/Mythril) — EVM + Solana
- Frontend audit (agent-browser)
- Results + visual proof display
- Responsible disclosure template

### Phase 2: Dynamic Analysis + Registry
- Docker sandbox for exploit execution
- Opt-in miniapp registry (on-chain)
- Developer notification via Farcaster DM
- Bounty integration

---

## Success Metrics

- Audit request → completed report in <5 minutes for contract audits
- Target resolution success rate >80% for plain-name inputs
- Visual proof generated for >90% of frontend findings
- Zero SSRF incidents (existing validator maintains this)
- User confirmation step prevents >99% of wrong-target audits
