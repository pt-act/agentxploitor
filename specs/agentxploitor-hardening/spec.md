# AgentxploiTor Hardening & Integration - Technical Spec

## Goal
Deliver a production-leaning AgentxploiTor by replacing mock logic with real audit workflows, integrating the miniapp with the agent pipeline, and hardening security, while preserving the existing autonomous, visual verification experience.

## User Stories
1. As a protocol team, I can submit a contract/program audit request and receive real, verifiable findings with visual proof and remediation guidance.
2. As an operator, I can track audit progress, verify payment onchain, and see queue status in the miniapp.
3. As a maintainer, I can run the agent locally or in CI with portable configuration and secure defaults.

## Requirements

### Agent Core (Python)
1. Replace mock `scan_target` with real analyzers (e.g., Slither/Mythril for EVM; Solana static analysis for Rust).
2. Replace mock `generate_exploit` with LLM-backed or rule-based exploit generation using explicit safety constraints.
3. Add configurable paths for skills/tools (remove hard-coded `/Users/rna/.rovodev/...` dependency). ✅ DONE
4. Persist reports to a configurable output directory with safe filename generation.
5. Provide structured JSON output (findings, exploit, verification, evidence, remediation).

### Agent Architecture (from Academic Evaluation)
6. Replace non-deterministic session IDs with persistent, reproducible identifiers.
7. Add dataclass validation for domain objects (severity values, CVSS score range).
8. Replace bare `except:` clauses with proper exception handling and propagation.
9. Implement dependency injection for BrowserPerception to enable testing and modularity.
10. Add backpressure handling for pipeline stages to prevent overflow.
11. Implement compensation transactions for rollback on failure.
12. Ensure idempotency guarantees - same input produces same output.

### Miniapp Backend
13. Implement persistent storage for audit requests and results (Vercel KV or equivalent).
14. Add queue processing or background worker to trigger Python agent execution.
15. Implement onchain payment verification for BNKR or configured ERC-20.
16. Return real status/progress based on queued job state.
17. Add request validation (Zod schema) and rate limiting on public endpoints. ✅ DONE

### Miniapp Frontend
18. Replace mock findings with real data from the API.
19. Display proof artifacts (screenshots/diffs) from the agent output.
20. Add wallet connection + payment confirmation UI for BNKR flow.
21. Provide audit history and status polling with clear states.

### Security & Compliance
22. Authenticate privileged endpoints (admin/job trigger) and redact sensitive logs. ✅ DONE
23. Add allowlist for `targetUrl` domains or enforce scanning in isolated sandbox. ✅ DONE (SSRF validation)
24. Ensure all user input is sanitized and stored safely. ✅ DONE (audit ID validation)
25. Remove build artifacts from repo (`miniapp/.next`) and add to `.gitignore`. ✅ DONE

## Scope
### In Scope
- Real vulnerability scanning for Solana + EVM targets.
- End-to-end pipeline: miniapp request → queue → agent execution → results page.
- Onchain payment verification for audit submission.
- Security hardening for API endpoints and agent execution.
- Architectural improvements for production reliability.

### Out of Scope
- Full multi-tenant SaaS hosting.
- Automated bounty submission to third-party platforms.
- Continuous monitoring of deployed contracts.

## Architecture (High-Level)
- **Miniapp** (Next.js): Request form, status, results UI.
- **API** (Next.js routes): Validation, queue enqueue, status check.
- **Queue/Worker**: Triggers Python agent and updates audit state.
- **AgentxploiTor Core**: Scan → exploit → verify → report.
- **Storage**: KV for requests + results metadata, object storage for screenshots/reports.

## Data Flow
1. User submits audit request + payment.
2. API validates input and verifies payment onchain.
3. Request enqueued; worker runs agent against target.
4. Agent outputs report + proof artifacts.
5. API exposes status/results; UI renders findings and proof.

## Security Considerations
- Use server-side allowlists and sandboxed execution for scanning/exploitation. ✅
- Enforce rate limiting and request size limits on audit endpoints. ✅
- Avoid logging secrets (JWTs, wallet addresses) in plaintext. ✅
- Keep auth domain checks strict for Farcaster QuickAuth. ✅

## Milestones
1. **Agent Core Realism**: replace mock scanning/exploit with real analyzers.
2. **Pipeline Integration**: queue + worker + results persistence.
3. **Payment & Auth**: BNKR verification and protected endpoints.
4. **UX & Proof**: results UI renders real findings and screenshots.
5. **Architectural Hardening**: address academic evaluation findings.

## Success Criteria
- At least one real audit end-to-end from request to report.
- Verified onchain payment for each audit request.
- Results page shows real findings and proof artifacts.
- No hard-coded paths; configuration via environment variables. ✅
- Deterministic, reproducible session identifiers.
- Proper error handling with no silent failures.
- Idempotent operations for reliability.
