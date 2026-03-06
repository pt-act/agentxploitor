# ARCHITECTURAL_DECISIONS.md — AgentxploiTor
> Newest entries at top. Updated: 2026-03-04

---

## [2026-03-04] ADR-001: Sandbox Strategy for Miniapp Auditor

**Decision**: Docker container per audit job (self-hosted), with E2B as fallback/alternative

**Context**:
Running an autonomous security agent against third-party targets requires strict isolation:
- Prevent SSRF / network pivoting
- Contain any malicious payloads discovered during analysis
- Protect host system from exploit side-effects
- Legal clarity: analysis is contained, not adversarial

**Options considered**:

| Option | Pro | Con |
|--------|-----|-----|
| Docker per job | Full isolation, self-hosted, cost-effective | Requires container infra |
| E2B API | Zero infra, purpose-built for AI agents | External dependency, cost per run |
| Vercel Edge only | Already deployed | Severely limited (no heavy tools) |
| agent-browser only | Already exists | UI-only, no static analysis |

**Decision rationale**:
- agent-browser already provides browser-level isolation for UI auditing
- Slither/Mythril are static analysis tools — no execution risk, run safely
- Docker needed only for dynamic analysis (future phases)
- Phase 1 can ship without full Docker sandbox using existing tools safely

**Consequence**: Phase 1 scope = static analysis + browser-based UI analysis. Dynamic exploit execution deferred to Phase 2 with proper Docker sandbox.

---

## [2026-03-04] ADR-002: Target Discovery Strategy

**Decision**: Three-tier discovery: explicit input → Warpcast API search → GitHub search

**Context**:
Users may supply: a full URL, a GitHub repo URL, a contract address, or just a miniapp name.

**Resolution order**:
1. If URL provided → validate + use directly
2. If contract address (0x...) → resolve via chain explorer API
3. If GitHub URL → clone repo, run static analysis
4. If plain name → search Warpcast API for frames/casts, then GitHub

**Consequence**: A plain name search is best-effort. UI should set expectation ("We searched for X and found Y — is this the right target?") with confirmation step before running audit.

---

## [2026-03-04] ADR-003: Audit Permission Model

**Decision**: Three-mode permission model

**Modes**:
- **Self-audit**: User supplies their own contract address or repo. No permission needed. Unlimited.
- **Research mode**: User audits a public, open-source target. Requires target to be open-source (GitHub public repo or verified open contract). Responsible disclosure framing.
- **Registry mode** (Phase 2): Targets opt-in to a public registry inviting audits. Bounty-style rewards.

**Consequence**: v1 ships Self-audit + Research mode. Registry is Phase 2.

---

## [2026-03-04] ADR-004: Frontend Component Architecture

**Decision**: Strict <400 line components, feature-based folder structure

**Pattern**:
```
miniapp/src/components/
├── audit-request/
│   ├── TargetInputForm.tsx       # Input: URL / repo / contract / name
│   ├── PersonaSelector.tsx       # Researcher / Dev / Contract Dev
│   ├── PermissionGate.tsx        # Self-audit vs Research mode
│   └── AuditConfirmation.tsx     # Target confirmation before run
├── audit-results/
│   ├── VulnerabilityList.tsx
│   ├── VisualProofViewer.tsx
│   └── ReportDownload.tsx
└── discovery/
    └── TargetPreview.tsx         # Shows resolved target before confirming
```

**Consequence**: No component exceeds 400 lines. Each has single responsibility.
