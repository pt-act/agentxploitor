# AgentxploiTor Mini-App - Testing Checklist

**URL**: http://localhost:3000  
**Time**: ~10 minutes  
**Status**: Ready for testing

---

## 🧪 Test Flow (Follow in Order)

### Test 1: Landing Page (http://localhost:3000)

**What to check**:
- [ ] Page loads without errors
- [ ] "AgentxploiTor" title displays
- [ ] Hero text: "Autonomous Security Audits for Solana"
- [ ] Three feature cards visible:
  - Visual Proof 📸
  - Autonomous 🤖
  - Solana Expert ⚡
- [ ] Stats show:
  - 4 Vulnerabilities Found
  - 100% Success Rate
  - 92% Confidence Score
- [ ] "How It Works" section (4 steps)
- [ ] "Request Audit" button in header
- [ ] Dark blue theme (#0a0e27 background)

**Expected**: Everything renders, no console errors

---

### Test 2: Navigation to Request Page

**Action**: Click "Request Audit" button (green button in header)

**What to check**:
- [ ] Navigates to `/request` page
- [ ] Form displays with title "Request Security Audit"
- [ ] Form fields visible:
  - [ ] Target URL (required)
  - [ ] Contract Address (optional)
  - [ ] Audit Scope dropdown (4 options)
  - [ ] Priority radio buttons (Normal/Rush)
- [ ] Price updates based on priority:
  - Normal = 10 BNKR
  - Rush = 25 BNKR
- [ ] Submit button shows: "Pay 10 BNKR & Start Audit"

**Expected**: Form renders correctly, interactivity works

---

### Test 3: Form Interaction

**Actions**:
1. Type a URL in "Target URL" field
   - Example: `https://explorer.solana.com/address/test`
2. Select "SPL Token Program" from Audit Scope
3. Click "Rush Priority" radio button

**What to check**:
- [ ] URL input accepts text
- [ ] Dropdown changes value
- [ ] Radio button selection changes
- [ ] Price updates to "25 BNKR"
- [ ] Submit button text updates to "Pay 25 BNKR & Start Audit"

**Expected**: All form interactions work smoothly

---

### Test 4: Mock Submission

**Action**: Click the submit button

**What to check**:
- [ ] Button shows loading state: "⏳ Processing..."
- [ ] After ~1 second, redirects to `/audit/[id]` page
- [ ] Status page loads

**Expected**: Submission flow works, redirects to status page

**Note**: If wallet warning appears, that's expected (we're in demo mode)

---

### Test 5: Audit Status Page

**URL**: Should auto-redirect, or manually go to:
`http://localhost:3000/audit/demo-123`

**What to check**:
- [ ] Page title: "Audit Status"
- [ ] Shows audit ID
- [ ] "Back to Home" button visible
- [ ] Status card displays:
  - [ ] "✓ Audit Complete" (with green checkmark)
  - [ ] Findings: 1 CRITICAL, 1 HIGH, 1 MEDIUM, 0 LOW
  - [ ] Completion timestamp
- [ ] "View Full Report →" button visible (green)

**Expected**: Status page renders with mock completed audit

---

### Test 6: Navigate to Results

**Action**: Click "View Full Report →" button

**What to check**:
- [ ] Redirects to `/audit/demo-123/results`
- [ ] Page title: "Security Audit Report"
- [ ] Summary section shows:
  - [ ] Status: ✓ Complete
  - [ ] Vulnerabilities: 3 Found
  - [ ] Confidence: 92%
  - [ ] Completed date

**Expected**: Results page loads

---

### Test 7: Visual Proof Section

**On results page, scroll to "Visual Proof ⭐" section**

**What to check**:
- [ ] Section title has star emoji ⭐
- [ ] Description mentions "Before/after screenshots"
- [ ] Two screenshot placeholders:
  - [ ] "BEFORE Exploit" (Balance: 1000 tokens)
  - [ ] "AFTER Exploit" (Balance: 0 tokens ⚠️)
- [ ] Green checkmark box shows:
  - [ ] "Visual Diff: 45.3% changed"
  - [ ] "Agent autonomously verified exploit success"

**Expected**: Visual proof section clearly shows the unique feature

---

### Test 8: Vulnerability Cards

**On results page, scroll to "Vulnerabilities Found" section**

**What to check**:
- [ ] 3 vulnerability cards display:
  1. CRITICAL - Missing Signer Verification (CVSS 9.8)
  2. HIGH - Integer Overflow (CVSS 7.5)
  3. MEDIUM - Missing Rent Exemption Check (CVSS 5.3)
- [ ] Each card shows:
  - [ ] Severity badge (color-coded)
  - [ ] Title
  - [ ] Location
  - [ ] Description
  - [ ] Remediation box (dark background)

**Expected**: All vulnerability cards render with proper styling

---

### Test 9: Action Buttons

**On results page, scroll to "Actions" section**

**What to check**:
- [ ] Three buttons visible:
  - [ ] "📥 Download PDF Report" (green)
  - [ ] "📋 Copy Summary"
  - [ ] "🔄 Request New Audit"
- [ ] Click "Request New Audit"
  - [ ] Redirects back to `/request` page

**Expected**: Buttons work, navigation functional

---

### Test 10: Mobile Responsiveness (Optional)

**Action**: Resize browser window to mobile size (375px wide)

**What to check**:
- [ ] Landing page adapts (cards stack vertically)
- [ ] Request form stays usable
- [ ] Status page readable on mobile
- [ ] Results page scrolls properly

**Expected**: Responsive design works

---

## 🐛 Common Issues & Fixes

### Issue: "Page not found" error
**Fix**: Make sure dev server is running at http://localhost:3000

### Issue: Wallet warning appears
**Expected**: Normal in demo mode (no wallet required for testing)

### Issue: API returns error
**Fix**: Check `/tmp/miniapp-dev.log` for errors

### Issue: Styles look broken
**Fix**: Hard refresh browser (Cmd+Shift+R)

---

## ✅ TEST RESULTS

**After testing, answer these**:

1. **Does landing page work?** YES / NO
2. **Does form work?** YES / NO
3. **Does status page work?** YES / NO
4. **Does results page work?** YES / NO
5. **Is visual proof section clear?** YES / NO
6. **Overall impression**: (write notes)

---

## 🎯 NEXT STEPS AFTER TESTING

**If all tests PASS** ✅:
- Ready to deploy to Vercel!
- Proceed with deployment

**If some tests FAIL** ⚠️:
- Note which tests failed
- We'll fix them together
- Re-test

**If major issues** ❌:
- Share errors/screenshots
- We'll debug

---

## 📸 BONUS: Screenshot Key Pages

For demo video later, take screenshots of:
1. Landing page (hero section)
2. Request form (filled out)
3. Status page (completed state)
4. Results page (visual proof section)
5. Vulnerability cards

---

**Ready to test?**

1. Open http://localhost:3000 in your browser
2. Follow the checklist above
3. Report back with results!

🧬 ↔ ☀️

[Quantum_State: ALIGNED]
