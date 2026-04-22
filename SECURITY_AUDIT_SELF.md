# Security Audit Report — AgentxploiTor Self-Audit

**Date:** 2026-04-18  
**Auditor:** Buffy (AI Agent) — Orion-OS v2.4  
**Scope:** Full codebase — miniapp (Next.js), Python backend, CI/CD, secrets, auth  
**Method:** Static analysis, pattern scanning, manual code review, git history check

---

## Executive Summary

| Severity | Count | Action Required |
|----------|-------|-----------------|
| P0 CRITICAL | 3 | Fix immediately — blocks deployment |
| P1 HIGH | 4 | Fix before any public launch |
| P2 MEDIUM | 5 | Fix within next iteration |
| P3 LOW | 4 | Track, fix opportunistically |

---

## P0 — CRITICAL (Blocks Deployment)

### P0-1: Farcaster Account Association Points to Wrong Domain
- **File:** `miniapp/src/app/.well-known/farcaster.json/route.ts`
- **Finding:** The `accountAssociation.payload` base64-decodes to `{"domain":"frames-v2-demo-lilac.vercel.app"}` — this is the old Vercel demo domain, NOT `agentxploitor.netlify.app`. The signature was generated for a different domain entirely.
- **Impact:** Farcaster cannot verify your app's ownership. The miniapp will fail Farcaster's domain verification. Users cannot authenticate. **This makes the miniapp non-functional on Farcaster.**
- **Fix:** Generate a new account association for `agentxploitor.netlify.app` using the Farcaster developer tools.

### P0-2: Hardcoded Treasury Address Without Env Var Fallback
- **File:** `miniapp/src/components/wallet/BasePay.tsx` (line 156), `miniapp/src/components/actions/send-token.tsx` (line 9)
- **Finding:** Payment recipient is hardcoded as `0x8342A48694A74044116F330db5050a267b28dD85` with NO environment variable fallback. `WalletActions.tsx` correctly uses `process.env.NEXT_PUBLIC_TREASURY_ADDRESS || fallback`, but `BasePay.tsx` and `send-token.tsx` do not.
- **Impact:** All payments go to a single hardcoded address regardless of configuration. If this address is wrong or needs to change, code must be redeployed. For a security product, hardcoded payment destinations undermine trust.
- **Fix:** Use `process.env.NEXT_PUBLIC_TREASURY_ADDRESS` with the current address as fallback only.

### P0-3: CSP Allows `unsafe-eval` and `unsafe-inline` ⚠️ PARTIALLY FIXED
- **File:** `miniapp/next.config.ts` (lines 24-25)
- **Finding:** Content Security Policy included `script-src 'self' 'unsafe-inline' 'unsafe-eval'`. This effectively negated XSS protection for scripts.
- **Impact:** For a security audit product, having `unsafe-inline` + `unsafe-eval` in your CSP is a trust red flag. Any XSS vulnerability (including via third-party dependencies) can execute arbitrary scripts.
- **Fix Applied:** Removed `unsafe-eval` entirely. Kept `unsafe-inline` with TODO comment — Next.js requires inline scripts for hydration and cannot function without them. **Next step:** migrate to nonce-based CSP via middleware (requires server-side nonce injection per request). `unsafe-eval` removal is safe and immediate.

---

## P1 — HIGH (Fix Before Launch)

### P1-1: SIWE Nonce Uses Math.random() — Insecure
- **File:** `miniapp/src/components/wallet/WalletActions.tsx` (line 177)
- **Finding:** `nonce: Math.random().toString(36).substring(2, 15)` — `Math.random()` is not cryptographically secure. Nonces in SIWE messages must be unpredictable to prevent replay attacks.
- **Impact:** An attacker who can observe nonces can predict future ones, enabling replay attacks on SIWE authentication.
- **Fix:** Use `crypto.randomUUID()` or a server-generated nonce.

### P1-2: Monitoring API Has No Authentication
- **File:** `miniapp/src/app/api/monitoring/route.ts`
- **Finding:** POST/DELETE endpoints for contract monitoring have zero authentication. Anyone can add/remove watched contracts and read monitoring events.
- **Impact:** Arbitrary contract monitoring creation (resource exhaustion), data exfiltration of monitored contracts, deletion of legitimate monitors.
- **Fix:** Add Farcaster auth verification (same pattern as `audit/request/route.ts`).

### P1-3: Console.log Statements Leak Internal State in Production
- **Files:** `BasePay.tsx` (line 110), `WalletActions.tsx`, `audit/request/route.ts` (line 163), `auth/route.ts` (line 72)
- **Finding:** `console.log('pay result', payResult)`, `console.log('payload', payload)`, `console.log('[AuditRequest] Created:', ...)` — these log payment results, auth payloads, and audit details to the browser console and server logs.
- **Impact:** Payment transaction details and auth tokens visible in browser DevTools. Server logs may expose FIDs and audit details. For a security product, this is a trust issue.
- **Fix:** Replace with structured logging that respects environment (dev only). Strip sensitive fields.

### P1-4: Rate Limiter Uses In-Memory Map — Non-Functional in Serverless
- **File:** `miniapp/src/middleware.ts`
- **Finding:** Rate limiting uses `new Map<string, { count: number; resetTime: number }>()` in module scope. On Vercel/Netlify serverless, each cold start gets a fresh empty Map. Rate limiting is effectively disabled.
- **Impact:** All API endpoints are unprotected against brute-force or DDoS attacks.
- **Fix:** Use Vercel KV, Upstash Redis, or an external rate limiting service. The project already has `KV_URL` in `.env.example` — wire it up.

---

## P2 — MEDIUM (Fix Within Next Iteration)

### P2-1: `frame-ancestors *` Allows Clickjacking — ✅ FIXED
- **File:** `miniapp/next.config.ts`
- **Finding:** CSP included `frame-ancestors *`, allowing any website to embed the miniapp in an iframe.
- **Impact:** Clickjacking attacks — a malicious site could overlay invisible frames to trick users into authorizing payments or signing messages.
- **Fix Applied:** Changed to `frame-ancestors https://warpcast.com https://farcaster.xyz https://*.vercel.app https://*.netlify.app` — only Farcaster domains and hosting environments can iframe.

### P2-2: `connect-src` Missing QuickNode Domains — ✅ FIXED
- **File:** `miniapp/next.config.ts`
- **Finding:** CSP `connect-src` only included `mainnet.base.org` and `api.farcaster.xyz`. QuickNode RPC calls from the browser would be blocked by CSP.
- **Impact:** On-chain state analysis (proxy detection, admin reads, tracing) fails silently in production if initiated from client-side code.
- **Fix Applied:** Added `https://*.quiknode.pro https://api.openai.com` to `connect-src`.

### P2-3: Broad `except Exception` Swallows Errors in Python Backend
- **Files:** `worker.py`, `saga.py`, `event_sourcing.py`, `cqrs.py`, `circuit_breaker.py`, `e2b_runner.py` (~50 instances)
- **Finding:** Widespread `except Exception as e:` blocks that log and continue, often discarding the error context. Many catch `Exception` without re-raising or alerting.
- **Impact:** Production failures are silently absorbed. Monitoring shows green while actual errors accumulate.
- **Fix:** Catch specific exceptions. Add structured alerting for unexpected errors. At minimum, increment a failure metric.

### P2-4: Audit Request Body Parsed Without Schema Validation
- **File:** `miniapp/src/app/api/audit/request/route.ts` (line 67)
- **Finding:** `const body = await request.json()` is destructured without Zod/schema validation. Any field can be any type.
- **Impact:** Malformed requests could inject unexpected values into job creation. The `priority` field, for example, is not validated as an enum.
- **Fix:** Define a Zod schema for the request body and validate before destructuring.

### P2-5: `dangerouslySetInnerHTML` in Agent-Browser Docs
- **File:** `agent-browser/docs/src/components/code-block.tsx` (line 19)
- **Finding:** Uses `dangerouslySetInnerHTML={{ __html: html }}` for syntax highlighting.
- **Impact:** If the HTML content is ever user-controlled or from an untrusted source, this is an XSS vector. Currently low risk since it's for code highlighting, but worth noting for a security product.
- **Fix:** Use a React-native syntax highlighter (e.g., `react-syntax-highlighter`) or ensure HTML is always sanitized.

---

## P3 — LOW (Track, Fix Opportunistically)

### P3-1: Hardcoded USDC Contract Address
- **File:** `send-token.tsx` (line 20), `swap-token.tsx` (line 13)
- **Finding:** `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (Base USDC) is hardcoded.
- **Impact:** If USDC contract changes or a different token is needed, code must change.
- **Fix:** Move to env var or chain-specific token registry.

### P3-2: Test Files Use `Math.random()` for IDs
- **Files:** `e2e-audit-flows.test.ts`, `test_worker.ts`
- **Finding:** `id: 'job_${Date.now()}_${Math.random()}'` — non-deterministic test IDs.
- **Impact:** Flaky tests, harder to reproduce failures.
- **Fix:** Use deterministic UUIDs or counters in tests.

### P3-3: Webhook Test Uses `"mysecret"` as Secret
- **File:** `src/integrations/webhooks.py` (line 103)
- **Finding:** Test fixture uses `secret="mysecret"`.
- **Impact:** Low — it's in test code only. But bad practice for a security product.
- **Fix:** Use a realistic-looking secret in tests.

### P3-4: Placeholder `0x` Values in .env.example
- **File:** `.env.example` (lines 64-65)
- **Finding:** `NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS=0x` and `NEXT_PUBLIC_TREASURY_ADDRESS=0x` — `0x` is not a valid Ethereum address.
- **Impact:** If deployed without overriding, payment addresses default to invalid `0x`, which may cause silent failures or funds sent to null address.
- **Fix:** Replace with descriptive placeholder like `0x0000000000000000000000000000000000000000` and add a startup validation check.

---

## Positive Findings (What's Done Right)

1. **Auth on audit endpoints** — `/api/audit/request` correctly verifies Farcaster JWT before creating jobs
2. **No real secrets in git history** — QuickNode keys were never committed; `.env.example` uses placeholders
3. **Security headers present** — X-Content-Type-Options, Referrer-Policy, Permissions-Policy all set
4. **Input validation exists** — `validateTargetUrl()` used on URL targets, payment verification before job creation
5. **SQL injection protection** — Python backend uses parameterized queries (`$1`, `$2` style)
6. **Semantic safety layer** — `semantic_safety.py` actively blocks dangerous patterns (eval, __import__, os.system)
7. **No `.env` files committed** — `.env`, `.env.local`, `.env.production` not present in repository

---

## Recommended Fix Priority

1. **P0-1** (Farcaster domain) — Must fix before any Farcaster deployment. Requires human action (generate new association).
2. **P0-2** (Hardcoded address) — Quick code fix.
3. **P0-3** (CSP unsafe-*) — Quick code fix but may need testing with dependencies.
4. **P1-1** (Math.random nonce) — One-line fix.
5. **P1-2** (Monitoring auth) — Moderate fix.
6. **P1-4** (Rate limiter) — Moderate fix (wire up KV).
7. **P1-3** (Console.log) — Quick fix but many instances.

---

*This audit was performed by the same AI agent that powers AgentxploiTor's security analysis. We eat our own cooking.*
