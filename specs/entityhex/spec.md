# Spec: EntityHex-Powered AgentxploiTor Miniapp
> Repurposed: 2026-03-04
> Original: Unified audit platform merging AgentxploiTor + HexStrike + CryptoAgents
> New direction: AgentxploiTor Farcaster miniapp with EntityHex Security Agent as backend
> Consciousness Gate 1: ✅ PASSED (8.5/10 — see CONSCIOUSNESS_LOG.md)

---

## The Vision in One Sentence

A Farcaster-native security auditing miniapp that gives any user — investor, developer, or
researcher — independent, AI-powered audits of any Farcaster miniapp or smart contract,
powered by HexStrike's 12-agent intelligence, priced to reflect genuine security value, and designed to become
the trust infrastructure of the entire Base/Farcaster ecosystem — Base-native first, expanding to all major EVM chains and Solana.

---

## Strategic Context

### Why Two Features First

Smart contract evaluation and miniapp auditing are the **credibility anchors** of the crypto
ecosystem. Every project needs them. Every user with capital at risk wants them. They are the
one capability that earns trust across every user segment before anything else can be offered.

### The Trust Chain

```
Developer audits contract before launch
        ↓
User sees "Audited by AgentxploiTor" → trusts app → invests capital
        ↓
Developer succeeds → tells other developers → more audits
        ↓
End users seek independent validation → pay for peace of mind
        ↓
Platforms subscribe for continuous monitoring (Phase 2)
        ↓
Community trust established → EntityHex full reveal (Phase 3)
→ 7 CryptoAgents unlock to an already-trusting user base
```

### The Independence Moat

Every audit report carries:
- Reporter's Farcaster FID
- Timestamp
- Declaration: *"This audit was independently requested and is not affiliated with the audited project."*

This is the competitive moat traditional audit firms cannot replicate. They are paid by the
project. We are paid by the user who wants to verify the project. The conflict of interest is
structurally impossible for us.

---

## Architecture

### System Overview

```
Farcaster Miniapp (Next.js 14, port 3000)
    │
    ├── Farcaster Quick Auth (JWT) ✅ already built
    ├── Base chain payment (ETH/USDC + BNKR discount) ← wire existing stub
    │
    ▼
miniapp API layer (/api/audit/*)
    │
    ├── Smart Contract Evaluator path:
    │       ↓
    │   EntityHex Security Agent (TypeScript, port 3000/api/v1)
    │       │  POST /api/v1/agents/security/audit
    │       │  WS   /ws/{requestId}
    │       ↓
    │   HexStrike REST API (Python/FastAPI, port 8000)
    │       │  POST /api/v1/agents/security/audit
    │       │  WS   /ws/{request_id}
    │       ↓
    │   12 HexStrike Agents (with SimpleMem persistence)
    │   + Slither + Mythril + 150 tools
    │       ↓
    │   E2B Sandbox (dynamic analysis isolation)
    │
    └── Miniapp Auditor path:
            ↓
        agent-browser daemon (isolated browser sessions)
            ↓
        UI surface analysis + visual proof capture
            ↓
        Any detected contracts → Smart Contract Evaluator path above
```

### What Already Exists (Do Not Rebuild)

| Component | Location | Status |
|-----------|----------|--------|
| Farcaster Quick Auth | `miniapp/src/app/api/auth/` | ✅ Real, working |
| Base chain payment verification | `miniapp/src/lib/payment.ts` | ✅ Real (viem + RPC) |
| Security URL validator / SSRF protection | `miniapp/src/lib/security.ts` | ✅ Real, working |
| In-memory job store + state machine | `miniapp/src/lib/storage.ts` | ✅ Real structure |
| Rate limiting middleware | `miniapp/src/middleware.ts` | ✅ Real, working |
| All UI components (forms, dashboard, stream) | `miniapp/src/components/` | ✅ Built, need data |
| ReasoningStream component | `miniapp/src/components/ReasoningStream.tsx` | ✅ Built |
| EntityHex Security Agent | `cryptoagents-master/src/agents/security-agent-service.ts` | ✅ Production ready |
| HexStrike REST API | `hexstrike.aiV2-main/` | ✅ Production ready |
| HexStrike WebSocket streaming | `hexstrike.aiV2-main/api/websocket/` | ✅ Production ready |
| agent-browser daemon | `agentxploitor/agent-browser/` | ✅ Production ready |

### What Needs to Be Built / Wired

| Gap | What it is | Tier |
|-----|-----------|------|
| Queue worker | Processes jobs from queue, calls EntityHex Security Agent | CRITICAL |
| WebSocket server | Bridges HexStrike WS events → miniapp client | CRITICAL |
| Form → API wiring | AuditRequestForm doesn't call submit API | CRITICAL |
| Persistent storage | Replace in-memory store with Vercel KV or Redis | HIGH |
| E2B sandbox wrapper | Wrap HexStrike dynamic analysis calls in E2B | HIGH |
| Payment form completion | `writeContract()` for ETH/USDC + BNKR on Base | HIGH |
| Target input extension | Accept contract address + GitHub repo (not just URL) | HIGH |
| Report generation | Build real report from HexStrike findings | HIGH |
| Visual proof pipeline | agent-browser screenshots → results viewer | MEDIUM |
| Responsible disclosure | Auto-generate template from findings | MEDIUM |

---

## Feature 1: Smart Contract Evaluator

### Input Acceptance
- EVM contract address: `0x...` (40 hex chars) — auto-detected
- Solana program address: base58 format — auto-detected
- GitHub repo URL: `github.com/...` — clone + detect contracts
- Chain auto-detection: Base (primary), Ethereum, Arbitrum, Optimism, Polygon, BSC, Solana
- **Phase 1 supported**: Base (EVM) — full support, native payment settlement
- **Phase 2 expansion**: Arbitrum, Optimism (same EVM tooling, low friction)
- **Phase 3 expansion**: Ethereum mainnet, Polygon
- **Phase 4 expansion**: Solana (agent core already has partial support)
- Unsupported chains: surface graceful "chain coming soon" message, do not hard-fail

### Resolution Flow
```
Contract address provided
    │
    ├── EVM: call Basescan/Etherscan API → fetch verified source
    │         if unverified → bytecode only (Mythril can handle)
    │
    ├── Solana: fetch program account → source if available
    │
    └── GitHub URL: clone repo → detect .sol / .rs files → analyse all
```

### Analysis Pipeline
```
Source obtained
    ↓
POST /api/v1/agents/security/audit (EntityHex Security Agent)
{
  "contract_address": "0x...",
  "blockchain": "base",
  "scan_type": "comprehensive",
  "options": { "include_exploits": true, "deep_analysis": true }
}
    ↓
EntityHex calls HexStrike POST /api/v1/agents/security/audit
    ↓
HexStrike orchestrates 12 agents:
  - IntelligentDecisionEngine: selects optimal tools
  - CVEIntelligenceManager: matches known CVEs
  - VulnerabilityCorrelator: builds attack chains
  - AIExploitGenerator: generates PoC exploits
  - BugBountyWorkflowManager: structures findings
  - PerformanceMonitor: tracks analysis quality
  - + 6 supporting agents
    ↓
Results streamed via WebSocket events → miniapp client
    ↓
Report generated with:
  - Severity-ranked findings (CRITICAL → INFO)
  - CVE/CWE references
  - Attack chains
  - Exploit PoCs (sandboxed via E2B)
  - Confidence scores
  - Fix recommendations
```

### Decision Logic (from EntityHex Security Agent)
| Condition | Status | Action |
|-----------|--------|--------|
| Critical vulns found | BLOCKED | Report immediately, strong warning |
| High vulns only | REVIEW | Report with recommended actions |
| Medium only | CAUTION | Report with fix recommendations |
| Low/Info only | CLEAR | Report confirming low risk |
| No vulns | CLEAN | Report confirming safety |

---

## Feature 2: Miniapp Auditor

### Input Acceptance
- HTTPS URL: used directly as browser target
- Plain miniapp name: 3-tier discovery (Warpcast API → GitHub → ask user)
- Any detected contracts on the page → automatically fed into Feature 1 pipeline

### Discovery Flow (plain name input)
```
"SuperSwap" entered
    ↓
Tier 1: Search Warpcast API for frames/miniapps matching name
    → Found? Show candidates → user confirms → proceed
    ↓ (not found)
Tier 2: Search GitHub for matching public repos
    → Found? Show candidates → user confirms → proceed
    ↓ (not found)
Ask user: "We couldn't find SuperSwap automatically.
          Please provide a direct URL or contract address."
```

### Browser Analysis Pipeline
```
URL confirmed
    ↓
agent-browser daemon: navigate to target
    ↓
UI surface checks:
  - DOM inspection: XSS vectors, event handler injection
  - Script sources: external scripts, integrity attributes
  - iframe sources: cross-origin, sandboxing
  - Wallet connector: known connectors vs suspicious implementations
  - CSP headers: missing or weak policies
  - Phishing indicators: misleading UI, fake approval dialogs
  - Network requests: suspicious external calls during wallet connect
    ↓
For each finding:
  - Capture before screenshot
  - Trigger finding condition
  - Capture after screenshot
  - Generate pixel diff with highlighted regions
    ↓
Contract detection:
  - Extract any contract addresses from page source + network calls
  - Feed to Feature 1 pipeline automatically
    ↓
Report: UI findings + contract findings + visual proof
```

---

## Payment Model

### Pricing
| Product | Price (ETH/USDC) | BNKR (20% off) | Rationale |
|---------|-----------------|----------------|-----------|
| Contract Basic (Slither + Mythril only) | $79 | ~$63 | Credible entry point — not a bot scan |
| Contract Deep (+ HexStrike 12 agents) | $199 | ~$159 | 12 agents + E2B + intelligence layer — real work |
| Miniapp Audit (UI surface + visual proof) | $79 | ~$63 | Visual proof is unique — charge for it |
| Full Stack (frontend + contracts) | $349 | ~$279 | Competitive with low-end human audit firms |

**Pricing Philosophy**: Price reflects the value of independent verification, not the cost of compute.
A user investing $10,000+ into a protocol pays 0.8–3.5% for structural independence — that is rational.
Low pricing signals "automated scanner"; our pricing signals "serious security audit".

**Phase 2 monitoring subscriptions**: $299–$499/month (2–3× a single audit).
Users who paid $199 for a one-time audit see monthly monitoring as a clear value escalation.

### Payment Flow
```
User selects audit type → sees price
    ↓
Pay with ETH/USDC on Base (primary)
OR
Pay with BNKR on Base (20% discount for community)
    ↓
miniapp verifies tx on-chain (viem + Base RPC) ← already built
    ↓
Job queued → audit runs → results delivered
```

### No Refunds Policy
User pays for the audit process, not a guaranteed finding.
A clean report = peace of mind = the product.
This is stated clearly before payment.

---

## E2B Sandbox Integration

HexStrike's dynamic analysis (AIExploitGenerator, tool execution) runs inside E2B sandboxes.

```python
# Wrapper around HexStrike dynamic analysis calls
import e2b

async def run_hexstrike_dynamic(contract_address: str, analysis_type: str):
    sandbox = await e2b.AsyncSandbox.create()
    try:
        # Install tools in sandbox
        await sandbox.commands.run("pip install slither-analyzer mythril")
        # Run analysis
        result = await sandbox.commands.run(
            f"slither {contract_address} --json -"
        )
        return parse_slither_output(result.stdout)
    finally:
        await sandbox.kill()
```

Static analysis (Slither/Mythril invoked directly) and browser analysis (agent-browser)
do not need E2B — they are already isolated or inherently safe.

---

## Data Model

### Extended AuditJob (extends existing storage.ts job model)
```typescript
interface AuditJob {
  // existing fields
  id: string
  status: JobStatus
  fid: number                          // Farcaster FID
  createdAt: Date
  updatedAt: Date

  // new fields
  auditType: 'contract_basic' | 'contract_deep' | 'miniapp' | 'full_stack'
  targetType: 'contract_evm' | 'contract_solana' | 'github_repo' | 'miniapp_url'
  rawInput: string                     // exactly what user typed
  resolvedTarget: ResolvedTarget       // what agent resolved to
  discoveryTier?: 1 | 2 | 3           // which tier found the target
  paymentToken: 'eth' | 'usdc' | 'bnkr'
  paymentTx: string                    // on-chain tx hash
  hexstrikeRequestId?: string          // HexStrike job ID for WS tracking
  e2bSandboxId?: string               // E2B sandbox ID if dynamic analysis
}

interface ResolvedTarget {
  type: 'contract_evm' | 'contract_solana' | 'github_repo' | 'miniapp_url'
  value: string
  chain?: string
  sourceAvailable: boolean
  confirmedByUser: boolean
}

interface AuditReport {
  jobId: string
  completedAt: Date
  findings: Finding[]
  overallSeverity: 'critical' | 'high' | 'medium' | 'low' | 'clean'
  confidenceScore: number
  independenceDeclaration: string      // immutable, on every report
  reporterFid: number
  visualProofs?: VisualProof[]         // miniapp audits only
  downloadUrl: string                  // signed URL to JSON + markdown
}
```

---

## New API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/audit/discover` | POST | Resolve plain name → candidates |
| `/api/audit/request` | POST | Extended — new fields (auditType, targetType, etc.) |
| `/api/audit/status/[id]` | GET | Existing — no change |
| `/api/audit/results/[id]` | GET | Extended — full report with findings |
| `/api/disclosure/[id]` | GET | Generate responsible disclosure template |
| `/api/ws` | WS | Bridge HexStrike events → client |

---

## Miniapp Component Architecture

All components <400 lines. Single responsibility.

```
miniapp/src/components/
├── audit-request/
│   ├── TargetInputForm.tsx        # Extended: contract address + GitHub + URL + name
│   ├── AuditTypeSelector.tsx      # Contract Basic/Deep, Miniapp, Full Stack
│   ├── TargetPreview.tsx          # Resolved target confirmation step
│   └── PaymentGate.tsx            # ETH/USDC/BNKR payment with price display
│
├── audit-results/                 # Extend existing components
│   ├── FindingCard.tsx            # Already exists — extend with CVE/attack chain
│   ├── VisualProofViewer.tsx      # NEW — before/after screenshots with diff
│   ├── ContractAuditView.tsx      # NEW — contract-specific layout
│   ├── ReportHeader.tsx           # NEW — independence declaration + reporter FID
│   └── ReportDownload.tsx         # NEW — JSON + markdown download
│
└── discovery/
    └── TargetResolutionStatus.tsx # NEW — animated 3-tier discovery progress
```

---

## Learning & Evolution Architecture

This is the intelligence foundation that separates AgentxploiTor from every other security tool.
It is built on two open-source, academically-grounded systems — leveraged and integrated as the
memory and learning substrate for the entire platform.

### The Two Foundations

**SimpleMem** (open source, academic provenance)
A structured memory architecture that gives agents persistent, queryable knowledge across
sessions. Every audit fact — what was found, where, when, with what confidence — is stored and
retrievable via semantic similarity search. Agents don't start from zero. They start from
everything they've learned before.

**Code-Voyager** (open source, university research)
A self-evolving skill system that mines agent transcripts after each execution, extracts
reusable techniques, and writes new SKILL.md files autonomously. No human programs what the
agent learns. The agent decides what's worth remembering and writes its own improvement plan
from experience. Skills are scored, refined, and promoted over thousands of executions.

These are not add-ons. They are the intelligence substrate everything else runs on.

### The Three-Layer Memory Stack

```
┌─────────────────────────────────────────────────────┐
│  SKILL LAYER (Code-Voyager)                         │
│  "How to do things"                                 │
│  → Exploit techniques, testing methodologies        │
│  → Tool selection workflows, chain-specific patterns│
│  → Written by the agent from its own experience     │
│  → Scored and refined over thousands of executions  │
├─────────────────────────────────────────────────────┤
│  FACT LAYER (SimpleMem)                             │
│  "What happened when"                               │
│  → Specific vulnerabilities found, per contract     │
│  → Scan results, confidence scores, timestamps      │
│  → Vector similarity: "this pattern matches X"      │
│  → Temporal: "what changed between v1 and v2"       │
├─────────────────────────────────────────────────────┤
│  CONTEXT LAYER (Code-Voyager Brain)                 │
│  "Current project state"                            │
│  → Goals, decisions, progress across sessions       │
│  → SessionStart injects context automatically       │
│  → SessionEnd updates brain from transcript         │
│  → Survives restarts, new sessions, team changes    │
└─────────────────────────────────────────────────────┘
```

### The Self-Evolution Loop

```
Audit runs
    ↓
Findings generated → stored in SimpleMem (facts)
    ↓
Transcript mined by Code-Voyager Skill Factory
    ↓
New skills proposed autonomously:
  "Here is a reusable technique I used on this contract type"
  "This access control pattern appears in 3 Base contracts"
  "Proxy upgrade checks should run before reentrancy analysis"
    ↓
Skills stored, scored, refined across all future audits
    ↓
Next audit: relevant skills retrieved automatically
    ↓
Better audit → better transcript → better skills
    ↓
← loops forever, zero human intervention required
```

The agent writes its own improvement plan. We don't programme what it learns.

### The Compound Intelligence Effect

```
Audit 1:   System starts with foundational security knowledge
Audit 100: System has learned 30+ Base-specific vulnerability patterns
Audit 500: System recognises contract families, predicts likely issues
Audit 1000: System has domain expertise no human team could replicate
             — built from real audits, not theory
```

Every user who pays for an audit contributes to the intelligence of every future audit.
Early users help train the system. The system gets better for everyone.

### How This Powers Continuous Monitoring (Phase 2)

This is where SimpleMem + Code-Voyager become transformative for subscribers:

```
Subscriber: Protocol X, monitoring enabled

First audit (Month 1):
  → System audits cold, finds 2 medium findings
  → SimpleMem records: full findings, steps, tools used, contract state
  → Code-Voyager mines transcript:
       Creates Skill: "Protocol X uses custom access control —
                       check modifier inheritance before reentrancy"
  → Brain updated: Protocol X profile stored permanently

Contract update detected (Month 3):
  → Trigger fires: bytecode at address changed
  → System wakes with FULL context:
       "I audited this before. Here is what I found."
       "Here is the custom skill I built for this project."
       "Here is exactly what changed between v1 and v2."
       "Skipping what is already verified. Focusing on new code paths."
  → Audit is dramatically faster and more precise
  → Finds: 1 critical vulnerability in the NEW code specifically
  → SimpleMem updated: delta between v1 and v2 recorded
  → Skill refined: "Protocol X v2 introduced delegatecall risk"

Contract update detected (Month 6):
  → Two audits of history available
  → Custom skill refined twice from real findings
  → Pattern recognition highly tuned to THIS specific project
  → Audit faster still, findings more precise than any human analyst
    starting fresh from a new engagement
```

This is not a generic monitoring service. It is a dedicated AI security analyst
that knows each subscriber's project better with every passing audit.

### The Intelligence Moat

The moat is not the technology stack — open source tools can be copied.
The moat is the **accumulated intelligence that can only be built over time**:

- Thousands of independent audits across hundreds of contracts
- Skills written from real findings, not theoretical knowledge
- Project-specific memory that grows with every monitoring cycle
- Pattern libraries no competitor can replicate without running the same audits

By the time a competitor tries to replicate the product, the system has
a year of learned intelligence that cannot be purchased or accelerated.

### User-Facing Transparency

Because this is a glass-box system, users see the learning in action:

```
"AgentxploiTor has completed 847 independent audits on Base.
 It has learned 234 distinct vulnerability patterns.
 Your contract matches 3 previously audited patterns.
 Scanning for known issues first..."
```

This is not marketing copy. It is the actual system state — visible and verifiable.

### Data Flow: What Gets Stored Per Audit

```typescript
interface AuditMemoryRecord {
  // SimpleMem facts
  targetId: string              // contract address or miniapp URL
  targetType: string            // evm_contract | solana_program | miniapp_url
  chain: string                 // base | ethereum | solana etc.
  auditedAt: Date
  findings: Finding[]           // full findings with severity + location
  toolsUsed: string[]           // which HexStrike agents ran
  techniquesUsed: string[]      // which skill IDs were applied
  contractVersion: string       // bytecode hash at time of audit
  sourceHash?: string           // source code hash if available

  // Code-Voyager brain context
  projectProfile?: string       // for subscribers: accumulated project knowledge
  customSkillIds: string[]      // skills created/refined from this audit
  transcriptSummary: string     // what the agent learned this session
}
```

---

## PBT Validation Strategy

> Added 2026-03-04 — aligned with spec-architect v2 (SKILL-PHASE2.md) and pm-auditor v1.1.0

### Focused Testing Components (Tier 1)
These components are validated through standard focused tests (2–8 per group):
- UI components: `AuditRequestForm`, `AuditTypeCard`, `VisualProofViewer`, `FindingCard`
- Integration workflows: full audit E2E flows (Groups 3, 4, 6)
- External service interactions: Warpcast API, GitHub API, Basescan API (all mocked in tests)
- Business process flows: job state machine transitions

### Property-Based Testing Components (Tier 2)
These are security-critical paths requiring mathematical property validation:

| Component | PBT Property |
|-----------|-------------|
| Price calculation | `∀ auditType, token: bnkr_price(type) = base_price(type) × 0.8` |
| Input detection | `∀ input: detect(input) ∈ {contract_evm, contract_solana, github_repo, miniapp_url, plain_name}` |
| Payment verification | `∀ tx: verified(tx) → amount_gte(tx, expected_price)` |
| SSRF protection | `∀ url: is_private_ip(url) → rejected(url)` |
| Rate limiting | `∀ fid, window: requests(fid, window) > limit → 429_returned` |
| Auth validation | `∀ jwt: expired(jwt) → requires_reauth(jwt)` |
| Independence declaration | `∀ report: has_fid(report) ∧ has_timestamp(report) ∧ has_declaration(report)` |
| Job state machine | `∀ job: status_transitions_are_monotonic(job)` — no backwards transitions |

### Security-Critical Properties (formal)
1. **Payment integrity**: `∀ auditType, paymentToken: finalPrice = BNKR ? basePrice × 0.8 : basePrice`
2. **Access control**: `∀ request: fid_authenticated(request) → can_submit_audit(request)`
3. **Input sanitization**: `∀ url: validate(url) → no_ssrf(url) ∧ no_xss(url)`
4. **Rate limiting**: `∀ fid: within_rate_limit(fid) → request_processed(fid)`
5. **Job isolation**: `∀ jobA, jobB: jobA.fid ≠ jobB.fid → results_isolated(jobA, jobB)`
6. **Audit integrity**: `∀ report: independence_declaration_immutable(report)`

### Validation Timeline
- **Phase 3a (Groups 0–4)**: Focused tests during each group's implementation
- **Phase 3b (Group 5–6)**: PBT validation for all security-critical paths above
- **Phase 4 (Post-Group 6)**: PM-Auditor full audit with PBT evidence bundle

### Evidence Requirements for PM-Auditor Gate
When PM-Auditor activates at feature completion, evidence bundle must include:
- `specs/entityhex/pbt-properties.ts` — property definitions
- `specs/entityhex/pbt-report.md` — PBT results (test case counts, counterexamples found + fixed)
- `specs/entityhex/security-audit-prep.md` — pre-validated components list
- Test logs from all 6 groups
- TypeScript zero-error confirmation
- Component size audit (all <400 lines)

---

## Consciousness Assessment

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Consciousness Expansion | 9/10 | Makes professional security accessible to all; empowers users to protect their own capital without replacing their judgment |
| Glass-Box Transparency | 9/10 | Reasoning stream, visual proof, independence declaration — nothing hidden |
| Elegant Systems | 8/10 | Reuses 70%+ of existing infrastructure; new components focused and small |
| Truth Over Theater | 9/10 | Visual proof required; no refunds enforces honest pricing; independence declaration is structural |

**Average: 8.75/10 ✅ Gate 1 PASSED**

---

## Implementation Phases

### Phase 1 (This Spec) — ~6 iterations
- Feature 1: Smart Contract Evaluator (powered by HexStrike)
- Feature 2: Miniapp Auditor (powered by agent-browser)
- Payment: ETH/USDC on Base + BNKR discount
- E2B sandbox for dynamic analysis
- Responsible disclosure template

### Phase 2 — Continuous Monitoring
- Contract change watchers (on-chain event listeners)
- Auto-audit on detected changes
- User alert system (pull model — check in-app, not push)
- Protocol B2B subscriptions (early warning before public disclosure)
- Vulnerability marketplace (sell fix reports to non-subscribing protocols)

### Phase 3 — EntityHex Full Reveal
- Community trust established through AgentxploiTor
- 7 CryptoAgents unlock to trusting user base
- Trading, DeFi, Compliance, Arbitrage, Market Making, NFT domains
- Full EntityHex B2B platform for enterprise clients
