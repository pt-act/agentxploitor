# open_questions.md
> Updated: 2026-03-04

---

## Q1: Sandbox infrastructure preference

**Question**: Docker self-hosted or E2B API for Phase 2 dynamic analysis?

**Context**: Phase 1 uses agent-browser (UI) + Slither/Mythril (static) — both safe without full Docker sandbox. Phase 2 (dynamic exploit execution) needs real isolation.

**Options**:
- A) Docker on Fly.io / Railway — self-hosted, more control, slightly more setup
- B) E2B.dev — purpose-built AI agent sandboxes, API-based, zero infra management
- C) Both — Docker for heavy analysis, E2B for lighter agent tasks

**Decision needed by**: Before Phase 2 implementation begins

---

## Q2: BNKR pricing model ✅ RESOLVED (2026-03-04)

**Decision**: Flat rate per audit type. BNKR = 20% discount on all products.

**Final pricing**:
| Product | ETH/USDC | BNKR (20% off) |
|---------|----------|----------------|
| Contract Basic | $79 | ~$63 |
| Contract Deep | $199 | ~$159 |
| Miniapp Audit | $79 | ~$63 |
| Full Stack | $349 | ~$279 |

**Rationale**: Price reflects independent verification value, not compute cost. Low price signals "bot scanner"; higher price signals serious security audit. Phase 2 monitoring subs at $299–$499/month (2–3× single audit).

**Phase 2 pricing note**: Research mode (third-party audits) vs self-audit distinction deferred — both use same product pricing for now. Revisit in Phase 2 if usage data suggests tiering.

---

## Q3: Farcaster Frames v2 vs Mini-App SDK

**Question**: Target the Frames v2 spec or Farcaster Mini App SDK?

**Context**: Farcaster has evolved from Frames → Mini Apps. The miniapp already uses `@farcaster/frame-sdk`. Should we align fully with Mini App SDK conventions?

**Status**: Likely already using correct SDK — needs confirmation when implementing

---

## Q4: Opt-in registry design (Phase 2)

**Question**: How do miniapp developers register their app for community auditing?

**Options**:
- A) Smart contract registry on Base (on-chain opt-in)
- B) Farcaster cast with special tag (social opt-in)
- C) Off-chain database with verification

**Decision needed by**: Phase 2 planning
