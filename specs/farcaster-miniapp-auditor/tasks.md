# Tasks: Farcaster Miniapp Auditor
> Updated: 2026-03-04
> Total: 9 task groups | Phase 1

Legend: ⬜ Pending | 🔄 In Progress | ✅ Complete

---

## Group 1: Target Input & Discovery Layer
**Estimated**: 2 iterations | **Priority**: CRITICAL (blocks everything)

### Backend
- ⬜ 1.1 Create `src/discovery/target_resolver.py` — orchestrates 3-tier resolution
- ⬜ 1.2 Create `src/discovery/warpcast_resolver.py` — search Warpcast API by miniapp name
- ⬜ 1.3 Create `src/discovery/github_resolver.py` — search GitHub API + detect contract/frontend files
- ⬜ 1.4 Add contract address detection (EVM `0x...` pattern, Solana base58 format)
- ⬜ 1.5 Create `/api/audit/discover` POST endpoint — accepts raw input, returns resolved targets
- ⬜ 1.6 Write unit tests for all 3 resolver tiers (mock Warpcast + GitHub APIs)

### Frontend
- ⬜ 1.7 Create `TargetInputForm.tsx` — unified input field with type detection hint
- ⬜ 1.8 Create `TargetPreview.tsx` — shows resolved target(s) with confirmation step
- ⬜ 1.9 Create `TargetResolutionStatus.tsx` — animated progress through discovery tiers
- ⬜ 1.10 Wire discovery API call from `TargetInputForm` → `TargetPreview`

**Done when**: User can type a miniapp name and see a resolved target candidate before confirming.

---

## Group 2: Persona & Mode Selection UI
**Estimated**: 1 iteration | **Priority**: HIGH

- ⬜ 2.1 Create `PersonaSelector.tsx` — three cards: Researcher / Miniapp Dev / Contract Dev
- ⬜ 2.2 Create `ModeSelector.tsx` — Self-Audit / Research / Contract mode with permission explanation
- ⬜ 2.3 Create `AnalysisTypeSelector.tsx` — Smart Contract / Frontend UI / Full Stack (adapts to persona)
- ⬜ 2.4 Auto-infer persona from input type (contract address → Contract Dev, URL → Researcher/Dev)
- ⬜ 2.5 Show/hide analysis type options based on resolved target types
- ⬜ 2.6 Add mode to audit request payload schema (extend existing `AuditRequest` type)

**Done when**: User can select persona + mode + analysis type and it feels natural/guided.

---

## Group 3: Extend Audit Request API
**Estimated**: 1 iteration | **Priority**: HIGH

- ⬜ 3.1 Extend `/api/audit/request` to accept: `persona`, `mode`, `analysis_type`, `resolved_targets`, `raw_input`, `discovery_tier`
- ⬜ 3.2 Add `Target` dataclass to Python models (`src/models.py`)
- ⬜ 3.3 Add `persona`, `mode`, `analysis_type` to `AuditRequest` dataclass
- ⬜ 3.4 Rate limiting: Research mode max 5 audits/hour per FID; Self-Audit max 20/hour
- ⬜ 3.5 Validate Research mode targets are public (HTTPS or public GitHub repo)
- ⬜ 3.6 Update `AuditConfirmation.tsx` — summary screen before payment showing target + mode

**Done when**: API accepts extended payload and enforces mode-appropriate rate limits.

---

## Group 4: Contract Audit Pipeline (EVM + Solana)
**Estimated**: 2 iterations | **Priority**: HIGH

### EVM Contracts
- ⬜ 4.1 Extend `contract_analyzer.py` to accept GitHub repo URL as source input (clone + detect contracts)
- ⬜ 4.2 Add chain auto-detection from contract address (Etherscan / Basescan API for source code fetch)
- ⬜ 4.3 Return source code availability flag in discovery response
- ⬜ 4.4 Handle contracts without source (bytecode analysis via Mythril only)

### Solana Contracts
- ⬜ 4.5 Create `src/analyzers/solana_analyzer.py` — static analysis for Rust/Anchor programs
- ⬜ 4.6 Detect common Solana vulnerabilities: missing signer checks, integer overflow, CPI risks, account validation
- ⬜ 4.7 Integrate with existing analyzer registry

### Results
- ⬜ 4.8 Create `ContractAuditView.tsx` — contract-specific results layout (file tree + findings)
- ⬜ 4.9 Extend `/api/audit/results/[id]` to include `contract_findings` array with file locations

**Done when**: Contract address or GitHub repo → full Slither/Mythril report rendered in miniapp.

---

## Group 5: Frontend UI Audit Pipeline
**Estimated**: 1 iteration | **Priority**: HIGH

- ⬜ 5.1 Extend `frontend_analyzer.py` to accept miniapp URL as target
- ⬜ 5.2 Add UI-specific vulnerability checks: XSS vectors, insecure iframe src, wallet connector hijacking, phishing indicators
- ⬜ 5.3 Capture visual proof: before/after screenshots on each finding
- ⬜ 5.4 Create `VisualProofViewer.tsx` — side-by-side screenshot diff with highlighted regions
- ⬜ 5.5 Extend results API to serve screenshot data (base64 or signed URLs)
- ⬜ 5.6 Test with 3 real Farcaster miniapp URLs (use public, open-source ones)

**Done when**: Frontend URL → browser-based audit with visual proof screenshots in results view.

---

## Group 6: Reasoning Stream Integration
**Estimated**: 0.5 iterations | **Priority**: MEDIUM

- ⬜ 6.1 Verify `ReasoningStream.tsx` works with new audit types (contract + frontend)
- ⬜ 6.2 Add discovery phase to reasoning stream ("Searching Warpcast for X...", "Found contract at Y...")
- ⬜ 6.3 Add analysis phase labels to stream (Static Analysis, Browser Inspection, etc.)
- ⬜ 6.4 Ensure stream is visible during entire job lifecycle (not just analysis phase)

**Done when**: Users can watch the agent's thinking in real-time from discovery through to report.

---

## Group 7: Responsible Disclosure Module
**Estimated**: 1 iteration | **Priority**: MEDIUM

- ⬜ 7.1 Create `/api/disclosure/[id]` GET endpoint — generates disclosure template from audit results
- ⬜ 7.2 Disclosure template includes: finding summary, severity, recommended fix, reporter FID, timestamp
- ⬜ 7.3 Create `DisclosureTemplate.tsx` — renders template with copy button
- ⬜ 7.4 Add Farcaster cast composer deep link (pre-filled with non-sensitive summary)
- ⬜ 7.5 Only show disclosure UI when mode = "research" and findings severity >= MEDIUM
- ⬜ 7.6 Add "Contact Developer" section (manual — Farcaster DM link with FID lookup)

**Done when**: Researcher gets a ready-to-use disclosure template after finding real vulnerabilities.

---

## Group 8: Report Download & Export
**Estimated**: 0.5 iterations | **Priority**: MEDIUM

- ⬜ 8.1 Create `ReportDownload.tsx` — download JSON report + human-readable summary
- ⬜ 8.2 JSON report includes: audit metadata, resolved targets, all findings, visual proof paths, confidence scores
- ⬜ 8.3 Human-readable format: markdown with severity table, finding descriptions, fix recommendations
- ⬜ 8.4 Include attribution: "Audited by AgentxploiTor via Farcaster | Reporter FID: XXXX"

**Done when**: User can download a complete, professional audit report.

---

## Group 9: Integration Testing & Polish
**Estimated**: 1 iteration | **Priority**: HIGH (last gate)

- ⬜ 9.1 End-to-end test: plain name → discovery → contract audit → results (use public open-source miniapp)
- ⬜ 9.2 End-to-end test: GitHub repo URL → full-stack audit → results
- ⬜ 9.3 End-to-end test: contract address (Base) → Slither report → results
- ⬜ 9.4 End-to-end test: Farcaster URL → browser audit → visual proof
- ⬜ 9.5 Verify SSRF protection still blocks private IPs for all new input types
- ⬜ 9.6 Verify rate limiting works per FID
- ⬜ 9.7 Component size audit: ensure all new components <400 lines
- ⬜ 9.8 Consciousness Gate 3 validation (score all four dimensions ≥7.0)
- ⬜ 9.9 Update memory_bank at completion

**Done when**: All four user flows work end-to-end. Consciousness Gate 3 passed. Memory bank updated.

---

## Summary

| Group | Focus | Est. Iterations | Priority |
|-------|-------|----------------|----------|
| 1 | Target Input & Discovery | 2 | CRITICAL |
| 2 | Persona & Mode Selection UI | 1 | HIGH |
| 3 | Extend Audit Request API | 1 | HIGH |
| 4 | Contract Audit Pipeline | 2 | HIGH |
| 5 | Frontend UI Audit Pipeline | 1 | HIGH |
| 6 | Reasoning Stream | 0.5 | MEDIUM |
| 7 | Responsible Disclosure | 1 | MEDIUM |
| 8 | Report Download | 0.5 | MEDIUM |
| 9 | Integration Testing | 1 | HIGH |
| **Total** | | **~10 iterations** | |

**Phase 2** (not in scope here): Docker sandbox, on-chain registry, Farcaster DM notifications, bounty platform integration.
