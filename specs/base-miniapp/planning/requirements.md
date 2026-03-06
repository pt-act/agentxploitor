# AgentxploiTor BASE Mini-App - Requirements

**Project**: BASE Mini-App for AgentxploiTor  
**Goal**: Public interface for autonomous security agent on BASE  
**Target**: Bounty 2 submission enhancement  
**Timeline**: 4 hours

---

## 🎯 Vision

**AgentxploiTor Mini-App** enables users to:
1. Request security audits through web interface
2. Pay for audits using BASE wallet (BNKR tokens)
3. Receive autonomous security reports
4. View agent's past audit history
5. See real-time audit status

**The Economic Cycle**:
```
User → Request Audit → Pay (BASE) → Agent Audits → Visual Proof → Report → User
```

---

## 👤 User Stories

### As a DeFi Protocol Owner
- I want to **request a security audit** of my Solana program
- I want to **pay with crypto** (BNKR on BASE)
- I want to **receive automated findings** without human delays
- I want to **see visual proof** that vulnerabilities are real
- I want to **track audit status** in real-time

### As the AgentxploiTor Agent
- I want to **receive audit requests** automatically
- I want to **accept payment** on BASE blockchain
- I want to **display my capabilities** (visual verification)
- I want to **show my reputation** (past audits)
- I want to **operate autonomously** (no human in ops loop)

### As a Bounty 2 Judge
- I want to **see the agent in action** (live demo)
- I want to **understand the economic model** (how it makes money)
- I want to **verify blockchain integration** (real BASE transactions)
- I want to **assess autonomy** (agent operates without human)

---

## 🎨 Core Features (MVP)

### 1. Landing Page
**Purpose**: Introduce AgentxploiTor and its unique capability

**Content**:
- Hero section: "First AI Security Agent with Visual Verification"
- Features: Autonomous, Visual Proof, Self-Evaluating, Solana-Focused
- Stats: Vulnerabilities found, Audits completed, Success rate
- CTA: "Request Security Audit"

### 2. Audit Request Form
**Purpose**: Users submit audit requests

**Fields**:
- Target URL (Solana Explorer link or GitHub repo)
- Contract address (if applicable)
- Audit scope (SPL token, DeFi protocol, NFT, etc.)
- Contact info (optional for results delivery)
- Payment: Connect BASE wallet

**Flow**:
1. User fills form
2. Connects BASE wallet
3. Pays audit fee (e.g., 10 BNKR)
4. Transaction confirmed
5. Audit queued for agent

### 3. Agent Dashboard
**Purpose**: Show agent capabilities and status

**Displays**:
- Agent status: Online/Auditing/Idle
- Current audit in progress (if any)
- Capabilities:
  - ✅ Browser Perception (screenshots)
  - ✅ Visual Verification (before/after)
  - ✅ Self-Evaluation (confidence scoring)
  - ✅ Solana Expertise (SPL programs)

### 4. Audit Results View
**Purpose**: Display completed audits with visual proof

**Shows**:
- Vulnerability summary (CRITICAL, HIGH, MEDIUM, LOW)
- Visual proof screenshots (before/after)
- Confidence scores
- Remediation recommendations
- Download full report (PDF/JSON)

### 5. Payment Integration
**Purpose**: Accept payments on BASE

**Implementation**:
- Coinbase Developer Platform SDK
- BASE wallet connection (WalletConnect/Coinbase Wallet)
- BNKR token contract
- Transaction tracking

### 6. Live Audit Stream (Bonus)
**Purpose**: Show agent working in real-time

**Shows**:
- Real-time console output (sanitized)
- Current step (scanning, exploiting, verifying)
- Browser perception preview (if safe to show)
- Progress bar

---

## 🔷 Technical Requirements

### Frontend
- **Framework**: Next.js 14 (from template)
- **Styling**: Tailwind CSS (from template)
- **Wallet**: Coinbase Wallet SDK / WalletConnect
- **State**: React hooks + Context

### Backend
- **API**: Next.js API routes
- **Database**: Vercel KV (Redis) for audit queue
- **Agent Integration**: Webhook to AgentxploiTor
- **Notifications**: Server-Sent Events for live updates

### Blockchain
- **Network**: BASE (Coinbase L2)
- **Token**: BNKR (your 537 tokens)
- **Wallet**: Your BASE wallet address
- **Explorer**: BaseScan

---

## 📊 Data Model

### Audit Request
```typescript
interface AuditRequest {
  id: string;
  targetUrl: string;
  contractAddress?: string;
  scope: 'spl-token' | 'defi' | 'nft' | 'general';
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  paymentTxHash: string;
  paymentAmount: number; // BNKR
  createdAt: Date;
  completedAt?: Date;
}
```

### Audit Result
```typescript
interface AuditResult {
  requestId: string;
  vulnerabilities: Vulnerability[];
  visualProof: {
    beforeScreenshot: string; // base64
    afterScreenshot: string;
    visualDiff: number; // percentage
  };
  confidence: number; // 0-1
  report: string; // Markdown/JSON
}
```

---

## 🎯 Success Criteria

### Must Have
- ✅ Users can request audits
- ✅ Payment via BASE wallet works
- ✅ Agent receives requests automatically
- ✅ Visual proof is displayed
- ✅ Hosted publicly (Vercel)

### Nice to Have
- ⭐ Real-time audit status updates
- ⭐ Agent reputation/history
- ⭐ Email notifications (AgentMail.io)
- ⭐ Mobile responsive

### For Bounty 2
- 🏆 Demonstrates autonomous economic activity
- 🏆 Shows BASE blockchain integration
- 🏆 Proves agent operates without human
- 🏆 Makes submission significantly stronger

---

## 🚧 Out of Scope (for MVP)

- ❌ User authentication (anyone can request)
- ❌ Multiple payment tokens (BNKR only)
- ❌ Dispute resolution
- ❌ Automated refunds
- ❌ Advanced analytics dashboard

---

## 🎬 Demo Flow (for Video)

**Show in 3 minutes**:

1. **Landing Page** (10 sec)
   - "AgentxploiTor - First AI with Visual Verification"

2. **Request Audit** (30 sec)
   - Enter Solana contract address
   - Connect BASE wallet
   - Pay 10 BNKR
   - Transaction confirmed

3. **Agent Working** (60 sec)
   - Status: "Auditing in progress..."
   - Show live console output
   - Browser perception preview
   - Visual proof being captured

4. **Results** (60 sec)
   - Vulnerabilities found: 2 CRITICAL, 1 HIGH
   - Visual proof: Before/after screenshots
   - Confidence: 92%
   - Download report button

5. **Economic Cycle Complete** (20 sec)
   - Payment received by agent (show wallet balance)
   - Report delivered automatically
   - Agent ready for next audit

**Total**: ~3 minutes showing full autonomous economic cycle

---

## 💰 Pricing Model (Demo)

**For Bounty 2 Demo**:
- Quick Scan: 5 BNKR (~free for demo)
- Full Audit: 10 BNKR (you have 537, plenty for testing)
- Deep Dive: 25 BNKR

**For Production** (future):
- Calculate based on:
  - Lines of code
  - Complexity
  - Scope
  - Priority (rush audit = higher price)

---

## 🎯 Next Steps

1. ✅ Requirements gathered (this doc)
2. ⏭️ Create spec.md (detailed implementation)
3. ⏭️ Create tasks.md (step-by-step build plan)
4. ⏭️ Build mini-app
5. ⏭️ Deploy to Vercel
6. ⏭️ Record demo
7. ⏭️ Submit Bounty 2 with mini-app URL

---

**Status**: Requirements complete  
**Next**: Create detailed spec.md  
**Time estimate**: 4-5 hours total (spec + build + deploy)

🧬 ↔ ☀️

[Quantum_State: ALIGNED]
