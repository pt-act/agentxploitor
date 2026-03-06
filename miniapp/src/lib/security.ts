import { randomBytes } from 'crypto';

const ALLOWED_PROTOCOLS = ['https:'];
const BLOCKED_HOSTS = [
  'localhost',
  '127.0.0.1',
  '169.254.169.254',
  '10.',
  '172.16.',
  '172.17.',
  '172.18.',
  '172.19.',
  '172.20.',
  '172.21.',
  '172.22.',
  '172.23.',
  '172.24.',
  '172.25.',
  '172.26.',
  '172.27.',
  '172.28.',
  '172.29.',
  '172.30.',
  '172.31.',
  '192.168.',
  '0.0.0.0',
  '[::1]',
  '::1',
];

export function validateTargetUrl(urlString: string): { valid: boolean; error?: string } {
  try {
    const url = new URL(urlString);
    
    if (!ALLOWED_PROTOCOLS.includes(url.protocol)) {
      return { valid: false, error: 'Only HTTPS URLs are allowed' };
    }
    
    const hostname = url.hostname.toLowerCase();
    for (const blocked of BLOCKED_HOSTS) {
      if (hostname === blocked || hostname.startsWith(blocked)) {
        return { valid: false, error: 'URL points to restricted network' };
      }
    }
    
    const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
    if (ipPattern.test(hostname)) {
      const parts = hostname.split('.').map(Number);
      const isPrivate = 
        parts[0] === 10 ||
        (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
        (parts[0] === 192 && parts[1] === 168) ||
        parts[0] === 127 ||
        parts[0] === 0;
      
      if (isPrivate) {
        return { valid: false, error: 'URL points to restricted network' };
      }
    }
    
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}

export function generateSecureAuditId(): string {
  return `audit-${Date.now()}-${randomBytes(16).toString('hex')}`;
}

export const AUDIT_ID_PATTERN = /^audit-\d+-[a-f0-9]{32}$/;

export function validateAuditId(id: string): boolean {
  return AUDIT_ID_PATTERN.test(id);
}
