# Security Deployment Checklist

## Pre-Deployment

### Environment Configuration
- [ ] Copy `.env.local.example` to `.env.local`
- [ ] Set `AGENT_WEBHOOK_SECRET` to a securely generated value (32+ bytes random)
- [ ] Set `NEXT_PUBLIC_TREASURY_ADDRESS` to your receiving wallet
- [ ] Set `NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS` to the BNKR token contract
- [ ] Set `BROWSER_PERCEPTION_PATH` or `AGENT_BROWSER_CLI` if using custom browser (defaults to `agent-browser/`)
- [ ] Never commit `.env.local` to version control

### Secrets Management
- [ ] Rotate any secrets that were previously committed
- [ ] Use environment variables for all sensitive values
- [ ] Set up secrets management in deployment platform (Vercel, etc.)
- [ ] Audit git history for accidentally committed secrets

### Authentication
- [ ] Verify Farcaster QuickAuth domain is correctly configured
- [ ] Test authentication flow end-to-end
- [ ] Ensure JWT tokens are not logged in plaintext
- [ ] Verify Authorization header is required on protected endpoints

### Network Security
- [ ] Verify SSRF validation blocks internal IPs
- [ ] Test rate limiting is working (`/api/*` endpoints)
- [ ] Confirm HTTPS is enforced in production
- [ ] Review Content Security Policy headers

## API Security

### Input Validation
- [ ] All user inputs are validated (targetUrl, wallet addresses, etc.)
- [ ] Audit IDs are validated against regex pattern
- [ ] Request body size limits are enforced
- [ ] Zod schemas are applied to all API inputs

### Rate Limiting
- [ ] Rate limiting middleware is active on `/api/audit/*`
- [ ] Configure limits appropriate for your traffic
- [ ] Set up monitoring for rate limit violations

### Authentication Endpoints
- [ ] `/api/audit/request` requires Bearer token
- [ ] Invalid tokens return 401, not 500
- [ ] Error messages don't reveal internal details
- [ ] Token expiration is handled gracefully

## Agent Security

### Execution Isolation
- [ ] Run agent in isolated environment (container, sandbox)
- [ ] Limit filesystem access to output directory only
- [ ] Restrict network access to required endpoints only
- [ ] Disable real fund movements (safety constraints)

### Browser Perception
- [ ] `BROWSER_PERCEPTION_PATH` points to valid module
- [ ] Browser instances are properly cleaned up
- [ ] Screenshots are stored in configurable output directory
- [ ] Proof artifacts are cleaned up after retention period

### Analyzer Tools
- [ ] Analyzer binaries are from trusted sources
- [ ] Analyzer paths are configurable via environment
- [ ] Analyzer output is parsed safely
- [ ] External tool errors are handled gracefully

## Data Protection

### Logging
- [ ] JWTs are redacted from logs
- [ ] Wallet addresses are redacted from logs
- [ ] Sensitive request parameters are not logged
- [ ] Error logs don't include stack traces in production

### Storage
- [ ] Job data is persisted securely
- [ ] Report JSON files are stored in protected location
- [ ] Proof screenshots are not publicly accessible
- [ ] Old artifacts are cleaned up on schedule

### Payment Verification
- [ ] Payment transactions are verified on-chain
- [ ] Minimum amount requirements are enforced
- [ ] Recipient address matches expected treasury
- [ ] Transaction confirmations are checked

## Production Deployment

### Vercel Deployment
- [ ] Environment variables are set in Vercel dashboard
- [ ] KV (Redis) is configured for job storage
- [ ] Function timeouts are appropriate for agent work
- [ ] Region is set appropriately for latency

### Monitoring
- [ ] Error tracking is configured (Sentry, etc.)
- [ ] API endpoint monitoring is set up
- [ ] Job queue depth is monitored
- [ ] Agent execution time is tracked

### Backup & Recovery
- [ ] Job queue persistence is configured
- [ ] Report storage backup strategy is defined
- [ ] Session recovery for interrupted audits is tested
- [ ] Rollback procedure is documented

## Post-Deployment

### Security Testing
- [ ] Run automated security scanner against deployed API
- [ ] Test SSRF protection with internal IPs
- [ ] Verify rate limiting under load
- [ ] Test authentication bypass attempts

### Incident Response
- [ ] Secret rotation procedure is documented
- [ ] Emergency contact information is available
- [ ] Rollback process is tested
- [ ] Log access is available for investigation

### Maintenance
- [ ] Dependencies are regularly updated
- [ ] Security advisories are monitored
- [ ] Access logs are reviewed periodically
- [ ] API keys are rotated on schedule

---

## Quick Security Audit Commands

```bash
# Check for exposed secrets
grep -r "SECRET\|KEY\|TOKEN" --include="*.ts" --include="*.tsx" --include="*.js"

# Verify .env.local is in .gitignore
grep ".env.local" .gitignore

# Check for hardcoded addresses
grep -r "0x[0-9a-fA-F]{40}" --include="*.ts" --include="*.tsx"

# Run security tests
npm run test

# Type check
npx tsc --noEmit
```

## Contact

For security issues, please contact the development team privately.
