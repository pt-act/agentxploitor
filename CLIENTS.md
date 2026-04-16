# Client Management Protocol — AgentxploiTor

## Purpose
All AgentxploiTor audit engagements are recorded in `memory_bank_clients/`. This is separate from `memory_bank/` (development records). AgentxploiTor publishes on MoltLaunch as a Farcaster miniapp — audit clients come through the miniapp interface.

## When to Create a Client Record

A new client directory is created when:
- A user submits an audit request via the miniapp (contract_basic, contract_deep, full_stack)
- A protocol requests continuous monitoring
- A B2B engagement is established (via EntityHex)

## Directory Structure

For each client, create: `memory_bank_clients/[client-id]/`

```
[client-id]/
├── profile.md       # WHO they are
├── audit.md         # Audit details and findings
└── revenue.md       # Payment tracking
```

### Client ID Format
`audit-[sequential-number]` — e.g., `audit-001`, `audit-002`

## Service Tiers

| Service | Price | Includes |
|---|---|---|
| Contract Basic | $79 | 4 agents, quick scan, summary report |
| Contract Deep | $199 | 10 agents, comprehensive audit, PoC exploits |
| Full Stack | $349 | All 12 agents + frontend + SDK audit |
| Continuous Monitoring | $200-1,000/mo | Weekly re-audits, alert on changes |

**BNKR token discount:** 20% off all prices

## clients-index.md

Maintain a running index at `memory_bank_clients/clients-index.md`.

---

## File Templates

### profile.md
```markdown
# Client: [Wallet/Protocol]

- **Client ID**: audit-001
- **Wallet**: 7xKXt...
- **Farcaster FID**: [if applicable]
- **Source**: MoltLaunch miniapp | Direct | EntityHex referral
- **Service Tier**: Contract Basic | Contract Deep | Full Stack
- **Payment Token**: ETH/USDC (Base) | BNKR (20% discount)
- **Amount Paid**: $XX
```

### audit.md
```markdown
# Audit: [Contract Address / GitHub URL]

- **Audit ID**: audit-001
- **Target**: 0x1234... or github.com/org/repo
- **Target Type**: contract_evm | contract_solana | github_repo | miniapp_url
- **Chain**: base | ethereum | solana
- **Audit Type**: contract_basic | contract_deep | full_stack
- **Date**: YYYY-MM-DD

## Findings
| ID | Title | Severity | Confidence |
|---|---|---|---|
| VULN-001 | Reentrancy in withdraw() | CRITICAL | 95% |
| VULN-002 | Missing access control | HIGH | 80% |

## Agent Memory Updated
- SimpleMem: Y/N
- Code-Voyager: Y/N
- Skills mined: [list]

## Report
- **Generated**: YYYY-MM-DD
- **Delivered to**: [wallet/FID]
- **Independence declaration**: "This audit was independently requested and is not affiliated with the audited project."
```

### revenue.md
```markdown
# Revenue: audit-001

| Date | Type | Amount | Token | Status |
|---|---|---|---|---|
| YYYY-MM-DD | Contract Deep | $199 | USDC | ✅ Received |
| YYYY-MM-DD | BNKR discount | -$40 | — | Applied |

**Net Revenue**: $159
**Monthly Recurring**: $0 (or $XXX/mo if monitoring)
```

---

*Last updated: 2026-03-21*
