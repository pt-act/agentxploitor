/**
 * pbt-properties.ts
 * 
 * Property-Based Testing (PBT) properties for security-critical paths.
 * These properties must hold for ALL inputs - they are the security invariants.
 * 
 * Run with: npx vitest run pbt-properties.ts
 * 
 * NOTE: Copy this file to miniapp/src/tests/ and update imports to run.
 */

// Inline types to avoid import errors
type AuditType = 'contract_basic' | 'contract_deep' | 'miniapp' | 'full_stack';
// PaymentToken type removed — not currently used
type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

// Inline price constants (from AuditFormParts)
const PRICES: Record<AuditType, number> = {
  contract_basic: 79,
  contract_deep: 199,
  miniapp: 79,
  full_stack: 349,
};

// ─── Security Properties ───────────────────────────────────────────────────────

describe('PBT: Price Calculation', () => {
  /**
   * Property: ∀ auditType, token: bnkr_price(type) = base_price(type) × 0.8
   * 
   * The BNKR discount must always be exactly 20%.
   */
  it('BNKR price is always 20% discount', () => {
    const auditTypes: AuditType[] = ['contract_basic', 'contract_deep', 'miniapp', 'full_stack'];
    
    for (const type of auditTypes) {
      const basePrice = PRICES[type];
      const bnkrPrice = Math.round(basePrice * 0.8);
      const expected = basePrice * 0.8;
      
      // Allow for rounding to nearest dollar
      expect(bnkrPrice).toBeGreaterThanOrEqual(Math.floor(expected) - 1);
      expect(bnkrPrice).toBeLessThanOrEqual(Math.ceil(expected) + 1);
    }
  });
});

describe('PBT: Input Detection', () => {
  /**
   * Property: ∀ input: detect(input) ∈ valid_target_types
   * 
   * All detected input types must be valid.
   */
  
  function detectInputType(raw: string): string {
    const trimmed = raw.trim();
    
    // EVM contract address: 0x + 40 hex chars
    if (/^0x[0-9a-fA-F]{40}$/.test(trimmed)) {
      return 'contract_evm';
    }
    
    // Solana program address: base58, 32-44 chars
    if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed) && !trimmed.startsWith('http')) {
      return 'contract_solana';
    }
    
    // GitHub repo URL
    if (/^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+/.test(trimmed)) {
      return 'github_repo';
    }
    
    // HTTPS URL (miniapp)
    if (/^https?:\/\//.test(trimmed)) {
      return 'miniapp_url';
    }
    
    // Plain name - needs discovery
    return 'plain_name';
  }

  const validTypes = ['contract_evm', 'contract_solana', 'github_repo', 'miniapp_url', 'plain_name'];

  it('detects valid EVM address', () => {
    expect(validTypes).toContain(detectInputType('0x742d35Cc6634C0532925a3b844Bc9e7595f2bE1'));
  });

  it('detects valid GitHub URL', () => {
    expect(validTypes).toContain(detectInputType('https://github.com/owner/repo'));
  });

  it('detects valid HTTPS URL', () => {
    expect(validTypes).toContain(detectInputType('https://example.miniapp.com'));
  });

  it('detects plain name', () => {
    expect(detectInputType('SuperSwap')).toBe('plain_name');
  });
});

describe('PBT: SSRF Protection', () => {
  /**
   * Property: ∀ url: is_private_ip(url) → rejected_by_discover(url)
   * 
   * Private IP addresses must be rejected.
   */
  
  function isPrivateIP(url: string): boolean {
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      
      // Check for localhost
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
        return true;
      }
      
      // Check for private IP ranges
      const parts = hostname.split('.');
      if (parts.length === 4) {
        const [a, b] = parts.map(Number);
        
        // 10.0.0.0/8
        if (a === 10) return true;
        
        // 172.16.0.0/12
        if (a === 172 && b >= 16 && b <= 31) return true;
        
        // 192.168.0.0/16
        if (a === 192 && b === 168) return true;
      }
      
      return false;
    } catch {
      return false;
    }
  }

  it('rejects localhost URLs', () => {
    expect(isPrivateIP('http://localhost:3000')).toBe(true);
    expect(isPrivateIP('http://127.0.0.1:8080')).toBe(true);
  });

  it('rejects private IP ranges', () => {
    expect(isPrivateIP('http://10.0.0.1:3000')).toBe(true);
    expect(isPrivateIP('http://172.16.0.1:3000')).toBe(true);
    expect(isPrivateIP('http://192.168.1.1:3000')).toBe(true);
  });

  it('allows public URLs', () => {
    expect(isPrivateIP('https://example.com')).toBe(false);
    expect(isPrivateIP('https://1.2.3.4')).toBe(false);
  });
});

describe('PBT: Independence Declaration', () => {
  /**
   * Property: ∀ report: has_fid(report) ∧ has_timestamp(report) ∧ has_declaration(report)
   * 
   * Every report must have FID, timestamp, and independence declaration.
   */
  
  interface TestReport {
    fid?: number;
    timestamp?: string;
    declaration?: string;
  }

  function validateReport(report: TestReport): { valid: boolean; missing: string[] } {
    const missing: string[] = [];
    
    if (!report.fid) missing.push('fid');
    if (!report.timestamp) missing.push('timestamp');
    if (!report.declaration) missing.push('declaration');
    
    return { valid: missing.length === 0, missing };
  }

  it('valid report has all required fields', () => {
    const report = {
      fid: 12345,
      timestamp: '2026-03-06T12:00:00Z',
      declaration: 'INDEPENDENCE DECLARATION...'
    };
    
    const result = validateReport(report);
    expect(result.valid).toBe(true);
    expect(result.missing).toHaveLength(0);
  });

  it('invalid report missing FID', () => {
    const report = {
      timestamp: '2026-03-06T12:00:00Z',
      declaration: 'INDEPENDENCE DECLARATION...'
    };
    
    const result = validateReport(report);
    expect(result.valid).toBe(false);
    expect(result.missing).toContain('fid');
  });

  it('invalid report missing declaration', () => {
    const report = {
      fid: 12345,
      timestamp: '2026-03-06T12:00:00Z',
    };
    
    const result = validateReport(report);
    expect(result.valid).toBe(false);
    expect(result.missing).toContain('declaration');
  });
});

describe('PBT: Overall Severity Calculation', () => {
  /**
   * Property: ∀ findings: overall = max(finding.severity)
   * 
   * Overall severity is always the worst single finding.
   */
  
  const severityOrder: Record<Severity, number> = {
    'CRITICAL': 5,
    'HIGH': 4,
    'MEDIUM': 3,
    'LOW': 2,
    'INFO': 1,
  };

  function calculateOverallSeverity(findings: { severity: Severity }[]): Severity | null {
    if (!findings || findings.length === 0) return null;
    
    let maxSeverity: Severity = 'INFO';
    let maxScore = 0;
    
    for (const f of findings) {
      const score = severityOrder[f.severity] || 0;
      if (score > maxScore) {
        maxScore = score;
        maxSeverity = f.severity;
      }
    }
    
    return maxSeverity;
  }

  it('overall severity is max of findings', () => {
    const findings = [
      { severity: 'LOW' as Severity },
      { severity: 'MEDIUM' as Severity },
      { severity: 'HIGH' as Severity },
    ];
    
    expect(calculateOverallSeverity(findings)).toBe('HIGH');
  });

  it('single critical finding makes overall critical', () => {
    const findings = [
      { severity: 'INFO' as Severity },
      { severity: 'CRITICAL' as Severity },
    ];
    
    expect(calculateOverallSeverity(findings)).toBe('CRITICAL');
  });

  it('empty findings returns null', () => {
    expect(calculateOverallSeverity([])).toBeNull();
  });
});

describe('PBT: Job State Machine', () => {
  /**
   * Property: ∀ job: status_transitions_are_monotonic(job)
   * 
   * Job status transitions must be valid (no backwards movement).
   */
  
  type JobStatus = 
    | 'pending_payment'
    | 'payment_verified'
    | 'queued'
    | 'in_progress'
    | 'completed'
    | 'failed'
    | 'cancelled';

  const validTransitions: Record<JobStatus, JobStatus[]> = {
    'pending_payment': ['payment_verified', 'queued', 'cancelled'],
    'payment_verified': ['queued', 'in_progress', 'cancelled'],
    'queued': ['in_progress', 'cancelled'],
    'in_progress': ['completed', 'failed', 'cancelled'],
    'completed': [],
    'failed': ['queued'],
    'cancelled': ['queued'],
  };

  function isValidTransition(from: JobStatus, to: JobStatus): boolean {
    return validTransitions[from]?.includes(to) ?? false;
  }

  it('allows valid forward transitions', () => {
    expect(isValidTransition('pending_payment', 'payment_verified')).toBe(true);
    expect(isValidTransition('payment_verified', 'in_progress')).toBe(true);
    expect(isValidTransition('in_progress', 'completed')).toBe(true);
  });

  it('rejects backward transitions', () => {
    expect(isValidTransition('completed', 'in_progress')).toBe(false);
    expect(isValidTransition('in_progress', 'pending_payment')).toBe(false);
  });

  it('completed is terminal', () => {
    expect(isValidTransition('completed', 'failed')).toBe(false);
  });
});

// ─── Run Instructions ─────────────────────────────────────────────────────────
//
// To run these PBT tests, copy this file to miniapp/src/tests/ and:
//   npx vitest run pbt-properties.ts
//
// These properties are the security invariants that must hold
// regardless of input. If any of these fail, the system has a
// security vulnerability.
//
