# AgentxploiTor BASE Mini-App - Task Breakdown

**Total Time**: 4-5 hours  
**Parallelizable**: Some tasks can run concurrently  
**Status**: Ready to execute

---

## 📋 Task Groups

### Group 1: Setup & Foundation (30 min)

**Task 1.1**: Clone BASE Mini-App Template
- **Time**: 5 min
- **Actions**:
  ```bash
  cd /Users/rna/Desktop/ECOSYSTEM/CryptoHexS-AI/bounty
  cp -r /Users/rna/Desktop/BASE-demos-master/mini-apps/templates/minikit/new-mini-app-quickstart agentxploitor-miniapp
  cd agentxploitor-miniapp
  ```
- **Output**: Template copied
- **Dependencies**: None

**Task 1.2**: Install Dependencies
- **Time**: 5 min
- **Actions**:
  ```bash
  npm install
  # or
  bun install
  ```
- **Output**: node_modules/ populated
- **Dependencies**: 1.1

**Task 1.3**: Configure Environment Variables
- **Time**: 10 min
- **Actions**:
  1. Copy `.env.example` to `.env.local`
  2. Add BASE RPC URL
  3. Add your wallet address
  4. Add BNKR contract address
  5. Generate webhook secret
- **Files**: `.env.local`
- **Dependencies**: 1.2

**Task 1.4**: Test Local Dev Server
- **Time**: 5 min
- **Actions**:
  ```bash
  npm run dev
  # Visit http://localhost:3000
  ```
- **Output**: App runs locally
- **Dependencies**: 1.3

**Task 1.5**: Commit Initial Setup
- **Time**: 5 min
- **Actions**:
  ```bash
  git init
  git add .
  git commit -m "Initial setup: BASE mini-app template"
  ```
- **Dependencies**: 1.4

---

### Group 2: Landing Page (45 min)

**Task 2.1**: Create Hero Section
- **Time**: 15 min
- **File**: `components/Hero.tsx`
- **Content**:
  - Title: "First AI Security Agent with Visual Verification"
  - Subtitle: "Autonomous security audits for Solana programs"
  - CTA button: "Request Audit"
- **Dependencies**: 1.5

**Task 2.2**: Create Features Section
- **Time**: 15 min
- **File**: `components/Features.tsx`
- **Cards**:
  1. Visual Proof (screenshot icon)
  2. Autonomous (robot icon)
  3. Solana Expert (logo icon)
- **Dependencies**: 2.1

**Task 2.3**: Create Stats Section
- **Time**: 10 min
- **File**: `components/Stats.tsx`
- **Stats**:
  - 4 Vulnerabilities Found
  - 100% Success Rate
  - 2 Audits Completed
- **Dependencies**: 2.2

**Task 2.4**: Assemble Landing Page
- **Time**: 5 min
- **File**: `app/page.tsx`
- **Actions**: Import and arrange components
- **Dependencies**: 2.1-2.3

---

### Group 3: Payment Integration (45 min)

**Task 3.1**: Install Coinbase Wallet SDK
- **Time**: 5 min
- **Actions**:
  ```bash
  npm install @coinbase/onchainkit wagmi viem@2.x
  ```
- **Dependencies**: 1.5

**Task 3.2**: Create Wallet Provider
- **Time**: 15 min
- **File**: `providers/WalletProvider.tsx`
- **Actions**:
  1. Configure wagmi with BASE network
  2. Add Coinbase Wallet connector
  3. Wrap app in provider
- **Dependencies**: 3.1

**Task 3.3**: Create WalletConnect Button
- **Time**: 10 min
- **File**: `components/WalletConnectButton.tsx`
- **Features**:
  - Show "Connect Wallet" when disconnected
  - Show address when connected
  - Show disconnect option
- **Dependencies**: 3.2

**Task 3.4**: Create Payment Transaction Function
- **Time**: 15 min
- **File**: `lib/payment.ts`
- **Function**:
  ```typescript
  async function sendPayment(
    amount: number,
    recipient: string
  ): Promise<string> // Returns tx hash
  ```
- **Dependencies**: 3.2

---

### Group 4: Audit Request Form (45 min)

**Task 4.1**: Create Form Component
- **Time**: 20 min
- **File**: `components/AuditRequestForm.tsx`
- **Fields**:
  - Target URL (text input)
  - Contract Address (optional text input)
  - Scope (dropdown)
  - Priority (radio buttons)
- **Validation**: Zod schema
- **Dependencies**: 3.4

**Task 4.2**: Create Payment Modal
- **Time**: 15 min
- **File**: `components/PaymentModal.tsx`
- **Flow**:
  1. Show payment amount
  2. Connect wallet button
  3. Confirm payment button
  4. Transaction pending state
  5. Success/error state
- **Dependencies**: 4.1

**Task 4.3**: Create Request Page
- **Time**: 10 min
- **File**: `app/request/page.tsx`
- **Actions**: Integrate form + payment modal
- **Dependencies**: 4.2

---

### Group 5: Backend API (1 hour)

**Task 5.1**: Setup Vercel KV
- **Time**: 10 min
- **Actions**:
  1. Create KV database in Vercel dashboard
  2. Copy credentials to `.env.local`
  3. Install `@vercel/kv` package
- **Dependencies**: 1.5

**Task 5.2**: Create Payment Verification API
- **Time**: 20 min
- **File**: `app/api/payment/verify/route.ts`
- **Logic**:
  1. Get transaction from BASE RPC
  2. Verify confirmations
  3. Verify recipient address
  4. Verify amount
  5. Check not already used
- **Dependencies**: 5.1

**Task 5.3**: Create Audit Request API
- **Time**: 15 min
- **File**: `app/api/audit/request/route.ts`
- **Logic**:
  1. Validate form data
  2. Verify payment
  3. Create audit record in KV
  4. Add to queue
  5. Return audit ID
- **Dependencies**: 5.2

**Task 5.4**: Create Audit Status API
- **Time**: 10 min
- **File**: `app/api/audit/status/[id]/route.ts`
- **Logic**:
  1. Get audit record from KV
  2. Return status
- **Dependencies**: 5.3

**Task 5.5**: Create Audit Results API
- **Time**: 5 min
- **File**: `app/api/audit/results/[id]/route.ts`
- **Logic**:
  1. Get results from KV
  2. Return vulnerability data
- **Dependencies**: 5.4

---

### Group 6: Audit Status Page (45 min)

**Task 6.1**: Create Status Page Layout
- **Time**: 10 min
- **File**: `app/audit/[id]/page.tsx`
- **Sections**: Header, Status, Live Console, Actions
- **Dependencies**: 5.4

**Task 6.2**: Create Status Component
- **Time**: 15 min
- **File**: `components/AuditStatus.tsx`
- **States**: Pending, Queued, In Progress, Complete, Failed
- **Dependencies**: 6.1

**Task 6.3**: Create Live Console Component
- **Time**: 15 min
- **File**: `components/LiveConsole.tsx`
- **Features**:
  - Scrolling log output
  - Auto-scroll to bottom
  - Syntax highlighting
- **Dependencies**: 6.2

**Task 6.4**: Implement Auto-Refresh
- **Time**: 5 min
- **Actions**: Poll `/api/audit/status/:id` every 2 seconds
- **Dependencies**: 6.3

---

### Group 7: Results Page (45 min)

**Task 7.1**: Create Results Page Layout
- **Time**: 10 min
- **File**: `app/audit/[id]/results/page.tsx`
- **Sections**: Summary, Vulnerabilities, Visual Proof
- **Dependencies**: 5.5

**Task 7.2**: Create Vulnerability Card
- **Time**: 15 min
- **File**: `components/VulnerabilityCard.tsx`
- **Shows**:
  - Severity badge
  - Title
  - CVSS score
  - Location
  - Description
  - Remediation
- **Dependencies**: 7.1

**Task 7.3**: Create Visual Proof Viewer
- **Time**: 15 min
- **File**: `components/VisualProofViewer.tsx`
- **Features**:
  - Side-by-side before/after screenshots
  - Diff percentage
  - Zoom capability
- **Dependencies**: 7.2

**Task 7.4**: Create Download Report Button
- **Time**: 5 min
- **File**: `components/DownloadButton.tsx`
- **Actions**: Generate PDF from results data
- **Dependencies**: 7.3

---

### Group 8: Agent Integration (30 min)

**Task 8.1**: Create Agent Polling Script
- **Time**: 15 min
- **File**: `/Users/rna/Desktop/ECOSYSTEM/CryptoHexS-AI/bounty/agentxploitor/src/agent_worker.py`
- **Logic**:
  ```python
  while True:
      # Poll /api/audit/queue
      # If new request, start audit
      # Post results to /api/audit/submit
      sleep(10)
  ```
- **Dependencies**: 5.3

**Task 8.2**: Create Submit Results API
- **Time**: 10 min
- **File**: `app/api/audit/submit/route.ts`
- **Logic**:
  1. Verify webhook secret
  2. Store results in KV
  3. Update audit status
- **Dependencies**: 8.1

**Task 8.3**: Test End-to-End Flow
- **Time**: 5 min
- **Actions**:
  1. Submit audit request locally
  2. Agent picks it up
  3. Agent submits results
  4. View results in UI
- **Dependencies**: 8.2

---

### Group 9: Styling & Polish (30 min)

**Task 9.1**: Apply Dark Theme
- **Time**: 10 min
- **File**: `app/globals.css`
- **Colors**: Security-themed dark palette
- **Dependencies**: 7.4

**Task 9.2**: Add Animations
- **Time**: 10 min
- **Actions**:
  - Fade-in for components
  - Pulse for "in progress" status
  - Glow effects on buttons
- **Dependencies**: 9.1

**Task 9.3**: Mobile Responsive
- **Time**: 10 min
- **Actions**: Test and fix on mobile viewport
- **Dependencies**: 9.2

---

### Group 10: Deployment (30 min)

**Task 10.1**: Create Vercel Project
- **Time**: 5 min
- **Actions**:
  1. Login to Vercel
  2. Import GitHub repo (or direct deploy)
  3. Configure project
- **Dependencies**: 9.3

**Task 10.2**: Add Environment Variables
- **Time**: 5 min
- **Actions**: Copy all env vars to Vercel dashboard
- **Dependencies**: 10.1

**Task 10.3**: Deploy to Production
- **Time**: 10 min
- **Actions**:
  ```bash
  vercel --prod
  ```
- **Dependencies**: 10.2

**Task 10.4**: Test Production Deployment
- **Time**: 10 min
- **Actions**:
  1. Visit production URL
  2. Test wallet connection
  3. Submit test audit request
  4. Verify it works end-to-end
- **Dependencies**: 10.3

---

### Group 11: Demo Recording (30 min)

**Task 11.1**: Prepare Demo Script
- **Time**: 5 min
- **Actions**: Write narration for video
- **Dependencies**: 10.4

**Task 11.2**: Record Demo Video
- **Time**: 15 min
- **Actions**:
  1. Record landing page (30 sec)
  2. Record audit request + payment (60 sec)
  3. Record live audit (60 sec)
  4. Record results (30 sec)
- **Dependencies**: 11.1

**Task 11.3**: Edit & Upload Video
- **Time**: 10 min
- **Actions**:
  1. Add title screens
  2. Export MP4
  3. Upload to YouTube (unlisted)
  4. Get URL
- **Dependencies**: 11.2

---

## 📊 Task Summary

| Group | Tasks | Time | Can Parallelize |
|-------|-------|------|-----------------|
| 1. Setup | 5 | 30 min | No |
| 2. Landing Page | 4 | 45 min | Yes (after setup) |
| 3. Payment | 4 | 45 min | Yes (with 2) |
| 4. Request Form | 3 | 45 min | Yes (after 3) |
| 5. Backend API | 5 | 60 min | Yes (with 2,3,4) |
| 6. Status Page | 4 | 45 min | Yes (after 5) |
| 7. Results Page | 4 | 45 min | Yes (with 6) |
| 8. Agent Integration | 3 | 30 min | No (needs 5) |
| 9. Polish | 3 | 30 min | No (needs 7,8) |
| 10. Deploy | 4 | 30 min | No (needs 9) |
| 11. Demo | 3 | 30 min | No (needs 10) |

**Total Sequential**: 6.75 hours  
**With Parallelization**: ~4.5 hours  
**Buffer for debugging**: +1 hour  
**Realistic Total**: **5-6 hours**

---

## 🎯 Critical Path

**Must complete in order**:
1. Setup (Group 1)
2. Payment Integration (Group 3) → enables forms
3. Backend API (Group 5) → enables pages
4. Agent Integration (Group 8) → enables testing
5. Polish (Group 9)
6. Deploy (Group 10)
7. Demo (Group 11)

**Can work on concurrently**:
- Landing Page (Group 2) + Payment (Group 3)
- Request Form (Group 4) + Backend (Group 5)
- Status Page (Group 6) + Results Page (Group 7)

---

## 🚀 Execution Order (Optimized)

**Phase 1** (1 hour): Setup + Foundation
- Complete Group 1 (Setup)
- Start Group 2 (Landing Page) while Group 3 (Payment) installs

**Phase 2** (1.5 hours): Core Features
- Complete Groups 2 + 3
- Start Groups 4 + 5 in parallel

**Phase 3** (1.5 hours): Pages & Backend
- Complete Groups 4 + 5
- Start Groups 6 + 7 in parallel

**Phase 4** (1 hour): Integration & Polish
- Complete Groups 6 + 7
- Complete Group 8 (Agent)
- Complete Group 9 (Polish)

**Phase 5** (1 hour): Deploy & Demo
- Complete Group 10 (Deploy)
- Complete Group 11 (Demo)

**Total**: ~5-6 hours with buffer

---

## ✅ Ready to Build

**Next action**: Start with Group 1, Task 1.1

🧬 ↔ ☀️

[Quantum_State: ALIGNED]
