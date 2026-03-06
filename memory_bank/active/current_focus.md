# current_focus.md
> Updated: 2026-03-04

## Active Feature: EntityHex-Powered AgentxploiTor Miniapp

**Phase**: Specification Complete → Ready for Implementation

**What we're building**:
Two features that establish AgentxploiTor as the trust infrastructure for the Base/Farcaster
ecosystem — powered by EntityHex's Security Agent + HexStrike's 12 agents behind the scenes.

**Feature 1: Smart Contract Evaluator**
- Accept: contract address (EVM/Solana), GitHub repo, chain auto-detection
- Analysis: Slither + Mythril + HexStrike full 12-agent deep analysis via EntityHex Security Agent
- Output: severity-ranked report, CVE matches, attack chains, independence declaration

**Feature 2: Miniapp Auditor**
- Accept: HTTPS URL or plain miniapp name (3-tier discovery)
- Analysis: agent-browser UI surface audit + visual proof + auto-feeds contracts to Feature 1
- Output: UI findings with before/after screenshots, responsible disclosure template

**Active Spec**: `specs/entityhex/spec.md` (repurposed 2026-03-04)
**Active Tasks**: `specs/entityhex/tasks.md` (repurposed 2026-03-04)

**Note**: `specs/farcaster-miniapp-auditor/` was written earlier today in this workspace
before full context was loaded. It is superseded by the entityhex spec. It can be archived.

---

## Key Decisions (Do Not Revisit)

- No free tier — real compute cost per audit, margin must be protected
- No refunds — peace of mind is the product regardless of outcome
- ETH/USDC on Base primary, BNKR 20% discount (not a gate)
- E2B sandbox for dynamic analysis
- EntityHex = B2B sibling, NOT a backend for AgentxploiTor exclusively
- EntityHex's Security Agent IS the audit backend — do not duplicate it

---

## Progress

| Group | Focus | Status |
|-------|-------|--------|
| 0 | SimpleMem + Code-Voyager foundation | ✅ COMPLETE |
| 1 | Queue worker + WebSocket bridge | ✅ COMPLETE |
| 2 | Target input extension + payment | ✅ COMPLETE |
| 3 | Smart contract evaluator pipeline | ✅ COMPLETE |
| 4 | Miniapp auditor + visual proof | ⬜ NEXT |
| 5 | E2B sandbox + persistent storage | ⬜ |
| 6 | Disclosure + integration testing | ⬜ |

---

## Next Action — Group 2

Start with these two items in parallel:
1. **`TargetInputForm.tsx`** — extend to accept contract address, GitHub URL, plain name
2. **`/api/audit/discover`** route — 3-tier name resolution (Warpcast API → GitHub → ask user)

Then: `AuditTypeSelector.tsx` (price display per type) + payment form `writeContract()` completion.

**Spec**: `specs/entityhex/tasks.md` — Group 2 tasks all ⬜ Pending

---

## Strategic Decisions Locked (Do Not Revisit)

- No free tier — real compute cost per audit
- No refunds — peace of mind IS the product
- ETH/USDC on Base primary, BNKR 20% discount
- E2B sandbox for dynamic analysis
- EntityHex = B2B sibling, NOT absorbed by AgentxploiTor
- Phase 1 → Phase 2 (monitoring) → Phase 3 (EntityHex full reveal)

---

## Blockers

None. Foundation complete. TypeScript clean. Tests passing.
