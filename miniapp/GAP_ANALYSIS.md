# AgentxploiTor MiniApp - Comprehensive Gap Analysis

**Date**: 2025-01-20  
**Scope**: Complete analysis of `/src/` directory - every API route, component, lib file, middleware  
**Purpose**: Identify all stubs, mocks, TODOs, hardcoded values, and missing implementations

---

## Executive Summary

The miniapp is **60% structurally complete** with good scaffolding but **40% functionally incomplete**. Key findings:

- **Real implementations**: Authentication flow, payment verification, storage layer, security validation
- **Stubbed/Mocked**: Dashboard data, reasoning stream, audit execution, report generation
- **Missing integrations**: HexStrike agent connection, actual audit execution, WebSocket server, real reasoning data
- **Hardcoded values**: Mock audits, mock metrics, demo data, placeholder addresses

**Critical blockers**: No actual connection to HexStrike agents, no WebSocket server, reasoning stream is polling mock data only.

---

## FILE-BY-FILE ANALYSIS

### 1. MIDDLEWARE: `middleware.ts` ✅ REAL
**Status**: Functional, complete  
**Purpose**: Rate limiting for API endpoints

**What it does**:
- Extracts client IP from headers (x-forwarded-for, x-real-ip)
- Enforces rate limit: 100 requests per 60 seconds
- Tracks per-IP: count + resetTime in memory Map
- Returns 429 if exceeded, passes request through if OK

**Stubbed/Mocked**: None - fully functional  
**Hardcoded values**:
- `RATE_LIMIT = 100` (requests per window)
- `WINDOW_MS = 60 * 1000` (1 minute window)

**Missing**: None - complete

---

### 2. API ROUTE: `app/api/auth/route.ts` ✅ REAL
**Status**: Functional, complete  
**Purpose**: Farcaster JWT verification for quick-auth

**What it does**:
- GET endpoint only
- Validates Bearer token from Authorization header
- Verifies JWT using Farcaster quickAuth client
- Returns `{ success: true, user: { fid, issuedAt, expiresAt } }`
- Handles domain resolution (Origin header → Host header → env fallback)

**Stubbed/Mocked**: None - real JWT verification with Farcaster SDK  
**Hardcoded values**:
- Domain resolution logic (tries Origin, Host, env vars)
- Uses `process.env.VERCEL_ENV` for production check

**Missing**: None - complete

---

### 3. API ROUTE: `app/api/audit/request/route.ts` ⚠️ MOSTLY REAL
**Status**: Functional but incomplete integration  
**Purpose**: Create audit requests, optionally verify payment

**What it does (POST)**:
- Validates auth (Bearer token required)
- Accepts: targetUrl, contractAddress, scope, priority, paymentTxHash, walletAddress
- Validates target URL (HTTPS only, blocks private IPs)
- **REAL**: verifyBNKRPayment() if paymentTxHash provided
- Creates job with status: `pending_payment` or `payment_verified`
- Enqueues job if payment verified
- Returns: auditId, status, queuePosition, estimatedStart, paymentRequired, treasury address, min amount

**What it does (GET)**:
- Lists jobs by wallet address (optional filter)
- Returns: first 20 jobs with id, targetUrl, status, createdAt, findingsCount

**Stubbed/Mocked**:
- Job storage is in-memory only (not persistent)
- Queue is in-memory array (lost on restart)
- No actual audit execution triggered

**Real integrations**:
- Payment verification with viem (Base network RPC)
- URL validation with regex
- Audit ID generation with crypto randomBytes

**Hardcoded values**:
- None (all config-driven via payment.ts)

**Missing**:
- ❌ No connection to HexStrike agent to trigger actual audit
- ❌ No queue worker to process enqueued jobs
- ❌ No webhook/notification system
- ❌ No persistent storage (will lose data on restart)

---

### 4. API ROUTE: `app/api/audit/status/[id]/route.ts` ⚠️ PARTIALLY REAL
**Status**: Functional but reads from incomplete backend

**What it does**:
- GET endpoint for audit status
- Validates audit ID format (regex: `audit-\d+-[a-f0-9]{32}`)
- Retrieves job from storage
- Returns: id, targetUrl, status, queuePosition (hardcoded 1 if queued), progress (map-based), findings, paymentVerified, error, createdAt, updatedAt, completedAt

**Stubbed/Mocked**:
- Progress calculation is hardcoded map (not dynamic):
  ```
  pending_payment: 0, payment_verified: 10, queued: 15,
  in_progress: 50, completed: 100, failed: 100, cancelled: 100
  ```
- queuePosition always returns 1 if queued (not actual position)
- findings come from job.findingsCount (populated by... nothing currently)

**Real parts**: 
- Audit ID validation
- Job retrieval from storage

**Missing**:
- ❌ No actual queue position calculation
- ❌ No real progress tracking (depends on HexStrike)
- ❌ No findings generation (depends on audit execution)

---

### 5. API ROUTE: `app/api/audit/results/[id]/route.ts` ⚠️ PARTIALLY REAL
**Status**: Functional but depends on missing audit execution

**What it does**:
- GET endpoint for completed audit results
- Validates audit ID format
- Checks if job status === 'completed', rejects if not
- Attempts to retrieve report from reportStore
- Falls back to job.findingsCount if report not found
- Returns: id, jobId, targetUrl, summary, vulnerabilities, exploits, verifications, evaluation, createdAt, proofUrls

**Stubbed/Mocked**:
- Report generation is completely missing
- Falls back to showing findingsCount as summary with message: "Report being processed"
- proofUrls extraction assumes report.verifications exist (they don't)

**Real parts**:
- Status checking
- Report retrieval from storage

**Missing**:
- ❌ No report generation pipeline
- ❌ No vulnerability analysis
- ❌ No exploit generation
- ❌ No verification system
- ❌ No visual proof capture

---

### 6. API ROUTE: `app/api/dashboard/audits/route.ts` ❌ COMPLETELY MOCKED
**Status**: Stub only

**What it does**:
- GET endpoint
- Returns hardcoded mockAudits array with 3 sample audits:
  ```
  audit-001: completed, 2 critical, 5 high, 8 medium, 3 low
  audit-002: in_progress, 1 critical, 2 high
  audit-003: queued, 0 findings
  ```
- Filters by status query param
- Limits by limit query param (default 10)

**Stubbed/Mocked**: 100% - all data is hardcoded  
**Hardcoded values**:
- Three fake audit objects with timestamps
- Mock finding counts
- Mock status values

**Missing**:
- ❌ No real data from jobStore
- ❌ Not connected to actual audits

---

### 7. API ROUTE: `app/api/dashboard/stats/route.ts` ❌ COMPLETELY MOCKED
**Status**: Stub only

**What it does**:
- GET endpoint
- Returns hardcoded stats object:
  ```json
  {
    "activeAudits": 2,
    "completedToday": 5,
    "criticalFindings": 3,
    "totalFindings": 27
  }
  ```

**Stubbed/Mocked**: 100% - all values hardcoded  
**Missing**:
- ❌ No aggregation of actual job data
- ❌ Not connected to real audits

---

### 8. API ROUTE: `app/api/metrics/route.ts` ❌ COMPLETELY MOCKED
**Status**: Stub only

**What it does**:
- GET endpoint supporting `?format=prometheus` (default) or `?format=json`
- Prometheus format: returns 52 lines of hardcoded Prometheus metrics text
- JSON format: returns hardcoded metrics object with:
  - jobs: completed: 42, failed: 3, total: 45
  - queue: normal: 5, high: 2, low: 8, processing: 3
  - analyzers: slither (35 success, 2 error), mythril (28 success)
  - audits: completed: 15, avgCost: 0.45
  - workers: active: 4
  - circuitBreakers: slither, mythril, llm (all closed)
  - timestamp: now

**Stubbed/Mocked**: 100% - all hardcoded mock data  
**Hardcoded values**:
- 52 lines of Prometheus text
- Version: 2.0.0
- Workspace ID: ws-001
- Analyzer success/fail counts
- Circuit breaker states

**Missing**:
- ❌ No real metrics collection
- ❌ No connection to queue or workers
- ❌ No actual analyzer invocations

---

### 9. API ROUTE: `app/api/reasoning/[id]/route.ts` ❌ COMPLETELY MOCKED
**Status**: Stub only

**What it does**:
- GET endpoint for reasoning events
- Returns hardcoded mockReasoningEvents array with 5 sample events:
  ```
  1. thought: "Analyzing target URL for potential vulnerabilities..."
  2. action: "Running Slither static analysis..."
  3. observation: "Found 3 high-severity issues in reentrancy pattern"
  4. decision: "Prioritizing reentrancy vulnerability for exploit generation"
  5. action: "Generating exploit proof-of-concept..."
  ```
- Filters by `since` query param (timestamp)
- Limits by limit query param (default 50)
- Returns: auditId, events, hasMore (always false), timestamp

**Stubbed/Mocked**: 100% - all events are hardcoded  
**Hardcoded values**:
- Five fake ReasoningEvent objects
- Mock timestamps, analyzers, confidence scores
- No actual reasoning data

**Missing**:
- ❌ No WebSocket support (polling only)
- ❌ No actual reasoning stream from HexStrike
- ❌ Not connected to actual audit execution

---

### 10. LIB: `lib/types.ts` ✅ REAL
**Status**: Complete type definitions

**What it defines**:
- JobStatus: pending_payment, payment_verified, queued, in_progress, completed, failed, cancelled
- Severity: CRITICAL, HIGH, MEDIUM, LOW, INFO
- StateHistoryEntry: status + timestamp + reason
- JobSession: complete audit job with all metadata
- FindingStatus: open, acknowledged, fixed, wont_fix, false_positive
- Vulnerability: full vulnerability record with CVSS, confidence, exploit scenario
- Exploit: vulnerability ID + technique + payload + steps + indicators + constraints
- VerificationResult: success + visualDiff + proofPath + evidence
- SelfEvaluation: confidence + issues + evidence
- AuditReport: full report with vulnerabilities, exploits, verifications, evaluation
- PaymentVerificationResult: valid + amount + blockNumber + confirmations + error

**Stubbed/Mocked**: None - real type definitions  
**Missing**: None - complete

---

### 11. LIB: `lib/storage.ts` ✅ REAL (but incomplete)
**Status**: Functional but in-memory only

**What it does**:
- MemoryJobStore: implements JobStore interface
  - get(id): retrieve job
  - set(id, job): store job
  - update(id, updates): merge updates
  - delete(id): remove job
  - list(walletAddress?): list all or filter by wallet
  - enqueue(id): add to queue
  - dequeue(): remove from queue and return job
- MemoryReportStore: implements ReportStore interface
  - get(id): retrieve report
  - set(id, report): store report
  - delete(id): remove report
- Helper functions:
  - createJob(): creates new job with state history
  - updateJobStatus(): validates transition, updates with state history
- Uses globalThis for persistence across hot reloads (dev mode)

**Stubbed/Mocked**:
- No persistent storage (in-memory Map)
- Will lose all data on server restart
- State transitions are validated but no enforcement of async operations

**Real parts**:
- Complete storage interface
- State history tracking
- Valid transition matrix:
  ```
  pending_payment → [payment_verified, queued, cancelled]
  payment_verified → [queued, in_progress, cancelled]
  queued → [in_progress, cancelled]
  in_progress → [completed, failed, cancelled]
  completed → []
  failed → [queued]
  cancelled → [queued]
  ```

**Missing**:
- ❌ No persistent database (Vercel KV mentioned in comment but not implemented)
- ❌ No indexing or query optimization
- ❌ Will lose data on deployment

---

### 12. LIB: `lib/security.ts` ✅ REAL
**Status**: Complete, functional

**What it does**:
- validateTargetUrl(): checks HTTPS, blocks private IPs (localhost, 10.x, 172.16-31.x, 192.168.x, 127.x, 0.0.0.x, ::1)
- generateSecureAuditId(): creates `audit-{timestamp}-{32 hex chars}` using crypto.randomBytes
- validateAuditId(): regex validation of audit ID format

**Stubbed/Mocked**: None - real implementation  
**Hardcoded values**:
- ALLOWED_PROTOCOLS: ['https:']
- BLOCKED_HOSTS: 24 ranges/IPs
- Private IP ranges (RFC1918)

**Missing**: None - complete

---

### 13. LIB: `lib/payment.ts` ✅ REAL (mostly)
**Status**: Functional, but env-dependent

**What it does**:
- verifyBNKRPayment(txHash, expectedSender, minAmount?):
  - Gets transaction receipt from Base network RPC
  - Validates: receipt exists, status=success, to=BNKR_CONTRACT, transfer logged
  - Extracts Transfer event from logs (topic 0xddf252...)
  - Checks: from=expectedSender, to=TREASURY_ADDRESS, amount >= minRequired
  - Returns: valid + amount + blockNumber + confirmations
- verifyERC20Payment(txHash, tokenAddress, expectedSender, recipientAddress, minAmount):
  - Same flow but for generic ERC-20 tokens
- getBNKRBalance(address): calls balanceOf on BNKR contract
- formatBNKR(amount): converts wei to decimal string

**Stubbed/Mocked**: None - real viem integration  
**Hardcoded values**:
- ERC20_ABI with transfer, transferFrom, balanceOf, Transfer event
- BNKR_CONTRACT: from env or `0x` (empty!)
- TREASURY_ADDRESS: from env or `0x` (empty!)
- BASE_RPC_URL: from env or 'https://mainnet.base.org'
- MIN_AUDIT_PRICE_BNKR: from env or 100 BNKR (18 decimals)
- Transfer event topic: hardcoded as magic string

**Missing**:
- ⚠️ Contract addresses are `0x` by default (will fail if env not set)
- ⚠️ No fallback for missing RPC URL
- ⚠️ No retry logic for RPC calls
- ⚠️ No validation of contract ABIs

**Real parts**:
- viem client integration
- Log parsing and event extraction
- Confirmation counting
- Amount validation

---

### 14. LIB: `lib/utils.ts` ✅ MINIMAL
**Status**: Minimal, incomplete

**What it does**:
- cn(): Tailwind classname merger (clsx + twMerge)
- METADATA object with hardcoded values

**Hardcoded values**:
- name: "AgentxploiTor"
- description: "First AI Security Agent with Visual Exploit Verification - Autonomous Solana security audits on BASE"
- bannerImageUrl: 'https://i.imgur.com/2bsV8mV.png' (with TODO comment)
- iconImageUrl: 'https://i.imgur.com/brcnijg.png' (with TODO comment)
- homeUrl: env or 'http://localhost:3000'
- splashBackgroundColor: '#0a0e27'

**Missing**:
- ❌ Images need to be replaced (TODOs noted)

---

### 15. LIB: `lib/truncateAddress.ts` ✅ COMPLETE
**Status**: Utility, complete

Simply truncates address: first 14 chars + "..." + last 12 chars

---

### 16. LIB HOOK: `lib/hooks/useReasoningStream.ts` ⚠️ REAL HOOK, FAKE DATA
**Status**: Functional component, but feeds from mocked API

**What it does**:
- Custom hook for reasoning event streaming
- Options: auditId, level (minimal/normal/verbose), pollInterval, useWebSocket, maxEvents, callbacks
- Returns: events[], connected, error, isLoading, clear(), reconnect()
- Implements polling (default 2s interval) OR WebSocket (if useWebSocket=true)
- WebSocket URL: `{protocol}//{host}/api/ws/audit/{auditId}/reasoning`
- Polling URL: `/api/reasoning/{auditId}?since={lastTimestamp}&limit=50`
- Event deduplication by ID
- Max 500 events (configurable)
- Exponential backoff reconnect (up to 5 attempts, max 30s delay)
- Filters events by detail level

**Real parts**:
- Hook implementation and state management
- WebSocket connection logic
- Polling implementation
- Event deduplication
- Reconnection strategy

**Stubbed/Mocked**:
- API endpoint `/api/reasoning/[id]` returns hardcoded mock events
- WebSocket server doesn't exist (will fail to connect)
- No actual reasoning data

**Missing**:
- ❌ WebSocket server implementation (referenced but doesn't exist)
- ❌ Real reasoning event data (all from hardcoded mock array)
- ❌ No connection to HexStrike reasoning pipeline

---

### 17. COMPONENT: `components/AgentxploiTor.tsx` ✅ UI COMPLETE
**Status**: Landing page, static

**What it does**:
- Hero section with title, description, CTA buttons
- Stats section (hardcoded: 4 vulns, 100% success, 92% confidence)
- Features section (3 features: visual proof, autonomous, solana expert)
- How it works section (4 step process)
- Footer with copyright

**Stubbed/Mocked**:
- All stats hardcoded (4, 100%, 92%)
- All hero text hardcoded
- No real data integration

**Real parts**:
- Navigation using useRouter()
- Responsive Tailwind design
- Button click handlers

**Missing**: None for this component (it's intentionally static landing page)

---

### 18. COMPONENT: `components/AuditRequestForm.tsx` ✅ FORM COMPLETE
**Status**: Form component, functional but not integrated

**What it does**:
- Form with fields: targetUrl (required), contractAddress (optional), scope (required), priority (required)
- Scope enum: SPL_TOKEN, DEFI, NFT, GENERAL
- Priority enum: NORMAL (10 BNKR), RUSH (25 BNKR)
- Shows price based on priority selection
- onSubmit callback (not connected to API)
- Renders all fields with validation

**Hardcoded values**:
- Priority pricing: 10 BNKR (Normal), 25 BNKR (Rush)
- Scope options: 4 fixed values
- Form validation: targetUrl required
- Placeholder URLs

**Stubbed/Mocked**:
- onSubmit callback not connected to POST /api/audit/request
- No payment flow integration
- No wallet connection

**Missing**:
- ❌ No POST call to /api/audit/request
- ❌ No wallet integration for payment
- ❌ No payment flow (signing transaction)
- ❌ No redirect after submission

---

### 19. COMPONENT: `components/ReasoningStream.tsx` ⚠️ UI COMPLETE, DATA MOCKED
**Status**: Functional component for displaying reasoning stream, but no real data

**What it does**:
- Renders scrollable event log with:
  - Connection indicator (green/red)
  - Detail level selector (minimal/normal/verbose)
  - Event list with timestamps, icons, content
  - Filtering by level
  - Metadata display (analyzer, confidence)
- Attempts WebSocket connection to `/api/ws/audit/{auditId}`
- Falls back to polling `/api/reasoning/{auditId}`
- Auto-scroll to bottom
- Accessibility: aria labels, roles, semantic HTML

**Real parts**:
- Component UI logic
- Event filtering
- WebSocket connection attempt
- Scroll management
- Keyboard accessibility

**Stubbed/Mocked**:
- WebSocket server doesn't exist (will fail to connect)
- Polling returns hardcoded mock events only

**Missing**:
- ❌ No WebSocket server
- ❌ No real reasoning data source

---

### 20. COMPONENT: `components/FindingCard.tsx` ✅ COMPONENT COMPLETE
**Status**: Card component for displaying vulnerability findings, functional

**What it does**:
- Expandable card for each vulnerability
- Shows: severity badge, CVSS score, confidence, title, description
- Expanded view: full details, exploit scenario, AI suggestion, expected outcome, status selector, assign button
- Status options: open, acknowledged, fixed, wont_fix, false_positive
- Severity colors: CRITICAL (red), HIGH (orange), MEDIUM (yellow), LOW (blue), INFO (gray)
- Accessibility: proper ARIA labels, keyboard navigation (Enter/Space to expand)

**Real parts**:
- All UI logic
- State management for expanded/status
- Callback handlers for status changes and assignments

**Stubbed/Mocked**:
- Status changes don't persist (no API call)
- Assign button has hardcoded 'current-user' value

**Missing**:
- ❌ No API integration for status updates
- ❌ No user assignment system
- ❌ No persistence of changes

---

### 21. COMPONENT: `components/FocusDashboard.tsx` ⚠️ UI COMPLETE, DATA MOCKED
**Status**: Dashboard component with focus mode feature

**What it does**:
- Fetches from `/api/dashboard/stats` and `/api/dashboard/audits`
- Displays stats grid: activeAudits, completedToday, criticalFindings, totalFindings
- Displays audit list with status, findings count
- Focus Mode: keyboard-driven navigation (⌘F to toggle, arrows/j/k to navigate, Enter to select)
- Active Audit View: shows selected audit details
- Responsive design (sidebar collapsible on mobile)
- Ambient color changes based on audit status

**Real parts**:
- Component state management
- Keyboard event handling
- Fetch logic
- Responsive design
- Focus mode implementation

**Stubbed/Mocked**:
- `/api/dashboard/stats` returns hardcoded stats
- `/api/dashboard/audits` returns hardcoded audits
- No real data integration

**Missing**:
- ❌ No connection to actual job data
- ❌ Stats don't aggregate real audits

---

### 22. COMPONENT: `components/AttackPathGraph.tsx` ✅ VISUALIZATION COMPLETE
**Status**: Graph visualization component, functional

**What it does**:
- SVG-based attack path graph visualization
- Layouts nodes in columns by type: entry → vulnerability → exploit → impact → asset
- Interactive: pan, zoom (mouse drag and wheel)
- Click nodes to see details in panel
- Connects with bezier curves showing attack flow
- Severity-based coloring and glow effects
- Responsive sizing

**Real parts**:
- SVG rendering
- Graph layout algorithm
- Pan/zoom interaction
- Event handling

**Stubbed/Mocked**:
- Receives nodes/edges as props (no data source shown)

**Missing**: None for this component (data provider would pass real nodes/edges)

---

### 23. COMPONENT: `components/Demo.tsx` ⚠️ MOSTLY REAL, INTEGRATION INCOMPLETE
**Status**: Demo/test component for Farcaster SDK

**What it does**:
- Tabs: Actions, Context, Wallet
- Actions tab: list of Farcaster mini app actions with detailed implementations
- Context tab: shows frame context object (Frame Data from Farcaster)
- Wallet tab: wallet connection and signing demo (wagmi-based)
- Haptic feedback (selectionChanged, impactOccurred)
- Safe area inset handling for mobile frames

**Real parts**:
- All action components (SignIn, QuickAuth, OpenMiniApp, ViewProfile, etc.)
- Wallet interactions (WagmiProvider integration)
- Frame context display
- SDK integration with Farcaster

**Stubbed/Mocked**:
- Some actions may have stub implementations in their sub-components
- Base Pay component referenced but could be incomplete

**Missing**:
- ⚠️ Unclear if all sub-action components are fully implemented
- ⚠️ RequestCameraMicrophoneAction conditionally included based on capabilities

---

### 24. APP: `app/layout.tsx` ✅ ROOT LAYOUT
**Status**: Complete

Simple root layout wrapper with Providers component.

---

### 25. APP: `app/page.tsx` ✅ HOME PAGE METADATA
**Status**: Complete

Sets up Farcaster frame metadata and renders AgentxploiTor component.

---

## CRITICAL GAPS SUMMARY

### 🚨 Tier 1: Architecture Blockers (Must Fix First)

#### Gap 1.1: No HexStrike Agent Connection
**Files affected**: `api/audit/request/route.ts`, `api/audit/results/route.ts`, `api/reasoning/[id]/route.ts`

**Current state**:
- Job is created and stored in memory
- If paymentVerified, job is enqueued via `jobStore.enqueue(auditId)`
- No worker/queue processor exists
- No call to HexStrike agents

**What's missing**:
- Queue worker thread/service that dequeues jobs
- HTTP/WebSocket client to HexStrike API
- Mapping from job to HexStrike audit request
- No wait for audit results
- No result storage back to job/report

**Impact**: Audits never execute. Jobs sit in queue forever.

**Effort**: 3-4 iterations (API integration + queue worker + error handling)

---

#### Gap 1.2: No WebSocket Server
**Files affected**: `lib/hooks/useReasoningStream.ts`, `components/ReasoningStream.tsx`

**Current state**:
- useReasoningStream hook attempts WebSocket connection to `/api/ws/audit/{auditId}/reasoning`
- No `/app/api/ws/` routes exist
- Hook falls back to polling `/api/reasoning/[id]` which returns hardcoded mock data

**What's missing**:
- WebSocket route handler at `/app/api/ws/audit/[id]/reasoning/route.ts` (or `route.js`)
- WebSocket upgrade handling in Next.js (uses node HTTP upgrade)
- Broadcasting of HexStrike reasoning events to connected clients
- Event queue for buffering events between HexStrike and client connection

**Impact**: Can't see live reasoning stream. Polling returns same mock data forever.

**Effort**: 2-3 iterations (WebSocket server + event streaming from HexStrike)

---

#### Gap 1.3: No Persistent Storage
**Files affected**: `lib/storage.ts`, all API routes using jobStore/reportStore

**Current state**:
- All data stored in globalThis Maps (in-memory only)
- Data lost on server restart/deployment
- Two identical copies work around hot-reload issues

**What's missing**:
- Vercel KV integration (mentioned in comment, not implemented)
- OR Redis integration for development
- Migration from MemoryJobStore to KVJobStore
- Transaction support for concurrent updates

**Impact**: Production deployments lose all audit history. User experience broken after restart.

**Effort**: 2-3 iterations (KV integration + migration)

---

### 🟡 Tier 2: Feature Gaps (Must Complete Before Launch)

#### Gap 2.1: No Audit Report Generation
**Files affected**: `api/audit/results/[id]/route.ts`, `lib/storage.ts` (reportStore)

**Current state**:
- audit/results endpoint returns: "Report being processed" message
- Reports never written to reportStore
- Falls back to job.findingsCount if report missing

**What's missing**:
- Report generation pipeline in queue worker
- Mapping HexStrike results to AuditReport schema
- Vulnerability extraction and categorization
- Exploit details formatting
- Verification result processing
- Report storage to reportStore

**Impact**: Users never see detailed audit results.

**Effort**: 3-4 iterations (result processing + report schema mapping)

---

#### Gap 2.2: No Payment Flow Integration
**Files affected**: `components/AuditRequestForm.tsx`, payment verification workflow

**Current state**:
- Form collects all data
- onSubmit callback does nothing (no API call)
- No wallet connection/signing
- No transaction broadcasting

**What's missing**:
- Form submission → POST `/api/audit/request`
- Wallet connection (already has Wagmi provider)
- Sign and broadcast BNKR transfer to treasury
- Wait for confirmation
- Submit paymentTxHash to API
- Redirect to audit status page

**Impact**: Users can't submit audits. No revenue collection.

**Effort**: 2-3 iterations (form submission + wallet integration)

---

#### Gap 2.3: Dashboard Data Not Real
**Files affected**: `api/dashboard/audits/route.ts`, `api/dashboard/stats/route.ts`

**Current state**:
- Returns hardcoded mock audits/stats
- FocusDashboard component fetches these

**What's missing**:
- Connect to actual jobStore
- Aggregate job data (count by status, sum findings by severity)
- Calculate daily/weekly stats
- Real-time updates

**Impact**: Dashboard misleading, shows fake data.

**Effort**: 1-2 iterations (query jobStore + aggregation)

---

#### Gap 2.4: Metrics Endpoint Not Real
**Files affected**: `api/metrics/route.ts`

**Current state**:
- 100% hardcoded Prometheus metrics
- Returns same data every request

**What's missing**:
- Real metrics collection/instrumentation
- Queue depth from jobStore
- Active job counts
- Analyzer success rates (from HexStrike)
- Circuit breaker states (from HexStrike)

**Impact**: Monitoring/observability shows fake data.

**Effort**: 2-3 iterations (instrument code + HexStrike metrics)

---

### 🟠 Tier 3: Polish Gaps (Nice-to-Have Before MVP)

#### Gap 3.1: Status Changes Don't Persist
**Files affected**: `components/FindingCard.tsx`

**Current state**:
- Status selector UI works
- onStatusChange callback fires
- No API call to save changes

**What's missing**:
- API endpoint to update finding status
- Persist to report/database

**Impact**: Users can change status locally but changes lost on refresh.

**Effort**: 1 iteration

---

#### Gap 3.2: Images Need Replacement
**Files affected**: `lib/utils.ts`

**Current state**:
```typescript
bannerImageUrl: 'https://i.imgur.com/2bsV8mV.png', // TODO: Replace
iconImageUrl: 'https://i.imgur.com/brcnijg.png',  // TODO: Replace
```

**What's missing**:
- AgentxploiTor brand banner image (1200x630px recommended)
- AgentxploiTor icon (512x512px recommended)

**Impact**: Farcaster frame preview shows placeholder/default images.

**Effort**: <1 iteration (graphic design asset)

---

#### Gap 3.3: Contract Addresses Not Set
**Files affected**: `lib/payment.ts`

**Current state**:
```typescript
const BNKR_CONTRACT = (process.env.NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS || '0x') as `0x${string}`;
const TREASURY_ADDRESS = (process.env.NEXT_PUBLIC_TREASURY_ADDRESS || '0x') as `0x${string}`;
```

**What's missing**:
- Environment variables not set
- Will fail silently with address `0x` if env missing

**Impact**: Payment verification always fails in production.

**Effort**: <1 iteration (set env vars)

---

#### Gap 3.4: Error Handling Incomplete
**Files affected**: All API routes

**Current state**:
- Basic try/catch blocks
- Generic 500 errors
- No detailed error logging
- No circuit breaker pattern

**What's missing**:
- Structured error responses
- Request logging/tracing
- Timeout handling
- Retry logic
- Circuit breaker for HexStrike API calls

**Impact**: Hard to debug production issues. Cascading failures.

**Effort**: 2-3 iterations

---

## INTEGRATION MAP: What Needs to Connect

### Data Flow: Audit Request → Execution → Results

```
1. User submits form
   ├─ POST /api/audit/request
   ├─ Wallet signs BNKR transfer
   ├─ TX broadcasts to Base network
   └─ TX hash submitted to API
   
2. API validates payment
   ├─ verifyBNKRPayment() ✅ (implemented)
   ├─ Creates JobSession ✅ (implemented)
   ├─ Stores in jobStore ✅ (implemented)
   └─ Enqueues for processing ✅ (implemented)
   
3. Queue worker processes job ❌ MISSING
   ├─ Dequeue job from jobStore
   ├─ Call HexStrike API ❌ MISSING
   ├─ Get audit results ❌ MISSING
   ├─ Generate AuditReport ❌ MISSING
   ├─ Store report to reportStore ❌ MISSING
   └─ Update job status to 'completed' ❌ MISSING
   
4. User checks audit status
   ├─ GET /api/audit/status/[id] ✅ (partially working)
   └─ Returns job status ✅
   
5. User views results
   ├─ GET /api/audit/results/[id]
   ├─ Retrieves report ❌ MISSING (reports never created)
   └─ Returns vulnerabilities/exploits ❌
   
6. User watches reasoning stream
   ├─ WebSocket to /api/ws/audit/[id]/reasoning ❌ MISSING
   └─ Server broadcasts HexStrike events ❌ MISSING
```

### Components Needing Integration

| Component | Currently | Needs |
|-----------|-----------|-------|
| AuditRequestForm | Form only | Form submission → API call + wallet signing |
| ReasoningStream | Mocked polling | WebSocket server + real HexStrike events |
| FocusDashboard | Hardcoded stats | Real jobStore queries + aggregation |
| FindingCard | UI only | API endpoints to save status changes |
| AttackPathGraph | UI only | Pass real nodes/edges from report data |

---

## ENVIRONMENT VARIABLES REQUIRED

```bash
# Authentication
NEXT_PUBLIC_FARCASTER_QUICK_AUTH_URL=https://...

# Blockchain
NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_TREASURY_ADDRESS=0x...
NEXT_PUBLIC_BASE_RPC_URL=https://mainnet.base.org

# Pricing
MIN_AUDIT_PRICE_BNKR=100000000000000000000  # 100 BNKR in wei

# HexStrike Integration (MISSING)
HEXSTRIKE_API_URL=http://localhost:3001  # or deployed URL
HEXSTRIKE_API_KEY=sk_...

# Storage (MISSING)
KV_URL=...  # Vercel KV or Redis
KV_REST_API_TOKEN=...

# Vercel
NEXT_PUBLIC_URL=https://agentxploitor.example.com
VERCEL_ENV=production
VERCEL_URL=agentxploitor.example.com
```

---

## IMPLEMENTATION PRIORITY ROADMAP

### Phase 1: Make It Work (Iterations 1-5)
1. ✅ Audit request form submission + wallet integration
2. ✅ Queue worker that processes jobs
3. ✅ Basic HexStrike API integration
4. ✅ Report storage to jobStore
5. ✅ Dashboard showing real data

**Time**: ~5 iterations  
**Outcome**: MVP where users can submit audits and see results

---

### Phase 2: Real-Time Experience (Iterations 6-8)
1. ✅ WebSocket server for reasoning stream
2. ✅ HexStrike event streaming to WebSocket clients
3. ✅ Persistent storage (Vercel KV or Redis)

**Time**: ~3 iterations  
**Outcome**: Live reasoning stream, data survives restart

---

### Phase 3: Polish (Iterations 9-10)
1. ✅ Error handling + logging
2. ✅ Status change persistence
3. ✅ Metrics instrumentation
4. ✅ Image assets

**Time**: ~2 iterations  
**Outcome**: Production-ready

---

## QUICK REFERENCE: STUB LOCATIONS

| What | Where | Line | Status |
|------|-------|------|--------|
| Mock audits | api/dashboard/audits/route.ts | 2-25 | ❌ Replace with jobStore.list() |
| Mock stats | api/dashboard/stats/route.ts | 4-9 | ❌ Compute from jobStore |
| Mock metrics | api/metrics/route.ts | 2-52 | ❌ Collect real metrics |
| Mock reasoning | api/reasoning/[id]/route.ts | 2-38 | ❌ Stream from HexStrike |
| Hardcoded URLs | lib/utils.ts | 6-7 | ⚠️ Replace with real images |
| No form submission | components/AuditRequestForm.tsx | 40-50 | ❌ Add POST call |
| No WebSocket server | - | N/A | ❌ Create /api/ws/ routes |
| No queue worker | - | N/A | ❌ Create queue processor |
| No HexStrike client | - | N/A | ❌ Create agent integration |

---

## FILE SIZE ANALYSIS

| File | Lines | Status | Should Refactor? |
|------|-------|--------|------------------|
| middleware.ts | 48 | ✅ | No (minimal) |
| api/auth/route.ts | 83 | ✅ | No |
| api/audit/request/route.ts | 165 | ✅ | No |
| api/audit/status/[id]/route.ts | 64 | ⚠️ | Maybe (split progress calc) |
| api/audit/results/[id]/route.ts | 76 | ⚠️ | Maybe |
| lib/payment.ts | 216 | ✅ | No |
| lib/storage.ts | 195 | ✅ | No (but needs migration to KV) |
| lib/hooks/useReasoningStream.ts | 219 | ⚠️ | No (logic is good) |
| components/ReasoningStream.tsx | 339 | ✅ | No |
| components/FindingCard.tsx | 310 | ✅ | No |
| components/FocusDashboard.tsx | 463 | ⚠️ | Yes (split views into subcomponents) |
| components/AgentxploiTor.tsx | 217 | ✅ | No |
| components/AuditRequestForm.tsx | 217 | ✅ | No |
| components/AttackPathGraph.tsx | 330 | ✅ | No |
| components/Demo.tsx | 418 | ✅ | No |

**All files under 500 lines**: ✅ Passes Orion-OS component size limit

---

## TESTING GAPS

| Feature | Has Tests? | Status |
|---------|-----------|--------|
| Payment verification | ⚠️ Not seen | Likely missing |
| URL validation | ⚠️ Not seen | Likely missing |
| Job state transitions | ⚠️ Not seen | Likely missing |
| ReasoningStream hook | ⚠️ Not seen | Likely missing |
| Payment formatting | ⚠️ Not seen | Likely missing |

**Note**: Only found `/src/components/__tests__/` and `/src/lib/__tests__/` directories with minimal test files.

---

## SUMMARY BY CATEGORY

### ✅ Ready to Deploy
- middleware.ts (rate limiting)
- api/auth/route.ts (Farcaster JWT)
- lib/security.ts (URL + audit ID validation)
- lib/types.ts (type definitions)
- lib/truncateAddress.ts (utility)
- UI components (AgentxploiTor, AuditRequestForm, etc.)

### ⚠️ Partially Ready (Needs Integration)
- api/audit/request/route.ts (needs form submission + wallet)
- lib/payment.ts (needs contract addresses in env)
- lib/storage.ts (needs migration to persistent KV)
- lib/hooks/useReasoningStream.ts (needs WebSocket server + real data)
- FocusDashboard (needs real jobStore queries)

### ❌ Not Ready (Core Missing)
- Queue worker (doesn't exist)
- HexStrike integration (doesn't exist)
- WebSocket server (doesn't exist)
- Report generation (doesn't exist)
- Metrics collection (doesn't exist)

---

**End of Gap Analysis**

