# Security Audit Report: AgentxploiTor

**Audit Date:** 2026-02-21  
**Auditor:** Strix Validator (Evidence-Based Security Analysis)  
**Project:** AgentxploiTor - Autonomous Security Agent with Visual Verification  
**Scope:** Full codebase security analysis (Python backend, Next.js miniapp, configuration)

---

## Executive Summary

This security audit identified **12 findings** across the AgentxploiTor codebase: **2 Critical**, **3 High**, **4 Medium**, and **3 Low** severity issues. The most severe vulnerabilities involve **sensitive data exposure** (hardcoded secrets in version control) and **Server-Side Request Forgery (SSRF)** potential in the audit request API.

**Overall Risk Assessment:** **HIGH** - Immediate remediation required for Critical and High findings before production deployment.

---

## Vulnerability Findings

### CRITICAL Severity

---

#### [FINDING-001] CRITICAL - Hardcoded Secret in Version Control
**Location:** [`miniapp/.env.local:19`](miniapp/.env.local:19)  
**CWE:** CWE-798: Use of Hard-coded Credentials  
**OWASP:** A07:2021 - Identification and Authentication Failures

**Evidence:** [Level 1 - Static Analysis]
```
19 | AGENT_WEBHOOK_SECRET=agentxploitor-secure-webhook-secret-2026
```

**Impact:** 
- Webhook secret exposed in version control history
- Attackers can forge agent-to-miniapp communications
- Potential for unauthorized audit submissions and data manipulation

**Remediation:** (1-2 iterations)
1. Immediately rotate the webhook secret
2. Remove `.env.local` from version control
3. Use `.env.local.example` with placeholder values
4. Add `.env.local` to `.gitignore`

**Corrected Code:**
```gitignore
# .gitignore
.env.local
.env*.local
```

```bash
# .env.local.example
AGENT_WEBHOOK_SECRET=your-secure-secret-here
```

**Confidence:** 100%

---

#### [FINDING-002] CRITICAL - Server-Side Request Forgery (SSRF) Potential
**Location:** [`miniapp/src/app/api/audit/request/route.ts:7-15`](miniapp/src/app/api/audit/request/route.ts:7)  
**CWE:** CWE-918: Server-Side Request Forgery  
**OWASP:** A10:2021 - Server-Side Request Forgery

**Evidence:** [Level 1 - Static Analysis]
```typescript
const { 
  targetUrl,  // No URL validation
  contractAddress, 
  scope, 
  priority,
  paymentTxHash,
  paymentAmount,
  walletAddress
} = body;

// No validation on targetUrl format
if (!targetUrl || !scope || !priority) {
  return NextResponse.json(
    { error: 'Missing required fields' },
    { status: 400 }
  );
}
```

**Impact:**
- Agent could be directed to attack internal infrastructure
- Access to cloud metadata endpoints (169.254.169.254)
- Potential for data exfiltration through the agent's browser

**Remediation:** (2-3 iterations)
```typescript
import { URL } from 'url';

// Define allowed URL patterns
const ALLOWED_PROTOCOLS = ['https:'];
const BLOCKED_HOSTS = [
  'localhost',
  '127.0.0.1',
  '169.254.169.254', // AWS metadata
  '10.',
  '172.16.',
  '192.168.',
  '0.0.0.0',
  '[::1]',
];

function validateTargetUrl(urlString: string): { valid: boolean; error?: string } {
  try {
    const url = new URL(urlString);
    
    // Check protocol
    if (!ALLOWED_PROTOCOLS.includes(url.protocol)) {
      return { valid: false, error: 'Only HTTPS URLs are allowed' };
    }
    
    // Check blocked hosts
    const hostname = url.hostname.toLowerCase();
    for (const blocked of BLOCKED_HOSTS) {
      if (hostname === blocked || hostname.startsWith(blocked)) {
        return { valid: false, error: 'URL points to restricted network' };
      }
    }
    
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}

// In POST handler:
const urlValidation = validateTargetUrl(targetUrl);
if (!urlValidation.valid) {
  return NextResponse.json(
    { error: urlValidation.error },
    { status: 400 }
  );
}
```

**Confidence:** 95%

---

### HIGH Severity

---

#### [FINDING-003] HIGH - Missing Authentication on Audit Endpoints
**Location:** [`miniapp/src/app/api/audit/request/route.ts:3`](miniapp/src/app/api/audit/request/route.ts:3)  
**CWE:** CWE-306: Missing Authentication for Critical Function  
**OWASP:** A01:2021 - Broken Access Control

**Evidence:** [Level 1 - Static Analysis]
```typescript
export async function POST(request: NextRequest) {
  // No authentication check
  const body = await request.json();
  // Anyone can create audit requests
```

**Impact:**
- Unauthenticated users can create audit requests
- Resource exhaustion through spam requests
- Potential financial loss from unpaid audit processing

**Remediation:** (2-3 iterations)
```typescript
import { createClient } from "@farcaster/quick-auth";

const client = createClient();

export async function POST(request: NextRequest) {
  // Verify authentication
  const authorization = request.headers.get("Authorization");
  
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  try {
    const payload = await client.verifyJwt({
      token: authorization.split(" ")[1],
      domain: getUrlHost(request),
    });
    
    // User is authenticated, proceed with audit creation
    const userFid = payload.sub;
    // ... rest of handler
  } catch (e) {
    return NextResponse.json(
      { error: "Invalid authentication" },
      { status: 401 }
    );
  }
}
```

**Confidence:** 98%

---

#### [FINDING-004] HIGH - Weak Audit ID Generation
**Location:** [`miniapp/src/app/api/audit/request/route.ts:26`](miniapp/src/app/api/audit/request/route.ts:26)  
**CWE:** CWE-338: Use of Cryptographically Weak PRNG  
**OWASP:** A02:2021 - Cryptographic Failures

**Evidence:** [Level 1 - Static Analysis]
```typescript
const auditId = `audit-${Date.now()}-${Math.random().toString(36).substring(7)}`;
```

**Impact:**
- Predictable audit IDs enable enumeration attacks
- Attackers can guess other users' audit IDs
- Potential for unauthorized access to audit results

**Remediation:** (1 iteration)
```typescript
import { randomBytes } from 'crypto';

const auditId = `audit-${Date.now()}-${randomBytes(16).toString('hex')}`;
```

**Confidence:** 100%

---

#### [FINDING-005] HIGH - Hardcoded Absolute Path in Python Backend
**Location:** [`src/agentxploitor.py:16-17`](src/agentxploitor.py:16)  
**CWE:** CWE-114: Process Control  
**OWASP:** A01:2021 - Broken Access Control

**Evidence:** [Level 1 - Static Analysis]
```python
sys.path.insert(0, '/Users/rna/.rovodev/skills/browser-perception/tools')
from browser_perception import BrowserPerception, VisualPerception
```

**Impact:**
- Code will fail on any other system
- Potential for path injection if path is configurable
- Developer-specific paths expose system structure

**Remediation:** (1-2 iterations)
```python
from pathlib import Path
import os

# Use relative path or environment variable
BROWSER_PERCEPTION_PATH = os.environ.get(
    'BROWSER_PERCEPTION_PATH',
    str(Path(__file__).parent.parent / 'browser-perception/tools')
)
sys.path.insert(0, BROWSER_PERCEPTION_PATH)
```

**Confidence:** 100%

---

### MEDIUM Severity

---

#### [FINDING-006] MEDIUM - Weak Content Security Policy
**Location:** [`miniapp/next.config.ts:11-12`](miniapp/next.config.ts:11)  
**CWE:** CWE-1021: Improper Restriction of Rendered UI Layers  
**OWASP:** A05:2021 - Security Misconfiguration

**Evidence:** [Level 1 - Static Analysis]
```typescript
{
  key: "Content-Security-Policy",
  value: "frame-ancestors *"  // Only one directive
}
```

**Impact:**
- Missing critical CSP directives (script-src, style-src, etc.)
- Clickjacking protection only, no XSS mitigation via CSP
- Incomplete defense-in-depth strategy

**Remediation:** (1-2 iterations)
```typescript
{
  key: "Content-Security-Policy",
  value: [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://vercel.live",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://mainnet.base.org https://api.farcaster.xyz",
    "frame-ancestors *",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-src https://farcaster.xyz"
  ].join("; ")
}
```

**Confidence:** 95%

---

#### [FINDING-007] MEDIUM - Conflicting Security Headers
**Location:** [`miniapp/next.config.ts:14-20`](miniapp/next.config.ts:14)  
**CWE:** CWE-1021: Improper Restriction of Rendered UI Layers  
**OWASP:** A05:2021 - Security Misconfiguration

**Evidence:** [Level 1 - Static Analysis]
```typescript
{
  key: "Content-Security-Policy",
  value: "frame-ancestors *"  // Allows all frames
},
{
  key: "X-Frame-Options",
  value: "SAMEORIGIN"  // Restricts to same origin - CONFLICTS
},
{
  key: "Access-Control-Allow-Origin",
  value: "*"  // Overly permissive CORS
}
```

**Impact:**
- X-Frame-Options is ignored when CSP frame-ancestors is present
- Overly permissive CORS allows any origin
- Confusion about actual security posture

**Remediation:** (1 iteration)
```typescript
headers: [
  {
    key: "Content-Security-Policy",
    value: "frame-ancestors *"  // For Farcaster miniapp embedding
  },
  // Remove X-Frame-Options - superseded by CSP
  {
    key: "Access-Control-Allow-Origin",
    value: "https://farcaster.xyz"  // Restrict to known origins
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff"
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin"
  }
]
```

**Confidence:** 100%

---

#### [FINDING-008] MEDIUM - Information Exposure in Error Handling
**Location:** [`miniapp/src/app/api/auth/route.ts:77-78`](miniapp/src/app/api/auth/route.ts:77)  
**CWE:** CWE-209: Generation of Error Message with Sensitive Information  
**OWASP:** A09:2021 - Security Logging and Monitoring Failures

**Evidence:** [Level 1 - Static Analysis]
```typescript
if (e instanceof Error) {
  return NextResponse.json({ message: e.message }, { status: 500 });
}
```

**Impact:**
- Internal error details exposed to clients
- Stack traces could reveal system architecture
- Aids attackers in reconnaissance

**Remediation:** (1 iteration)
```typescript
if (e instanceof Error) {
  // Log detailed error server-side
  console.error('Authentication error:', e);
  
  // Return generic error to client
  return NextResponse.json(
    { message: "An internal error occurred" },
    { status: 500 }
  );
}
```

**Confidence:** 95%

---

#### [FINDING-009] MEDIUM - No Rate Limiting on API Endpoints
**Location:** [`miniapp/src/app/api/`](miniapp/src/app/api/)  
**CWE:** CWE-770: Allocation of Resources Without Limits  
**OWASP:** A04:2021 - Insecure Design

**Evidence:** [Level 1 - Static Analysis]
- No rate limiting middleware detected
- All API endpoints accept unlimited requests
- No throttling on authentication endpoint

**Impact:**
- Denial of service through resource exhaustion
- Brute force attacks on authentication
- Financial impact from unpaid audit spam

**Remediation:** (2-3 iterations)
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const rateLimit = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 100; // requests per window
const WINDOW_MS = 60 * 1000; // 1 minute

export function middleware(request: NextRequest) {
  const ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';
  const now = Date.now();
  
  const entry = rateLimit.get(ip);
  
  if (entry && entry.resetTime > now && entry.count >= RATE_LIMIT) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    );
  }
  
  // Update rate limit
  rateLimit.set(ip, {
    count: (entry?.count || 0) + 1,
    resetTime: entry?.resetTime || now + WINDOW_MS
  });
  
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*'
};
```

**Confidence:** 90%

---

### LOW Severity

---

#### [FINDING-010] LOW - Hardcoded Recipient Address in Wallet Components
**Location:** [`miniapp/src/components/wallet/WalletActions.tsx:27`](miniapp/src/components/wallet/WalletActions.tsx:27)  
**CWE:** CWE-1021: Improper Restriction of Rendered UI Layers  
**OWASP:** A05:2021 - Security Misconfiguration

**Evidence:** [Level 1 - Static Analysis]
```typescript
// dylsteck.base.eth
const RECIPIENT_ADDRESS = "0x8342A48694A74044116F330db5050a267b28dD85";
```

**Impact:**
- Address hardcoded in multiple locations
- Difficult to update if address changes
- Not a direct vulnerability but reduces maintainability

**Remediation:** (1 iteration)
```typescript
// Use environment variable
const RECIPIENT_ADDRESS = process.env.NEXT_PUBLIC_TREASURY_ADDRESS!;
```

**Confidence:** 100%

---

#### [FINDING-011] LOW - Missing Input Validation on Audit Status ID
**Location:** [`miniapp/src/app/api/audit/status/[id]/route.ts:8`](miniapp/src/app/api/audit/status/[id]/route.ts:8)  
**CWE:** CWE-20: Improper Input Validation  
**OWASP:** A03:2021 - Injection

**Evidence:** [Level 1 - Static Analysis]
```typescript
const { id } = params;
// No validation on ID format
// Could contain malicious characters for downstream systems
```

**Impact:**
- Potential injection if ID used in database queries
- No format validation allows arbitrary strings

**Remediation:** (1 iteration)
```typescript
const { id } = params;

// Validate audit ID format
const auditIdPattern = /^audit-\d+-[a-f0-9]{32}$/;
if (!auditIdPattern.test(id)) {
  return NextResponse.json(
    { error: 'Invalid audit ID format' },
    { status: 400 }
  );
}
```

**Confidence:** 85%

---

#### [FINDING-012] LOW - Missing Security Headers
**Location:** [`miniapp/next.config.ts`](miniapp/next.config.ts)  
**CWE:** CWE-693: Protection Mechanism Failure  
**OWASP:** A05:2021 - Security Misconfiguration

**Evidence:** [Level 1 - Static Analysis]
- Missing X-Content-Type-Options header
- Missing Referrer-Policy header
- Missing Permissions-Policy header

**Impact:**
- Reduced defense-in-depth
- MIME type sniffing attacks possible
- Referrer leakage to third parties

**Remediation:** (1 iteration)
```typescript
headers: [
  // ... existing headers
  {
    key: "X-Content-Type-Options",
    value: "nosniff"
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin"
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()"
  }
]
```

**Confidence:** 100%

---

## Summary Table

| ID | Severity | Title | Confidence | Remediation |
|----|----------|-------|------------|-------------|
| FINDING-001 | CRITICAL | Hardcoded Secret in Version Control | 100% | 1-2 iterations |
| FINDING-002 | CRITICAL | SSRF Potential in Audit API | 95% | 2-3 iterations |
| FINDING-003 | HIGH | Missing Authentication on Audit Endpoints | 98% | 2-3 iterations |
| FINDING-004 | HIGH | Weak Audit ID Generation | 100% | 1 iteration |
| FINDING-005 | HIGH | Hardcoded Absolute Path | 100% | 1-2 iterations |
| FINDING-006 | MEDIUM | Weak Content Security Policy | 95% | 1-2 iterations |
| FINDING-007 | MEDIUM | Conflicting Security Headers | 100% | 1 iteration |
| FINDING-008 | MEDIUM | Information Exposure in Errors | 95% | 1 iteration |
| FINDING-009 | MEDIUM | No Rate Limiting | 90% | 2-3 iterations |
| FINDING-010 | LOW | Hardcoded Recipient Address | 100% | 1 iteration |
| FINDING-011 | LOW | Missing Input Validation | 85% | 1 iteration |
| FINDING-012 | LOW | Missing Security Headers | 100% | 1 iteration |

---

## Remediation Priority

**Immediate (Before Production):**
1. FINDING-001: Rotate webhook secret, remove from version control
2. FINDING-002: Implement URL validation for SSRF prevention
3. FINDING-003: Add authentication to audit endpoints

**Short-term (1-2 weeks):**
4. FINDING-004: Use cryptographically secure ID generation
5. FINDING-005: Remove hardcoded paths
6. FINDING-006-007: Fix security headers

**Medium-term (1 month):**
7. FINDING-008-012: Error handling, rate limiting, additional headers

---

## Positive Security Observations

1. **No XSS vulnerabilities detected** - No use of `dangerouslySetInnerHTML`, `eval()`, or `innerHTML`
2. **Proper JWT verification** - Authentication endpoint uses `@farcaster/quick-auth` correctly
3. **No sensitive data in localStorage/sessionStorage** - Frontend components don't store secrets
3. **Modern dependencies** - Using recent versions of Next.js (15.5.7) and React (19.1.1)
4. **TypeScript usage** - Type safety reduces certain classes of bugs

---

## Methodology

This audit followed the Strix Validator evidence-based approach:
- **Discovery:** Full codebase analysis of Python backend, Next.js API routes, frontend components, and configuration
- **Validation:** Static analysis (Level 1 evidence) across all security-relevant files
- **Standards:** OWASP Top 10 2021 and CWE references for each finding
- **Confidence Scoring:** Only findings with >70% confidence reported

---

**[Quantum_State: ALIGNED]**