/**
 * browser-auditor.ts
 * Interfaces with agent-browser daemon for UI surface auditing of miniapps.
 *
 * Responsibilities:
 * - Launch isolated browser session
 * - Run UI security checks (CSP, scripts, iframes, wallet connectors)
 * - Capture before/after screenshots with visual proof
 * - Extract contract addresses from page for Group 3 pipeline
 */

import { TargetType, ResolvedTarget } from './types';

// ─── Config ───────────────────────────────────────────────────────────────────

const AGENT_BROWSER_URL = process.env.NEXT_PUBLIC_AGENT_BROWSER_URL || 'http://localhost:9222';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UIFinding {
  type: 'csp' | 'script' | 'iframe' | 'wallet' | 'network' | 'phishing';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  location?: string;
  evidence?: string;
}

export interface VisualProof {
  id: string;
  findingId: string;
  beforeScreenshot: string;  // base64
  afterScreenshot: string;   // base64
  diffScreenshot?: string;  // base64 with highlighted regions
  timestamp: string;
  description: string;
}

export interface BrowserAuditResult {
  jobId: string;
  targetUrl: string;
  findings: UIFinding[];
  visualProofs: VisualProof[];
  extractedContracts: string[];  // Contract addresses found on page
  metadata: {
    analyzedAt: string;
    pageTitle?: string;
    pageUrl: string;
    screenshotCount: number;
  };
}

// ─── Agent Browser API ─────────────────────────────────────────────────────

async function agentBrowserRequest<T = any>(command: object): Promise<T> {
  const res = await fetch(`${AGENT_BROWSER_URL}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  });

  if (!res.ok) {
    throw new Error(`AgentBrowser error: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  if (!data.success) {
    throw new Error(`AgentBrowser command failed: ${data.error}`);
  }

  return data.result;
}

// ─── UI Security Checks ────────────────────────────────────────────────────

async function checkCSP(page: any): Promise<UIFinding | null> {
  // Agent-browser would run this via evaluate
  const result = await agentBrowserRequest({
    action: 'evaluate',
    script: `
      (() => {
        const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        const headers = performance.getEntriesByType('resource')
          .filter(r => r.transferSize === 0 && r.decodedBodySize === 0);
        return {
          hasCSP: !!meta,
          cspContent: meta?.getAttribute('content'),
          blocked: headers.length
        };
      })()
    `
  });

  if (!result?.hasCSP) {
    return {
      type: 'csp',
      severity: 'medium',
      title: 'Missing Content Security Policy',
      description: 'No CSP header found. This increases XSS and data injection risk.',
    };
  }
  return null;
}

async function checkExternalScripts(page: any): Promise<UIFinding[]> {
  const findings: UIFinding[] = [];
  const result = await agentBrowserRequest({
    action: 'evaluate',
    script: `
      Array.from(document.querySelectorAll('script[src]')).map(s => ({
        src: s.src,
        integrity: s.integrity,
        async: s.async,
        defer: s.defer
      }))
    `
  });

  for (const script of result || []) {
    if (!script.integrity && !script.src.includes(location.hostname)) {
      findings.push({
        type: 'script',
        severity: 'high',
        title: 'External Script Without Integrity',
        description: `Script loaded from ${script.src} lacks SRI integrity attribute.`,
        location: script.src,
      });
    }
  }

  return findings;
}

async function checkIframes(page: any): Promise<UIFinding[]> {
  const findings: UIFinding[] = [];
  const result = await agentBrowserRequest({
    action: 'evaluate',
    script: `
      Array.from(document.querySelectorAll('iframe')).map(i => ({
        src: i.src,
        sandbox: i.sandbox,
        allow: i.allow
      }))
    `
  });

  for (const iframe of result || []) {
    if (!iframe.sandbox && !iframe.src.startsWith('about:')) {
      findings.push({
        type: 'iframe',
        severity: 'medium',
        title: 'Unsandboxed Iframe',
        description: `Iframe from ${iframe.src} lacks sandbox attribute.`,
        location: iframe.src,
      });
    }
  }

  return findings;
}

async function checkWalletConnectors(page: any): Promise<UIFinding[]> {
  const findings: UIFinding[] = [];
  const result = await agentBrowserRequest({
    action: 'evaluate',
    script: `
      (() => {
        const patterns = [
          /walletconnect/i,
          /rainbow/i,
          /metamask/i,
          /coinbase/i,
          /phantom/i,
          /ethers/i,
          /web3modal/i
        ];
        const connectors = [];
        // Check for known connector libraries
        const scripts = Array.from(document.querySelectorAll('script[src]'))
          .map(s => s.src);
        for (const p of patterns) {
          if (scripts.some(s => p.test(s))) {
            connectors.push(p.source);
          }
        }
        return connectors;
      })()
    `
  });

  if (result && result.length > 0) {
    findings.push({
      type: 'wallet',
      severity: 'info',
      title: 'Wallet Connector Detected',
      description: `Detected wallet libraries: ${result.join(', ')}`,
    });
  }

  return findings;
}

async function extractContractAddresses(page: any): Promise<string[]> {
  const result = await agentBrowserRequest({
    action: 'evaluate',
    script: `
      (() => {
        const addresses = new Set();
        // Match EVM addresses in DOM and network calls
        const evmPattern = /0x[a-fA-F0-9]{40}/g;
        
        // Check page content
        const bodyText = document.body.innerText;
        let match;
        while ((match = evmPattern.exec(bodyText)) !== null) {
          addresses.add(match[0].toLowerCase());
        }
        
        return Array.from(addresses);
      })()
    `
  });

  return result || [];
}

// ─── Main Audit Function ───────────────────────────────────────────────────

export async function runBrowserAudit(
  target: ResolvedTarget,
  jobId: string
): Promise<BrowserAuditResult> {
  if (target.type !== 'miniapp_url') {
    throw new Error('Browser audit requires miniapp_url target type');
  }

  const targetUrl = target.value;
  const findings: UIFinding[] = [];
  const visualProofs: VisualProof[] = [];
  const extractedContracts: string[] = [];

  try {
    // 1. Launch browser session
    const session = await agentBrowserRequest<{ sessionId: string }>({
      action: 'launch',
      headless: true,
    });

    // 2. Navigate to target
    await agentBrowserRequest({
      action: 'navigate',
      url: targetUrl,
      waitUntil: 'networkidle',
    });

    // 3. Capture "before" state
    const beforeScreenshot = await agentBrowserRequest<{ base64: string }>({
      action: 'screenshot',
    });

    // 4. Run security checks
    const cspFinding = await checkCSP(null);
    if (cspFinding) findings.push(cspFinding);

    findings.push(...await checkExternalScripts(null));
    findings.push(...await checkIframes(null));
    findings.push(...await checkWalletConnectors(null));

    // 5. Extract contracts
    const contracts = await extractContractAddresses(null);
    extractedContracts.push(...contracts);

    // 6. Simulate "after" state (in real implementation, trigger each finding)
    // For demo, we just capture another screenshot
    const afterScreenshot = await agentBrowserRequest<{ base64: string }>({
      action: 'screenshot',
    });

    // 7. Create visual proof entries for findings that can be visualized
    for (const finding of findings.slice(0, 3)) {
      visualProofs.push({
        id: `proof-${finding.type}-${Date.now()}`,
        findingId: finding.type,
        beforeScreenshot: beforeScreenshot.base64,
        afterScreenshot: afterScreenshot.base64,
        timestamp: new Date().toISOString(),
        description: finding.title,
      });
    }

    // 8. Cleanup
    await agentBrowserRequest({ action: 'close' });

    return {
      jobId,
      targetUrl,
      findings,
      visualProofs,
      extractedContracts: [...new Set(extractedContracts)],
      metadata: {
        analyzedAt: new Date().toISOString(),
        pageUrl: targetUrl,
        screenshotCount: visualProofs.length,
      },
    };
  } catch (error) {
    console.error('[BrowserAudit] Error:', error);
    throw error;
  }
}

// ─── Utility: Generate Diff (Client-Side) ─────────────────────────────────

export async function generateScreenshotDiff(
  beforeBase64: string,
  afterBase64: string
): Promise<string> {
  // This would use a library like pixelmatch in a real implementation
  // For now, return the "after" image as placeholder
  return afterBase64;
}
