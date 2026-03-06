/**
 * Tests for Security Utilities
 */

import { describe, it, expect } from 'vitest';
import {
  validateTargetUrl,
  generateSecureAuditId,
  AUDIT_ID_PATTERN,
  validateAuditId,
} from '../security';

describe('validateTargetUrl', () => {
  describe('valid URLs', () => {
    it('accepts valid HTTPS URLs', () => {
      const result = validateTargetUrl('https://example.com');
      expect(result.valid).toBe(true);
    });

    it('accepts HTTPS URLs with paths', () => {
      const result = validateTargetUrl('https://example.com/path/to/page');
      expect(result.valid).toBe(true);
    });

    it('accepts HTTPS URLs with query parameters', () => {
      const result = validateTargetUrl('https://example.com/page?param=value');
      expect(result.valid).toBe(true);
    });
  });

  describe('blocked protocols', () => {
    it('rejects HTTP URLs', () => {
      const result = validateTargetUrl('http://example.com');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('HTTPS');
    });

    it('rejects file:// URLs', () => {
      const result = validateTargetUrl('file:///etc/passwd');
      expect(result.valid).toBe(false);
    });

    it('rejects ftp:// URLs', () => {
      const result = validateTargetUrl('ftp://example.com/file');
      expect(result.valid).toBe(false);
    });
  });

  describe('blocked internal hosts', () => {
    it('rejects localhost', () => {
      const result = validateTargetUrl('https://localhost:3000');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('restricted');
    });

    it('rejects 127.0.0.1', () => {
      const result = validateTargetUrl('https://127.0.0.1:8080');
      expect(result.valid).toBe(false);
    });

    it('rejects 0.0.0.0', () => {
      const result = validateTargetUrl('https://0.0.0.0');
      expect(result.valid).toBe(false);
    });

    it('rejects AWS metadata endpoint', () => {
      const result = validateTargetUrl('https://169.254.169.254/latest/meta-data');
      expect(result.valid).toBe(false);
    });
  });

  describe('blocked private IP ranges', () => {
    it('rejects 10.x.x.x', () => {
      const result = validateTargetUrl('https://10.0.0.1');
      expect(result.valid).toBe(false);
    });

    it('rejects 172.16.x.x - 172.31.x.x', () => {
      const result = validateTargetUrl('https://172.16.0.1');
      expect(result.valid).toBe(false);
    });

    it('rejects 192.168.x.x', () => {
      const result = validateTargetUrl('https://192.168.1.1');
      expect(result.valid).toBe(false);
    });

    it('rejects IPv6 localhost', () => {
      const result = validateTargetUrl('https://[::1]');
      expect(result.valid).toBe(false);
    });
  });

  describe('invalid URLs', () => {
    it('rejects malformed URLs', () => {
      const result = validateTargetUrl('not-a-url');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid URL');
    });

    it('rejects empty string', () => {
      const result = validateTargetUrl('');
      expect(result.valid).toBe(false);
    });
  });
});

describe('generateSecureAuditId', () => {
  it('generates unique IDs', () => {
    const id1 = generateSecureAuditId();
    const id2 = generateSecureAuditId();
    
    expect(id1).not.toBe(id2);
  });

  it('generates IDs with correct format', () => {
    const id = generateSecureAuditId();
    
    expect(id).toMatch(/^audit-\d+-[a-f0-9]{32}$/);
  });

  it('includes timestamp', () => {
    const before = Date.now();
    const id = generateSecureAuditId();
    const after = Date.now();
    
    const timestampMatch = id.match(/^audit-(\d+)/);
    expect(timestampMatch).not.toBeNull();
    
    const timestamp = parseInt(timestampMatch![1], 10);
    expect(timestamp).toBeGreaterThanOrEqual(before);
    expect(timestamp).toBeLessThanOrEqual(after);
  });

  it('includes 32-character hex random component', () => {
    const id = generateSecureAuditId();
    const parts = id.split('-');
    
    expect(parts.length).toBe(3);
    expect(parts[2]).toMatch(/^[a-f0-9]{32}$/);
  });
});

describe('AUDIT_ID_PATTERN', () => {
  it('matches valid audit IDs', () => {
    const validId = 'audit-1234567890-abcdef1234567890abcdef123456789012';
    expect(AUDIT_ID_PATTERN.test(validId)).toBe(true);
  });

  it('rejects IDs without audit prefix', () => {
    const invalidId = 'job-1234567890-abcdef1234567890abcdef123456789012';
    expect(AUDIT_ID_PATTERN.test(invalidId)).toBe(false);
  });

  it('rejects IDs with wrong hex length', () => {
    const invalidId = 'audit-1234567890-abcdef';
    expect(AUDIT_ID_PATTERN.test(invalidId)).toBe(false);
  });

  it('rejects IDs with uppercase hex', () => {
    const invalidId = 'audit-1234567890-ABCDEF1234567890ABCDEF123456789012';
    expect(AUDIT_ID_PATTERN.test(invalidId)).toBe(false);
  });
});

describe('validateAuditId', () => {
  it('returns true for valid audit IDs', () => {
    const validId = 'audit-1234567890-abcdef1234567890abcdef123456789012';
    expect(validateAuditId(validId)).toBe(true);
  });

  it('returns false for invalid audit IDs', () => {
    expect(validateAuditId('invalid-id')).toBe(false);
    expect(validateAuditId('audit-123-short')).toBe(false);
    expect(validateAuditId('')).toBe(false);
  });

  it('rejects SQL injection attempts', () => {
    expect(validateAuditId("audit-123'; DROP TABLE audits;--")).toBe(false);
  });

  it('rejects path traversal attempts', () => {
    expect(validateAuditId('../../../etc/passwd')).toBe(false);
  });
});
