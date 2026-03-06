# AgentxploiTor Hardening & Integration - Requirements

## Objective
Transition AgentxploiTor from demo-grade to production-leaning by replacing mock logic with real audit workflows, integrating miniapp requests with the agent pipeline, and adding security hardening across APIs and execution.

## Functional Requirements
### Agent Core (Python)
1. Support real vulnerability scanning for Solana and EVM targets.
2. Generate exploit strategies with safety constraints and structured outputs.
3. Capture and persist visual proof artifacts (before/after screenshots, diffs).
4. Produce structured JSON reports with remediation guidance.
5. Allow configuration of tool paths and output directories via environment variables.

### Miniapp Backend
6. Validate audit requests (schema validation) and enforce rate limits.
7. Persist audit requests and results (KV or database).
8. Queue and process audit jobs, tracking status transitions.
9. Verify audit payment onchain (BNKR or configured ERC-20).
10. Expose status and results endpoints for the miniapp UI.

### Miniapp Frontend
11. Replace mock data with live results from API.
12. Display proof artifacts with download links.
13. Show real-time status/progress states in the UI.
14. Provide audit history per user or wallet.

### Security & Compliance
15. Require auth for privileged endpoints (job triggers/admin ops).
16. Enforce target allowlists or sandboxed scanning.
17. Sanitize and limit all user input.
18. Remove build artifacts from version control and add `.next` to ignore.

## Non-Functional Requirements
- Performance: audit status endpoints should return within 500ms.
- Reliability: job state must be persisted and recoverable after restarts.
- Portability: no hard-coded paths; config via `.env`.
- Observability: log key events with redaction of sensitive data.

## Constraints
- Maintain current UI structure and routes.
- Preserve existing visual-verification narrative and UX.
- Avoid adding heavyweight infra beyond a simple queue + KV.

## Success Metrics
- End-to-end request → audit → results with real findings.
- Verified payment for each audit request.
- Visual proof artifacts displayed in results page.
- No hard-coded paths or committed build artifacts.
