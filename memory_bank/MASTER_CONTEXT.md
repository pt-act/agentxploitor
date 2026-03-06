# MASTER_CONTEXT.md — AgentxploiTor
> Newest entries at top. Updated: 2026-03-04

---

## [2026-03-04] Spec + PM Ledger Aligned with Evolved Skills

**Status**: Complete. All spec files now aligned with spec-architect v2 + pm-auditor v1.1.0.

### What changed
- `specs/entityhex/spec.md`: Added **PBT Validation Strategy** section — 8 security-critical properties formally defined, validation timeline (Phase 3a/3b/4), evidence requirements for PM-Auditor gate
- `specs/entityhex/tasks.md`: Added **Tier 1/2 validation tiers** legend, **Security Readiness Checklists** per group (0–5), **PBT tasks** (6.6–6.8) in Group 6, PM-Auditor activation step (6.18)
- `.plip/pm-ledger/`: Initialized — `milestones.md` (M1/M2), `risks.md` (R1–R8), `decisions.md` (4 locked decisions)

### PM-Auditor activation plan
- Groups 0–5: implement with Tier 1 focused tests + Security Readiness Checklists
- Group 6: run PBT suite, generate `pbt-report.md` + `security-audit-prep.md`
- Trigger: "Activate PM-Auditor for entityhex spec" — full evidence bundle required

---

## [2026-03-04] Strategic Decision: Pricing Revision + Base-First Chain Strategy

**Status**: Spec updated. Ready for Group 2 implementation.

### Pricing (Final — Do Not Revisit)
| Product | ETH/USDC | BNKR (20% off) |
|---------|----------|----------------|
| Contract Basic | $79 | ~$63 |
| Contract Deep | $199 | ~$159 |
| Miniapp Audit | $79 | ~$63 |
| Full Stack | $349 | ~$279 |

**Philosophy**: Independence is the product. Technical analysis is the delivery mechanism. Price signals quality — $15/$35 signals bot scan; $79–$349 signals serious audit. Users investing $10K+ pay 0.8–3.5% for structural independence — rational.

**Phase 2 monitoring**: $299–$499/month (2–3× single audit price — proportional and defensible).

**Brand strategy**: AgentxploiTor builds empirical trust (audit track record) → EntityHex launches to a pre-trusting audience. Every audit is a brick in the EntityHex brand wall.

### Chain Strategy (Final)
- **Phase 1**: Base (EVM) — full support, native Farcaster/payment settlement
- **Phase 2**: Arbitrum, Optimism (same EVM tooling)
- **Phase 3**: Ethereum mainnet, Polygon
- **Phase 4**: Solana (agent core already partially supports it)
- Unsupported chains: graceful "coming soon" — never hard-fail

---

## [2026-03-04] Implementation Session Complete — Groups 0 + 1

**Status**: 2 of 7 groups complete. Foundation solid. Ready for Group 2.

### Group 0 — Intelligence Foundation ✅ COMPLETE
- `src/memory/audit_memory.py` — AuditMemoryRecord + AuditMemoryStore (SimpleMem interface, delta analysis)
- `src/memory/project_profile.py` — ProjectProfile + ProjectProfileStore (Code-Voyager Brain hooks)
- `src/memory/session_hooks.py` — AuditSessionManager (full lifecycle orchestration)
- **Tests**: 4/4 passing (0.13s)

### Group 1 — Queue Worker + WebSocket Bridge ✅ COMPLETE
- `hexstrike.aiV2-main/api/security_audit_endpoint.py` — HexStrike audit endpoint + intelligence APIs
- `miniapp/src/worker/audit-worker.ts` — queue poller, HexStrike caller, WS bridge
- `miniapp/server.js` — mock stream removed, real bridge wired, worker started on boot
- `miniapp/src/app/api/audit/request/route.ts` — extended with new audit fields
- `miniapp/src/lib/types.ts` + `storage.ts` — AuditType, TargetType, PaymentToken added
- **TypeScript**: Zero errors on production code

### Website + Docs ✅ COMPLETE
- `website_by_kimi/`: hero, features, steps, comparison table, IntelligenceStats component
- `docs/`: 8 new pages + developer reference docs (code-voyager-api, simplemem-api, hexstrike-memory-wiring)
- `roadmap/INVESTOR_SUMMARY.md`: fully updated

### Next Session: Group 2
Start with `TargetInputForm.tsx` extension + `/api/audit/discover` endpoint (3-tier name resolution).

---

## [2026-03-04] Strategic Decision: EntityHex-Powered AgentxploiTor Miniapp

**Status**: Spec complete, ready for implementation

**The Final Architecture**:
AgentxploiTor Farcaster miniapp calls EntityHex's Security Agent as backend intelligence.
HexStrike's 12 agents power the analysis. agent-browser handles UI surface auditing.
E2B sandbox isolates dynamic analysis. Two features ship first to build community trust.

**The Strategic Vision**:
AgentxploiTor is the community-facing trust-building front door for the EntityHex ecosystem.
Security credibility earns trust across ALL user segments — investors, developers, researchers.
Phase 1 trust → Phase 2 monitoring subscriptions → Phase 3 full EntityHex reveal (7 CryptoAgents).

**Three-Phase Roadmap**:
- Phase 1: Smart Contract Evaluator + Miniapp Auditor (this spec)
- Phase 2: Continuous monitoring subscriptions + protocol B2B + vulnerability marketplace
- Phase 3: EntityHex full reveal — 7 CryptoAgents unlock to trusting user base

**Key Decisions Made**:
- No free tier (real compute cost per audit, pricing must cover it)
- No refunds (peace of mind is the product regardless of outcome)
- Payment: ETH/USDC on Base primary, BNKR 20% discount (not a gate)
- E2B sandbox for dynamic analysis ($98 credit = ~50-200 audit bootstrap runway)
- EntityHex and AgentxploiTor are siblings NOT parent/child — EntityHex B2B stays intact
- The entityhex spec inside AgentxploiTor repurposed (not abandoned) to reflect true relationship

**Spec location**: `specs/entityhex/spec.md` (repurposed 2026-03-04)
**Tasks location**: `specs/entityhex/tasks.md` (repurposed 2026-03-04)

**The Independence Moat**:
Every report carries: reporter FID + timestamp + independence declaration.
"This audit was independently requested and is not affiliated with the audited project."
Structurally impossible for traditional audit firms to replicate. This is the moat.

---

## [2026-03-04] Feature Ideation: Farcaster Miniapp Auditor

**Status**: Spec written, awaiting implementation

**The Idea**: Publish AgentxploiTor as a Farcaster miniapp that lets users audit OTHER miniapps (and their underlying smart contracts) on Base/Farcaster — with an isolated sandbox for safe execution.

**Three User Personas (v1)**:
1. **Security Researchers** — hunt bugs in other Farcaster miniapps for bounties
2. **Miniapp Developers** — audit their own app before launch
3. **Smart Contract Developers** — audit contracts they're building for their miniapp

**Key Insight**: All three personas share the same core workflow. They differ only in:
- What they bring (target URL / own repo / own contract address)
- What they're looking for (bugs to report / pre-launch confidence / contract correctness)

**Spec location**: `specs/farcaster-miniapp-auditor/spec.md`
**Tasks location**: `specs/farcaster-miniapp-auditor/tasks.md`

---

## Strategic Direction

AgentxploiTor's competitive moat:
- **First-mover** on Farcaster-native security auditing
- **Visual proof** of exploits — unique in the ecosystem
- **Base-native payments** already wired (BNKR token)
- **Three attack surfaces**: Frontend UI, Smart Contracts, Backend APIs

---

## Architecture Principles

- **Glass-box transparency**: Agent reasoning visible to users (reasoning stream already built)
- **Sandbox-first**: Every audit runs in an isolated execution environment
- **Pull model**: Users request audits; no push notifications or auto-polling
- **Opt-in registry**: Targets are either user-owned or publicly registered for auditing
- **Component size**: All frontend components <400 lines

---

## Current Codebase State (as of 2026-03-04)

### Core Agent (`src/`)
- `AgentxploiTorAgent` — production-ready, 96.5% hardening tasks complete
- Supports: Slither/Mythril (EVM), browser automation (agent-browser), LLM exploit gen
- Target types: Smart contracts (EVM + Solana), URLs, GitHub repos
- Visual proof: before/after screenshots with pixel diff

### Miniapp (`miniapp/`)
- Next.js 14 + TypeScript + Tailwind
- Farcaster Quick Auth ✅
- Base chain BNKR payment gating ✅
- API scaffolded: `/api/audit/request`, `/api/audit/status/[id]`, `/api/audit/results/[id]`
- Job pipeline: `pending_payment` → `payment_verified` → `queued` → `in_progress` → `completed`
- **Gap**: API stubs — agent not yet wired to backend

### Agent Browser (`agent-browser/`)
- Standalone browser automation daemon
- Already acts as UI-level sandbox (isolated browser sessions)

### Specs
- `specs/agentxploitor-hardening/` — 85/88 tasks complete ✅
- `specs/base-miniapp/` — full spec ready, awaiting impl
- `specs/farcaster-miniapp-auditor/` — NEW (2026-03-04)

---

## Technology Stack

> Open source foundations are acknowledged — the intellectual work is in the synthesis.

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Auth | Farcaster Quick Auth (JWT) |
| Payments | Base chain, BNKR token |
| Agent core | Python, asyncio |
| Memory layer | SimpleMem (open source, academic) — persistent audit facts, semantic search across sessions |
| Learning layer | Code-Voyager (open source, university research) — self-evolving skills, autonomous SKILL.md creation |
| Static analysis | Slither (EVM), Mythril (EVM) |
| Browser automation | agent-browser (Playwright-based) |
| Sandbox (planned) | Docker per-job OR E2B API |
| Target discovery | Warpcast API, GitHub Search API, ENS |

---

## Open Questions

See `memory_bank/active/open_questions.md`
