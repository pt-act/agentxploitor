# AgentxploiTor BASE Mini-App - Technical Specification

**Version**: 1.0  
**Date**: 2026-02-11  
**Status**: Specification  
**Estimated Time**: 4-5 hours

---

## 🎯 Overview

Build a BASE mini-app that serves as the public interface for AgentxploiTor, enabling users to request security audits, pay with crypto, and receive autonomous security reports with visual proof.

**Core Innovation**: First AI security agent with economic activity on BASE blockchain

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    BASE Mini-App (Frontend)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Next.js 14 + Tailwind + Coinbase Wallet SDK         │  │
│  │  - Landing Page                                       │  │
│  │  - Audit Request Form                                 │  │
│  │  - Payment Integration (BASE/BNKR)                    │  │
│  │  - Results Dashboard                                  │  │
│  │  - Live Audit Stream                                  │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │ API calls                             │
│                     ▼                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Next.js API Routes (Backend)                         │  │
│  │  - POST /api/audit/request                            │  │
│  │  - GET /api/audit/status/:id                          │  │
│  │  - GET /api/audit/results/:id                         │  │
│  │  - POST /api/payment/verify                           │  │
│  │  - GET /api/stream/audit/:id (SSE)                    │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │                                       │
│                     ▼                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Vercel KV (Redis)                                    │  │
│  │  - Audit requests queue                               │  │
│  │  - Audit results cache                                │  │
│  │  - Payment records                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Webhook
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentxploiTor (Python Agent)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Audit Worker                                         │  │
│  │  - Poll /api/audit/queue                              │  │
│  │  - Execute autonomous audit                           │  │
│  │  - POST results to /api/audit/submit                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BASE Blockchain                          │
│  - BNKR Token Contract                                      │
│  - Your Wallet: [address]                                   │
│  - Payment Tracking                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Pages & Components

### 1. Landing Page (`/`)

**Purpose**: Introduce AgentxploiTor and convert visitors to users

**Layout**:
```
┌────────────────────────────────────────┐
│  HEADER                                │
│  [AgentxploiTor Logo] [Request Audit] │
├────────────────────────────────────────┤
│  HERO                                  │
│  First AI Security Agent with          │
│  Visual Exploit Verification           │
│                                        │
│  [Request Audit CTA]                   │
├────────────────────────────────────────┤
│  FEATURES (3 cards)                    │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │Visual│ │Auto  │ │Solana│          │
│  │Proof │ │nomous│ │Expert│          │
│  └──────┘ └──────┘ └──────┘          │
├────────────────────────────────────────┤
│  STATS                                 │
│  4 Vulnerabilities Found               │
│  100% Success Rate                     │
│  $0 Funds Lost (prevented)             │
├────────────────────────────────────────┤
│  HOW IT WORKS (4 steps)                │
│  1→ Request → 2→ Pay → 3→ Audit →     │
│  4→ Report                             │
├────────────────────────────────────────┤
│  FOOTER                                │
│  MIT Licensed | Built on BASE          │
└────────────────────────────────────────┘
```

**Components**:
- `Header.tsx` - Navigation bar
- `Hero.tsx` - Main value prop
- `FeatureCard.tsx` - Feature showcase
- `Stats.tsx` - Social proof
- `HowItWorks.tsx` - User journey
- `Footer.tsx`

---

### 2. Request Audit Page (`/request`)

**Purpose**: Capture audit requests and payments

**Form Fields**:
```typescript
interface AuditRequestForm {
  targetUrl: string;        // Required
  contractAddress?: string; // Optional
  scope: AuditScope;        // Dropdown
  priority: Priority;       // Normal | Rush
  contactEmail?: string;    // Optional
}

enum AuditScope {
  SPL_TOKEN = 'SPL Token Program',
  DEFI = 'DeFi Protocol',
  NFT = 'NFT Contract',
  GENERAL = 'General Security Audit'
}

enum Priority {
  NORMAL = 'Normal (24-48h) - 10 BNKR',
  RUSH = 'Rush (1-6h) - 25 BNKR'
}
```

**Flow**:
1. User fills form
2. Clicks "Pay with BASE Wallet"
3. Wallet connect modal (Coinbase Wallet/WalletConnect)
4. Transaction preview (BNKR amount)
5. User confirms transaction
6. Wait for confirmation (show spinner)
7. Transaction confirmed → Audit queued
8. Redirect to `/audit/[id]` status page

**Components**:
- `AuditRequestForm.tsx`
- `WalletConnectButton.tsx`
- `PaymentModal.tsx`
- `TransactionStatus.tsx`

---

### 3. Audit Status Page (`/audit/[id]`)

**Purpose**: Real-time audit progress and results

**States**:

**State 1: Pending Payment**
```
⏳ Waiting for Payment Confirmation
Transaction: 0x...abc
[View on BaseScan]
```

**State 2: In Queue**
```
📋 Audit Queued
Position: #2
Estimated start: 5 minutes
```

**State 3: In Progress** (Live Stream)
```
🤖 Agent Working...

[Live Console Output]
> Scanning target: token-program.so
> Found 3 potential vulnerabilities
> Generating exploits...
> Opening browser for verification...
> Capturing visual proof...

Progress: ████████░░ 80%
```

**State 4: Complete**
```
✅ Audit Complete

Vulnerabilities Found: 3
  - 1 CRITICAL (CVSS 9.8)
  - 1 HIGH (CVSS 7.5)
  - 1 MEDIUM (CVSS 5.3)

Visual Proof: [View Screenshots]
Confidence: 92%

[Download Report] [View Details]
```

**Components**:
- `AuditStatus.tsx` - Status display
- `LiveConsole.tsx` - Real-time output
- `ProgressBar.tsx`
- `VulnerabilityCard.tsx`
- `VisualProof.tsx` - Screenshot viewer

---

### 4. Results Page (`/audit/[id]/results`)

**Purpose**: Detailed vulnerability report with visual proof

**Layout**:
```
┌────────────────────────────────────────┐
│  SUMMARY                               │
│  Target: token-2022.so                 │
│  Status: ✅ Complete                   │
│  Findings: 3 vulnerabilities           │
│  Confidence: 92%                       │
├────────────────────────────────────────┤
│  VULNERABILITIES                       │
│  ┌──────────────────────────────────┐ │
│  │ 🚨 CRITICAL: Missing Signer     │ │
│  │ CVSS: 9.8                        │ │
│  │ Location: transfer.rs:45         │ │
│  │ [Visual Proof] [Remediation]    │ │
│  └──────────────────────────────────┘ │
│  [More vulnerabilities...]            │
├────────────────────────────────────────┤
│  VISUAL PROOF                          │
│  ┌──────────┐ ┌──────────┐           │
│  │ Before   │ │ After    │           │
│  │ [img]    │ │ [img]    │           │
│  └──────────┘ └──────────┘           │
│  Visual Diff: 45.3% changed           │
├────────────────────────────────────────┤
│  ACTIONS                               │
│  [Download PDF] [Share] [New Audit]   │
└────────────────────────────────────────┘
```

**Components**:
- `ResultsSummary.tsx`
- `VulnerabilityList.tsx`
- `VulnerabilityDetail.tsx`
- `VisualProofViewer.tsx`
- `RemediationGuide.tsx`
- `DownloadButton.tsx`

---

## 🔷 API Endpoints

### POST `/api/audit/request`

**Purpose**: Create new audit request

**Request**:
```typescript
{
  targetUrl: string;
  contractAddress?: string;
  scope: string;
  priority: string;
  paymentTxHash: string;  // BASE transaction hash
  paymentAmount: number;  // BNKR amount
}
```

**Response**:
```typescript
{
  auditId: string;
  status: 'pending_payment' | 'queued';
  queuePosition: number;
  estimatedStart: Date;
}
```

**Implementation**:
1. Validate payment transaction on BASE
2. Verify payment amount matches priority
3. Create audit request in Vercel KV
4. Add to queue
5. Return audit ID

---

### GET `/api/audit/status/:id`

**Purpose**: Get current audit status

**Response**:
```typescript
{
  id: string;
  status: 'pending_payment' | 'queued' | 'in_progress' | 'completed' | 'failed';
  queuePosition?: number;
  progress?: number; // 0-100
  findings?: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  completedAt?: Date;
}
```

---

### GET `/api/audit/results/:id`

**Purpose**: Get completed audit results

**Response**:
```typescript
{
  id: string;
  targetUrl: string;
  status: 'completed';
  vulnerabilities: Vulnerability[];
  visualProof: {
    beforeScreenshot: string; // base64 or URL
    afterScreenshot: string;
    visualDiff: number;
  };
  confidence: number;
  report: string; // Markdown
  completedAt: Date;
}
```

---

### POST `/api/payment/verify`

**Purpose**: Verify BASE payment transaction

**Request**:
```typescript
{
  txHash: string;
  expectedAmount: number;
  expectedRecipient: string; // Your wallet
}
```

**Response**:
```typescript
{
  valid: boolean;
  amount: number;
  from: string;
  timestamp: Date;
}
```

**Implementation**:
1. Query BASE blockchain for transaction
2. Verify amount and recipient
3. Check confirmation status
4. Return validation result

---

### GET `/api/stream/audit/:id` (Server-Sent Events)

**Purpose**: Real-time audit progress updates

**Stream Events**:
```typescript
event: status
data: {"status": "in_progress", "progress": 25}

event: log
data: {"message": "Scanning target...", "timestamp": "..."}

event: finding
data: {"severity": "CRITICAL", "title": "Missing signer check"}

event: complete
data: {"status": "completed", "findings": 3}
```

---

## 💾 Data Storage (Vercel KV / Redis)

### Keys Structure

```
# Audit requests
audit:{id}                → AuditRequest object
audit:queue              → List of pending audit IDs
audit:active             → Currently running audit ID

# Results cache
audit:{id}:results       → AuditResult object
audit:{id}:logs          → List of log entries

# Payment tracking
payment:{txHash}         → Payment verification record

# Stats (cached)
stats:total_audits       → Counter
stats:vulnerabilities    → Counter
```

---

## 🎨 UI/UX Design

### Color Scheme (Security Theme)

```css
:root {
  --primary: #00ff41;     /* Matrix green (agent active) */
  --danger: #ff0055;      /* Critical vulnerabilities */
  --warning: #ffaa00;     /* High severity */
  --info: #00aaff;        /* Medium */
  --bg-dark: #0a0e27;     /* Dark blue background */
  --bg-card: #1a1f3a;     /* Card background */
  --text-primary: #ffffff;
  --text-secondary: #8892b0;
}
```

### Typography

```css
/* Headers */
font-family: 'Inter', sans-serif;
font-weight: 700;

/* Body */
font-family: 'Roboto Mono', monospace; /* Code/terminal feel */
font-weight: 400;
```

### Components Style Guide

**Buttons**:
- Primary: Green glow effect on hover
- Danger: Red for critical actions
- Ghost: Transparent with border

**Cards**:
- Dark background with subtle border
- Hover: Slight elevation + glow
- Border radius: 8px

**Status Indicators**:
- Pending: Yellow pulse
- In Progress: Green animated spinner
- Complete: Green checkmark
- Failed: Red X

---

## 🔐 Security Considerations

### Payment Verification

**Must verify**:
1. ✅ Transaction is confirmed on BASE
2. ✅ Amount matches requested audit tier
3. ✅ Recipient is your wallet address
4. ✅ Transaction not already used (prevent replay)

**Implementation**:
```typescript
async function verifyPayment(txHash: string): Promise<boolean> {
  const tx = await baseProvider.getTransaction(txHash);
  
  // Check confirmations
  if (tx.confirmations < 1) return false;
  
  // Verify recipient
  if (tx.to !== process.env.AGENT_WALLET_ADDRESS) return false;
  
  // Verify amount (with tolerance for gas)
  const expectedAmount = parseEther(auditTier.price);
  if (tx.value.lt(expectedAmount)) return false;
  
  // Check not already used
  const used = await kv.get(`payment:${txHash}`);
  if (used) return false;
  
  // Mark as used
  await kv.set(`payment:${txHash}`, true);
  
  return true;
}
```

### Rate Limiting

**API Routes**:
- `/api/audit/request`: 5 requests per hour per IP
- `/api/audit/status`: 60 requests per minute
- `/api/audit/results`: 30 requests per minute

**Implementation**: Use Vercel Edge Config or Upstash rate limiting

---

## 🚀 Deployment

### Environment Variables

```bash
# BASE Blockchain
NEXT_PUBLIC_BASE_RPC_URL=https://mainnet.base.org
NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_AGENT_WALLET_ADDRESS=0x...  # Your wallet

# Vercel KV (Redis)
KV_URL=...
KV_REST_API_URL=...
KV_REST_API_TOKEN=...
KV_REST_API_READ_ONLY_TOKEN=...

# Agent Webhook
AGENT_WEBHOOK_SECRET=...  # For securing agent→miniapp communication

# Coinbase Developer Platform (optional)
CDP_API_KEY=...
CDP_API_SECRET=...
```

### Vercel Configuration

**vercel.json**:
```json
{
  "framework": "nextjs",
  "buildCommand": "next build",
  "devCommand": "next dev",
  "installCommand": "npm install",
  "env": {
    "NEXT_PUBLIC_BASE_RPC_URL": "@base-rpc-url",
    "KV_URL": "@kv-url"
  }
}
```

---

## 🧪 Testing Strategy

### Unit Tests
- Payment verification logic
- Form validation
- Data transformations

### Integration Tests
- API endpoint responses
- Redis operations
- Wallet connection flow

### E2E Tests (Cypress/Playwright)
- Complete audit request flow
- Payment process
- Results viewing

**Test Coverage Target**: 70%+ for critical paths

---

## 📊 Analytics & Monitoring

### Events to Track

**User Actions**:
- Page views
- Audit requests started
- Payments initiated
- Payments completed
- Reports downloaded

**Agent Actions**:
- Audits queued
- Audits started
- Audits completed
- Vulnerabilities found

**Performance**:
- Page load times
- API response times
- Payment confirmation time
- Audit completion time

**Implementation**: Vercel Analytics + custom events

---

## 🎬 Demo Script Integration

### For Bounty 2 Video

**Minute 1**: Show Landing Page
- "AgentxploiTor mini-app on BASE"
- Highlight visual verification feature

**Minute 2**: Request Audit
- Fill form with Solana contract
- Connect BASE wallet (show 537 BNKR)
- Pay 10 BNKR
- Transaction confirmed

**Minute 3**: Live Audit
- Status page shows agent working
- Live console output scrolling
- Browser perception preview
- Visual proof captured

**Minute 4**: Results
- 3 vulnerabilities found
- Show before/after screenshots
- Confidence 92%
- Download report

**Key Message**: "Complete autonomous economic cycle - user pays, agent delivers, all on-chain"

---

## 🎯 Success Metrics

### Technical Success
- ✅ Deploys to Vercel without errors
- ✅ Payment flow works on BASE
- ✅ Agent receives requests automatically
- ✅ Visual proof displays correctly

### Bounty 2 Success
- ✅ Judges can interact with live demo
- ✅ Shows "agent in economy" capability
- ✅ Demonstrates BASE integration
- ✅ Proves autonomous operation

### User Success (Future)
- Real users request audits
- Payments are processed
- Reports are delivered
- Reputation builds

---

## 📋 Implementation Checklist

**Phase 1: Setup** (30 min)
- [ ] Clone BASE mini-app template
- [ ] Install dependencies
- [ ] Configure environment variables
- [ ] Test local dev server

**Phase 2: Frontend** (2 hours)
- [ ] Landing page
- [ ] Request audit form
- [ ] Payment integration
- [ ] Status page
- [ ] Results page

**Phase 3: Backend** (1.5 hours)
- [ ] API routes
- [ ] Vercel KV setup
- [ ] Payment verification
- [ ] Agent webhook

**Phase 4: Agent Integration** (30 min)
- [ ] Agent polls for requests
- [ ] Agent submits results
- [ ] Test end-to-end flow

**Phase 5: Deploy** (30 min)
- [ ] Deploy to Vercel
- [ ] Configure domain (optional)
- [ ] Test production
- [ ] Record demo

---

## 🚀 Next Steps

1. ✅ Spec complete
2. ⏭️ Create tasks.md (breakdown)
3. ⏭️ Build mini-app
4. ⏭️ Test locally
5. ⏭️ Deploy
6. ⏭️ Record demo
7. ⏭️ Submit Bounty 2

**Estimated Total Time**: 4-5 hours  
**Status**: Ready to build

🧬 ↔ ☀️

[Quantum_State: ALIGNED]
