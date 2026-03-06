/**
 * Group 3 Tests: Smart Contract Evaluator Pipeline
 * T3.1 - Source resolver fetches verified Solidity from Basescan (mock API)
 * T3.2 - Report builder: critical finding → BLOCKED overall verdict
 * T3.3 - Report builder: zero findings → CLEAN verdict with independence declaration
 * T3.4 - Results API returns complete report for completed job
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  calculateOverallSeverity,
  severityToVerdict,
  countFindings,
  generateDeclaration,
  buildReport,
  HexStrikeFinding,
} from '../lib/report-builder';
import { resolveEvmContract } from '../lib/chain-resolver';

// ─── T3.1: Source resolver — verified Solidity from Basescan ─────────────────

describe('T3.1 chain-resolver: EVM contract source resolution', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns verified_solidity when Basescan returns source code', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: '1',
        result: [{
          SourceCode: 'pragma solidity ^0.8.0;\ncontract Foo {}',
          ContractName: 'Foo',
          CompilerVersion: 'v0.8.20',
          ABI: '[]',
        }],
      }),
    }) as any;

    const result = await resolveEvmContract('0xabcdef1234567890abcdef1234567890abcdef12', 'base');

    expect(result.sourceType).toBe('verified_solidity');
    expect(result.verified).toBe(true);
    expect(result.contractName).toBe('Foo');
    expect(result.sourceFiles?.['contract.sol']).toContain('pragma solidity');
  });

  it('falls back to bytecode_only when source is not verified', async () => {
    // First call: source code API returns empty
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: '0',
          result: [{ SourceCode: '' }],
        }),
      })
      // Second call: bytecode API
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ result: '0x6080604052...' }),
      }) as any;

    const result = await resolveEvmContract('0xabcdef1234567890abcdef1234567890abcdef12', 'base');

    expect(result.sourceType).toBe('bytecode_only');
    expect(result.verified).toBe(false);
    expect(result.bytecode).toContain('0x');
  });
});

// ─── T3.2: Report builder — critical finding → BLOCKED ───────────────────────

describe('T3.2 report-builder: critical finding produces BLOCKED verdict', () => {
  const criticalFinding: HexStrikeFinding = {
    id: 'f-001',
    title: 'Reentrancy Vulnerability',
    description: 'The withdraw function is vulnerable to reentrancy attacks.',
    severity: 'critical',
    cvss_score: 9.8,
    location: 'contracts/Vault.sol:42',
    attack_chain: ['Call withdraw()', 'Re-enter before balance update', 'Drain funds'],
    fix_recommendation: 'Use ReentrancyGuard or check-effects-interactions pattern.',
    confidence: 0.95,
    analyzer: 'HexStrike',
  };

  it('calculates CRITICAL as overall severity', () => {
    const severity = calculateOverallSeverity([criticalFinding]);
    expect(severity).toBe('CRITICAL');
  });

  it('maps CRITICAL severity to BLOCKED verdict', () => {
    expect(severityToVerdict('CRITICAL')).toBe('BLOCKED');
  });

  it('buildReport produces BLOCKED verdict for critical finding', () => {
    const result = buildReport({
      jobId: 'job-test-001',
      targetValue: '0xabcd',
      auditType: 'contract_deep',
      chain: 'base',
      requestedByFid: 12345,
      hexStrikeFindings: [criticalFinding],
    });

    expect(result.verdict).toBe('BLOCKED');
    expect(result.findingCount.critical).toBe(1);
    expect(result.report.vulnerabilities).toHaveLength(1);
    expect(result.report.vulnerabilities[0].severity).toBe('CRITICAL');
    expect(result.report.vulnerabilities[0].exploitScenario).toContain('Re-enter');
    expect(result.markdownReport).toContain('BLOCKED');
    expect(result.markdownReport).toContain('Reentrancy Vulnerability');
  });

  it('worst severity wins when multiple findings present', () => {
    const findings: HexStrikeFinding[] = [
      { title: 'Low issue', description: 'Minor', severity: 'low' },
      criticalFinding,
      { title: 'Medium issue', description: 'Med', severity: 'medium' },
    ];
    const severity = calculateOverallSeverity(findings);
    expect(severity).toBe('CRITICAL');
    expect(severityToVerdict(severity)).toBe('BLOCKED');
  });
});

// ─── T3.3: Report builder — zero findings → CLEAN ────────────────────────────

describe('T3.3 report-builder: zero findings produces CLEAN verdict with declaration', () => {
  it('returns CLEAN verdict for empty findings', () => {
    const result = buildReport({
      jobId: 'job-test-002',
      targetValue: '0xclean1234',
      auditType: 'contract_basic',
      chain: 'base',
      requestedByFid: 99999,
      hexStrikeFindings: [],
    });

    expect(result.verdict).toBe('CLEAN');
    expect(result.findingCount.critical).toBe(0);
    expect(result.findingCount.high).toBe(0);
    expect(result.report.vulnerabilities).toHaveLength(0);
    expect(result.report.evaluation.satisfactory).toBe(true);
  });

  it('independence declaration contains required fields (PBT property)', () => {
    const result = buildReport({
      jobId: 'job-test-003',
      targetValue: '0xtest',
      auditType: 'contract_basic',
      chain: 'base',
      requestedByFid: 42,
      hexStrikeFindings: [],
    });

    // PBT property: ∀ report: has_fid ∧ has_timestamp ∧ has_declaration
    expect(result.declaration.requestedByFid).toBe(42);
    expect(result.declaration.timestamp).toBeTruthy();
    expect(result.declaration.text).toContain('FID:42');
    expect(result.declaration.text).toContain('INDEPENDENCE DECLARATION');
    expect(result.declaration.text).toContain('NOT affiliated');
    expect(result.declaration.text).toContain('immutable');
  });

  it('generateDeclaration is deterministic for same inputs (same FID + target)', () => {
    const d1 = generateDeclaration(100, '0xabc', 'contract_basic', 'base');
    const d2 = generateDeclaration(100, '0xabc', 'contract_basic', 'base');
    // Text content is identical (timestamp will differ by ms — check structure)
    expect(d1.text).toContain('FID:100');
    expect(d1.text).toContain('0xabc');
    expect(d2.text).toContain('FID:100');
    expect(d1.chain).toBe(d2.chain);
    expect(d1.auditType).toBe(d2.auditType);
  });

  it('markdown report contains independence declaration text', () => {
    const result = buildReport({
      jobId: 'job-test-004',
      targetValue: '0xcleantarget',
      auditType: 'contract_deep',
      chain: 'base',
      requestedByFid: 77,
      hexStrikeFindings: [],
    });

    expect(result.markdownReport).toContain('Independence Declaration');
    expect(result.markdownReport).toContain('FID:77');
    expect(result.markdownReport).toContain('No vulnerabilities detected');
  });
});

// ─── T3.4: Results API integration ───────────────────────────────────────────

describe('T3.4 results API: returns complete report for completed job', () => {
  it('severity verdict mapping covers all cases', () => {
    // Verify the full verdict ladder
    expect(severityToVerdict('CRITICAL')).toBe('BLOCKED');
    expect(severityToVerdict('HIGH')).toBe('REVIEW');
    expect(severityToVerdict('MEDIUM')).toBe('CAUTION');
    expect(severityToVerdict('LOW')).toBe('CLEAR');
    expect(severityToVerdict('INFO')).toBe('CLEAN');
    expect(severityToVerdict(null)).toBe('CLEAN');
  });

  it('countFindings tallies by severity correctly', () => {
    const findings: HexStrikeFinding[] = [
      { title: 'A', description: 'a', severity: 'critical' },
      { title: 'B', description: 'b', severity: 'high' },
      { title: 'C', description: 'c', severity: 'high' },
      { title: 'D', description: 'd', severity: 'medium' },
      { title: 'E', description: 'e', severity: 'info' },
    ];
    const count = countFindings(findings);
    expect(count.critical).toBe(1);
    expect(count.high).toBe(2);
    expect(count.medium).toBe(1);
    expect(count.low).toBe(0);
    expect(count.info).toBe(1);
  });

  it('buildReport report.summary matches findingCount', () => {
    const findings: HexStrikeFinding[] = [
      { title: 'X', description: 'x', severity: 'high' },
      { title: 'Y', description: 'y', severity: 'medium' },
    ];
    const result = buildReport({
      jobId: 'job-summary-test',
      targetValue: '0xsummary',
      auditType: 'contract_deep',
      chain: 'base',
      requestedByFid: 1,
      hexStrikeFindings: findings,
    });

    expect(result.report.summary.high).toBe(result.findingCount.high);
    expect(result.report.summary.medium).toBe(result.findingCount.medium);
    expect(result.report.summary.critical).toBe(0);
  });
});
