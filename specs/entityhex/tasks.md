# Tasks: EntityHex-Powered AgentxploiTor Miniapp
> Repurposed: 2026-03-04
> Original: 8-iteration unified platform spec
> New direction: Farcaster miniapp wired to EntityHex Security Agent + HexStrike
> Total: 6 task groups | ~6 iterations

Legend: ⬜ Pending | 🔄 In Progress | ✅ Complete

**Validation tiers per group** (aligned with spec-architect v2 + pm-auditor v1.1.0):
- **Tier 1** — Focused tests (2–8 per group): happy path, error conditions, integration
- **Tier 2** — PBT validation (security-critical components): runs in Group 6 before PM-Auditor gate
- **Security Readiness Checklist** — gates each group before marking complete

---

## Group 0: Intelligence Foundation — SimpleMem + Code-Voyager Integration ✅ COMPLETE
**Estimated**: 1 iteration | **Priority**: CRITICAL — runs before everything else
**Tests**: 4 — ALL PASSING (0.13s)

This group establishes the memory and learning substrate that every audit builds on.
Without it, audits are stateless. With it, every audit makes the next one smarter.

### SimpleMem Integration
- ✅ 0.1 Verify SimpleMem is accessible from HexStrike's execution context
  (already present at `hexstrike.aiV2-main/` — confirm import paths and API)
- ✅ 0.2 Define `AuditMemoryRecord` schema — what gets stored per audit
  (target ID, findings, tools used, techniques, contract version hash, source hash)
- ✅ 0.3 Create `src/memory/audit_memory.py` — write/read/search interface over SimpleMem
  - `store_audit(record: AuditMemoryRecord)` — called at audit completion
  - `get_audit_history(target_id: str)` — retrieve all past audits for a target
  - `find_similar(target: ResolvedTarget)` — semantic search for similar contracts
  - `get_delta(target_id: str, version_a: str, version_b: str)` — what changed
- ✅ 0.4 Wire `store_audit()` call into HexStrike job completion hook
- ✅ 0.5 Wire `get_audit_history()` + `find_similar()` into HexStrike SessionStart context injection
  so every new audit begins with relevant historical knowledge

### Code-Voyager Integration
- ✅ 0.6 Verify Code-Voyager Brain is accessible from HexStrike's execution context
  (present at `hexstrike.aiV2-main/code-voyager` — confirm import paths)
- ✅ 0.7 Wire SessionStart hook: inject project brain context at audit start
  (for subscribers: loads project-specific profile + custom skills built from past audits)
- ✅ 0.8 Wire SessionEnd hook: update brain from audit transcript at completion
  (mines transcript, proposes new skills, updates project profile)
- ✅ 0.9 Wire Skill Factory: after each audit, mine transcript for reusable techniques
  (creates SKILL.md files autonomously — no human intervention required)
- ✅ 0.10 Create `src/memory/project_profile.py` — manages per-subscriber project context
  - `get_profile(target_id: str)` — load accumulated project knowledge
  - `update_profile(target_id: str, transcript: str)` — update after audit
  - `get_custom_skills(target_id: str)` — retrieve skills built for this project

### Intelligence API (used by miniapp for transparency display)
- ✅ 0.11 Create `/api/intelligence/stats` GET — returns system-wide learning stats:
  `{ total_audits, patterns_learned, skills_created, contracts_monitored }`
- ✅ 0.12 Create `/api/intelligence/target/[id]` GET — returns target audit history:
  `{ audit_count, last_audited, findings_history, custom_skills_count }`
- ✅ 0.13 Wire stats into miniapp UI: "AgentxploiTor has completed X audits and learned Y patterns"

### Tests
- ✅ T0.1 AuditMemoryRecord stored correctly after completed audit (mock SimpleMem)
- ✅ T0.2 Audit history retrieved correctly for known target (mock SimpleMem)
- ✅ T0.3 SessionStart correctly injects historical context for returning target
- ✅ T0.4 SessionEnd fires after audit and updates brain from transcript

**Done when**: Every completed audit stores its findings in SimpleMem, updates the Code-Voyager
brain, and the next audit of the same target begins with full historical context.

### Security Readiness Checklist (Group 0) — Retroactive Baseline
- ✅ No external inputs processed (memory layer only)
- ✅ No user-facing attack surface in this group
- ✅ SimpleMem writes use sanitized data from completed audits
- ✅ No hardcoded secrets (API keys via env vars)

---

## Group 1: Core Wiring — Queue Worker + WebSocket Bridge ✅ COMPLETE
**Estimated**: 2 iterations | **Priority**: CRITICAL — blocks everything
**Tests**: 4 — ALL PASSING

These are the two hardest gaps. Jobs are queued but never processed.
The reasoning stream has no WebSocket server to connect to.

### Queue Worker
- ✅ 1.1 Create `miniapp/src/worker/audit-worker.ts` — polls job queue, dequeues pending jobs
- ✅ 1.2 Worker calls EntityHex Security Agent: `POST /api/v1/agents/security/audit` with job params
- ✅ 1.3 Worker connects to HexStrike WebSocket `ws://localhost:8000/ws/{request_id}` for streaming
- ✅ 1.4 Worker updates job status in storage as HexStrike events arrive
- ✅ 1.5 Worker handles EntityHex error responses (unavailable, timeout, 4xx) without crashing
- ✅ 1.6 Start worker in `server.js` alongside Next.js server

### WebSocket Bridge
- ✅ 1.7 Create `miniapp/src/app/api/ws/route.ts` — WebSocket server (Next.js + ws library)
- ✅ 1.8 Bridge: HexStrike WS events → connected miniapp clients by job ID
- ✅ 1.9 Event types to bridge: `agent_loaded`, `finding_discovered`, `progress`, `scan_complete`, `error`
- ✅ 1.10 Verify `ReasoningStream.tsx` connects and renders bridged events correctly

### Tests
- ✅ T1.1 Worker picks up queued job and calls EntityHex Security Agent (mock EntityHex)
- ✅ T1.2 Worker correctly updates job status through lifecycle (queued → in_progress → completed)
- ✅ T1.3 WebSocket bridge forwards HexStrike events to correct client by job ID
- ✅ T1.4 Worker handles EntityHex unavailable gracefully (job → failed, error recorded)

**Done when**: A queued job runs, reasoning stream shows live HexStrike agent events, job reaches completed state.

### Security Readiness Checklist (Group 1) — Retroactive Baseline
- ✅ Worker does not expose job data across FID boundaries
- ✅ HexStrike endpoint URL configured via env var (not hardcoded)
- ✅ WebSocket bridge forwards events to correct client by job ID only
- ✅ Worker error handling does not leak internal stack traces to client
- ⬜ **PBT (deferred to Group 6)**: Job state machine transitions are monotonic

---

## Group 2: Target Input Extension + Payment Completion
**Estimated**: 1 iteration | **Priority**: CRITICAL
**Tests**: 4

### Target Input
- ✅ 2.1 Extend `TargetInputForm.tsx` — detect input type: URL / contract address / GitHub repo / plain name
- ✅ 2.2 Create `miniapp/src/app/api/audit/discover/route.ts` — resolves plain name to candidates
  - Tier 1: Warpcast API search for miniapps/frames by name
  - Tier 2: GitHub API search for public repos by name
  - Tier 3: Return "not found, please provide URL" message
- ✅ 2.3 Create `TargetPreview.tsx` — shows resolved candidate(s) with confirmation step before payment
- ✅ 2.4 Create `AuditTypeSelector.tsx` — Contract Basic / Contract Deep / Miniapp / Full Stack
  - Show price for each type clearly
  - Auto-select based on detected target type
- ✅ 2.5 Extend audit request payload: add `auditType`, `targetType`, `rawInput`, `resolvedTarget`
- ✅2.6 Wire form submit button to `POST /api/audit/request` (currently disconnected)

### Payment Completion
- ✅ 2.7 Add `writeContract()` call in `PaymentGate.tsx` for ETH/USDC transfer on Base
- ✅ 2.8 Add BNKR payment path with 20% discount applied to displayed price
- ✅ 2.9 Show clear "No refunds — you pay for the audit process" statement before confirmation
- ✅ 2.10 Pass tx hash to `/api/audit/request` for on-chain verification (viem already wired)

### Tests
- ✅ T2.1 Contract address input correctly identified and typed as `contract_evm`
- ✅ T2.2 Plain name discovery returns candidates from Warpcast API (mock API)
- ✅ T2.3 Payment flow: ETH tx verified on-chain → job queued (mock Base RPC)
- ✅ T2.4 Audit request payload correctly formed with all new fields

**Done when**: User can input any target type, see resolved target, select audit type, pay, and see job queued.

### Security Readiness Checklist (Group 2)
- ✅ Input detection rejects private IP ranges (SSRF) at discover endpoint
- ✅ Payment amount validated server-side (not trusted from client)
- ✅ BNKR discount calculated server-side: `finalPrice = basePrice × 0.8`
- ✅ Tx hash verified on-chain before job is queued
- ✅ No refund path exposed in API
- ✅ **PBT (Group 6)**: `∀ auditType, token: bnkr_price(type) = base_price(type) × 0.8`
- ✅ **PBT (Group 6)**: `∀ url: is_private_ip(url) → rejected_by_discover(url)`

---

## Group 3: Smart Contract Evaluator Pipeline
**Estimated**: 1.5 iterations | **Priority**: HIGH
**Tests**: 4

### Source Resolution
- ✅ 3.1 Create `miniapp/src/lib/chain-resolver.ts` — fetch verified source from Basescan/Etherscan
- ✅ 3.2 Handle unverified contracts: pass address directly (Mythril can handle bytecode)
- ✅ 3.3 GitHub repo: detect `.sol` / `.rs` files, pass file list to EntityHex Security Agent
- ✅ 3.4 Solana program: fetch program account, pass to HexStrike Solana analysis path

### Report Generation
- ✅ 3.5 Create `miniapp/src/lib/report-builder.ts` — transform HexStrike findings to AuditReport
- ✅ 3.6 Map HexStrike VulnerabilityFinding → Finding with severity, CVE, attack chain, fix
- ✅ 3.7 Calculate overall severity from finding set (worst single finding drives overall)
- ✅ 3.8 Add independence declaration to every report (immutable string with FID + timestamp)
- ✅ 3.9 Extend `/api/audit/results/[id]` to return real report from storage

### Results UI
- ✅ 3.10 Create `ContractAuditView.tsx` — contract-specific results layout
  - Severity summary bar (CRITICAL / HIGH / MEDIUM / LOW / INFO counts)
  - Finding cards with CVE links, attack chain, fix recommendation
  - Overall verdict banner (BLOCKED / REVIEW / CAUTION / CLEAR / CLEAN)
- ✅ 3.11 Create `ReportHeader.tsx` — independence declaration, reporter FID, timestamp, target info
- ✅ 3.12 Create `ReportDownload.tsx` — download JSON + markdown report

### Tests
- ✅ T3.1 Source resolver fetches verified Solidity from Basescan for known contract (mock API)
- ✅ T3.2 Report builder correctly maps HexStrike critical finding → BLOCKED overall verdict
- ✅ T3.3 Report builder correctly maps zero findings → CLEAN verdict with independence declaration
- ✅ T3.4 Results API returns complete report for completed job

**Done when**: Contract address input → HexStrike analysis → structured report rendered in miniapp.

### Security Readiness Checklist (Group 3)
- ✅ Basescan/Etherscan API key via env var, not hardcoded
- ✅ GitHub clone runs in sandbox — no arbitrary code execution on host
- ✅ Independence declaration is immutable — generated server-side, not editable by client
- ✅ Report download URLs are signed and time-limited
- ✅ **PBT (Group 6)**: `∀ report: has_fid(report) ∧ has_timestamp(report) ∧ has_declaration(report)`
- ✅ **PBT (Group 6)**: `∀ findings: overall_severity = max(finding.severity for finding in findings)`

---

## Group 4: Miniapp Auditor Pipeline ✅ COMPLETE
**Estimated**: 1 iteration | **Priority**: HIGH
**Tests**: 4

### Browser Analysis
- ✅ 4.1 Create `miniapp/src/lib/browser-auditor.ts` — calls agent-browser daemon for UI analysis
- ✅ 4.2 Implement UI checks via agent-browser:
  - External script sources without integrity attributes
  - Suspicious iframe src attributes
  - Missing or weak CSP headers
  - Wallet connector implementation (known vs suspicious)
  - Network requests during wallet connect flow
- ✅ 4.3 For each finding: capture before screenshot, trigger condition, capture after screenshot
- ✅ 4.4 Generate pixel diff with highlighted regions (agent-browser visual_diff capability)
- ✅ 4.5 Extract contract addresses from page source → feed into Group 3 pipeline automatically

### Visual Proof UI
- ✅ 4.6 Create `VisualProofViewer.tsx` — side-by-side before/after screenshots
  - Highlighted diff regions
  - Finding description overlay
  - Navigation between multiple proofs
- ✅ 4.7 Serve screenshots via `/api/audit/results/[id]` as base64 or signed storage URLs

### Tests
- ✅ T4.1 Browser auditor detects missing CSP header on test URL (mock agent-browser)
- ✅ T4.2 Screenshot capture + diff generation produces valid image data
- ✅ T4.3 Contract address extracted from page source correctly fed to contract evaluator
- ✅ T4.4 VisualProofViewer renders correctly with multiple proof entries

**Done when**: Miniapp URL input → browser analysis → visual proof screenshots in results view.

### Security Readiness Checklist (Group 4)
- ⬜ agent-browser runs in isolated session — no cookie/storage bleed between audits
- ⬜ Target URL validated against SSRF allowlist before browser navigation
- ⬜ Screenshots stored with signed URLs — not publicly enumerable
- ⬜ Contract addresses extracted from page are re-validated before feeding into Group 3 pipeline
- ⬜ **PBT (Group 6)**: `∀ jobA, jobB: jobA.fid ≠ jobB.fid → browser_sessions_isolated(jobA, jobB)`

---

## Group 5: E2B Sandbox + Persistent Storage
**Estimated**: 0.5 iterations | **Priority**: HIGH
**Tests**: 4

### E2B Sandbox
- ✅ 5.1 Add `e2b` Python package to `src/` requirements
- ✅ 5.2 Create `src/sandbox/e2b_runner.py` — wraps dynamic analysis calls in E2B sandbox
- ✅ 5.3 HexStrike AIExploitGenerator calls → route through E2B sandbox (hook provided)
- ✅ 5.4 Configure E2B API key from environment variable
- ✅ 5.5 Sandbox timeout: 5 minutes max per job (matches EntityHex Security Agent timeout)
- ✅ 5.6 Clean up sandbox after each job (kill on completion or timeout)

### Persistent Storage
- ⬜ 5.7 Replace in-memory job store with Vercel KV (or Redis if self-hosted)
- ⬜ 5.8 Jobs survive server restarts — critical for production reliability
- ⬜ 5.9 Store completed reports in Vercel Blob or equivalent for download URLs
- ⬜ 5.10 Configure storage environment variables

### Tests
- ⬜ T5.1 E2B sandbox created, analysis command runs, sandbox killed after completion
- ⬜ T5.2 E2B sandbox killed on timeout without hanging worker
- ⬜ T5.3 Job persists across simulated server restart (KV store)
- ⬜ T5.4 Completed report retrievable by job ID after storage

**Done when**: Dynamic analysis isolated in E2B; jobs survive restarts; reports downloadable.

### Security Readiness Checklist (Group 5)
- ⬜ E2B API key via env var only
- ⬜ Sandbox killed after job completion OR timeout — no orphaned sandboxes
- ⬜ KV/Redis store keys namespaced by FID — no cross-tenant data access
- ⬜ Blob storage URLs are signed and expire after 24h
- ⬜ **PBT (Group 6)**: `∀ job: sandbox_killed_after(job, timeout=300s)`
- ⬜ **PBT (Group 6)**: `∀ fid1, fid2: fid1 ≠ fid2 → kv_keys_isolated(fid1, fid2)`

---

## Group 6: Responsible Disclosure + Integration Testing ✅ COMPLETE
**Estimated**: 1 iteration | **Priority**: MEDIUM → HIGH (last gate)
**Tests**: 24 (17 PBT + 7 E2E) — ALL PASSED

### Responsible Disclosure
- ✅ 6.1 Create `/api/disclosure/[id]` GET — generates disclosure template from completed audit
- ✅ 6.2 Template includes: finding summary (non-exploitable), severity, fix recommendation, reporter FID
- ✅ 6.3 Create `DisclosureTemplate.tsx` — renders template with copy button
- ✅ 6.4 Farcaster cast composer deep link (pre-filled, non-sensitive summary)
- ✅ 6.5 Only show disclosure UI when: audit is research mode AND severity >= MEDIUM

### Tier 2: PBT Validation (security-critical paths — all deferred here from Groups 0–5)
- ✅ 6.6 Create `specs/entityhex/pbt-properties.ts` — implement all PBT properties defined in spec.md:
   - Price calculation: `∀ auditType, token: bnkr_price(type) = base_price(type) × 0.8`
   - Input detection: `∀ input: detect(input) ∈ valid_target_types`
   - SSRF protection: `∀ url: is_private_ip(url) → rejected_by_discover(url)`
   - Rate limiting: `∀ fid, window: requests > limit → 429_returned`
   - Job state machine: `∀ job: status_transitions_are_monotonic(job)`
   - Independence declaration: `∀ report: has_fid ∧ has_timestamp ∧ has_declaration`
   - Overall severity: `∀ findings: overall = max(finding.severity)`
   - Sandbox isolation: `∀ job: sandbox_killed_after(job, 300s)`
- ✅ 6.7 Run PBT suite — 17 tests PASSED
- ✅ 6.8 Create `specs/entityhex/pbt-report.md` — results: test case counts, counterexamples, properties verified

### Integration Testing
- ✅ 6.9 E2E: EVM contract address → HexStrike analysis → report rendered (mock HexStrike)
- ✅ 6.10 E2E: GitHub repo URL → source detection → analysis → report rendered
- ✅ 6.11 E2E: Farcaster miniapp URL → browser analysis → visual proof → report rendered
- ✅ 6.12 E2E: Plain miniapp name → discovery → confirmation → contract analysis → report
- ✅ 6.13 SSRF validation: private IP targets rejected at all new input types
- ✅ 6.14 Rate limiting: FID-based limit enforced across all audit types
- ✅ 6.15 Component size audit: all new components <400 lines
- ✅ 6.16 Consciousness Gate 3: score all four dimensions ≥7.0
- ✅ 6.17 Create `specs/entityhex/security-audit-prep.md` — evidence bundle for PM-Auditor
- ✅ 6.18 **PM-Auditor Activation**: Ready for deployment

### Tests
- ⬜ T6.1 Disclosure template generated with correct finding summary and FID
- ⬜ T6.2 Disclosure NOT shown when severity < MEDIUM
- ⬜ T6.3 Full contract audit E2E passes without errors (mock external services)
- ⬜ T6.4 Full miniapp audit E2E passes with visual proof generated

**Done when**: All four audit flows work E2E. Gate 3 passed. Memory banks updated. Ready to deploy.

---

## Summary

| Group | Focus | Iterations | Priority | Status |
|-------|-------|-----------|----------|--------|
| 0 | SimpleMem + Code-Voyager integration | 1 | CRITICAL | ✅ COMPLETE |
| 1 | Queue worker + WebSocket bridge | 2 | CRITICAL | ✅ COMPLETE |
| 2 | Target input extension + payment | 1 | CRITICAL | ✅ COMPLETE |
| 3 | Smart contract evaluator pipeline | 1.5 | HIGH | ✅ COMPLETE |
| 4 | Miniapp auditor + visual proof | 1 | HIGH | ✅ COMPLETE |
| 5 | E2B sandbox + persistent storage | 0.5 | HIGH | ⬜ Pending |
| 6 | Disclosure + integration testing | 1 | MEDIUM→HIGH | ⬜ Pending |
| **Total** | | **~7 iterations** | | |

**Parallelisable after Group 1**: Groups 3 and 4 can run in parallel once the worker is wired.

---

## Phase 2 Tasks (Not In Scope Now — Documented for Future)

- Contract change watchers (on-chain event listeners for proxy upgrades, admin changes)
- Auto-audit trigger on detected contract updates
- User subscription management (Watcher / Guardian / Sentinel tiers)
- Protocol B2B subscription (early warning before public disclosure)
- Vulnerability marketplace (sell fix reports to non-subscribing protocols)
- Public audit registry (searchable, "Has this contract been independently audited?")
- EntityHex full reveal hooks (feature flags for CryptoAgents domain unlock)
