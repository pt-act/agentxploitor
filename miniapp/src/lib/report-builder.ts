/**
 * report-builder.ts
 * Transforms raw HexStrike findings into a structured AuditReport.
 *
 * Responsibilities:
 * - Map HexStrike VulnerabilityFinding → Finding
 * - Calculate overall severity (worst single finding wins)
 * - Generate immutable independence declaration
 * - Produce downloadable JSON + Markdown reports
 */

import { Severity, AuditReport, Vulnerability } from './types';

// ─── Types ────────────────────────────────────────────────────────────────────

export type Verdict = 'BLOCKED' | 'REVIEW' | 'CAUTION' | 'CLEAR' | 'CLEAN';

export interface HexStrikeFinding {
  id?: string;
  title: string;
  description: string;
  severity: string;           // HexStrike uses lowercase: 'critical', 'high', etc.
  cvss_score?: number;
  location?: string;
  cve_ids?: string[];
  attack_chain?: string[];
  fix_recommendation?: string;
  confidence?: number;
  analyzer?: string;
}

export interface FindingCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface IndependenceDeclaration {
  text: string;
  requestedByFid: number;
  targetValue: string;
  auditType: string;
  timestamp: string;
  chain: string;
}

export interface BuiltReport {
  report: AuditReport;
  verdict: Verdict;
  findingCount: FindingCount;
  declaration: IndependenceDeclaration;
  markdownReport: string;
}

// ─── Severity Mapping ─────────────────────────────────────────────────────────

const SEVERITY_ORDER: Record<string, number> = {
  critical: 5,
  high: 4,
  medium: 3,
  low: 2,
  info: 1,
};

const SEVERITY_MAP: Record<string, Severity> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
  info: 'INFO',
};

function normalizeSeverity(raw: string): Severity {
  return SEVERITY_MAP[raw.toLowerCase()] ?? 'INFO';
}

// ─── Overall Severity → Verdict ───────────────────────────────────────────────

export function severityToVerdict(overallSeverity: Severity | null): Verdict {
  switch (overallSeverity) {
    case 'CRITICAL': return 'BLOCKED';
    case 'HIGH':     return 'REVIEW';
    case 'MEDIUM':   return 'CAUTION';
    case 'LOW':      return 'CLEAR';
    case 'INFO':
    case null:
    default:         return 'CLEAN';
  }
}

// ─── Overall Severity Calculation ────────────────────────────────────────────
// Property: ∀ findings: overall = max(finding.severity)

export function calculateOverallSeverity(findings: HexStrikeFinding[]): Severity | null {
  if (!findings || findings.length === 0) return null;

  let maxScore = 0;
  let maxSeverity: Severity | null = null;

  for (const f of findings) {
    const score = SEVERITY_ORDER[f.severity?.toLowerCase()] ?? 0;
    if (score > maxScore) {
      maxScore = score;
      maxSeverity = normalizeSeverity(f.severity);
    }
  }

  return maxSeverity;
}

// ─── Finding Count ────────────────────────────────────────────────────────────

export function countFindings(findings: HexStrikeFinding[]): FindingCount {
  const count: FindingCount = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  for (const f of findings) {
    const key = f.severity?.toLowerCase() as keyof FindingCount;
    if (key in count) count[key]++;
    else count.info++;
  }
  return count;
}

// ─── Independence Declaration ─────────────────────────────────────────────────
// Immutable — generated server-side only, never editable by client
// Property: ∀ report: has_fid ∧ has_timestamp ∧ has_declaration

export function generateDeclaration(
  requestedByFid: number,
  targetValue: string,
  auditType: string,
  chain: string
): IndependenceDeclaration {
  const timestamp = new Date().toISOString();
  const text = [
    `INDEPENDENCE DECLARATION`,
    `This audit was independently requested by Farcaster user FID:${requestedByFid}.`,
    `It is NOT affiliated with, endorsed by, or compensated by the audited project.`,
    `Target: ${targetValue}`,
    `Audit type: ${auditType}`,
    `Chain: ${chain}`,
    `Timestamp: ${timestamp}`,
    `Analysis: EntityHex Security Agent + HexStrike 12-agent intelligence`,
    `This declaration is immutable and was generated server-side at audit completion.`,
  ].join('\n');

  return { text, requestedByFid, targetValue, auditType, timestamp, chain };
}

// ─── HexStrike Finding → Vulnerability ───────────────────────────────────────

function mapFinding(f: HexStrikeFinding, index: number): Vulnerability {
  return {
    id: f.id ?? `finding-${index + 1}`,
    title: f.title,
    description: f.description,
    severity: normalizeSeverity(f.severity),
    cvssScore: f.cvss_score ?? 0,
    location: f.location ?? 'Unknown',
    exploitScenario: f.attack_chain?.join(' → ') ?? 'See description',
    expectedOutcome: f.fix_recommendation ?? 'Review and remediate',
    analyzer: f.analyzer ?? 'HexStrike',
    confidence: f.confidence ?? 0.8,
    aiSuggestion: f.fix_recommendation,
    status: 'open',
  };
}

// ─── Markdown Report Generator ────────────────────────────────────────────────

function buildMarkdownReport(
  jobId: string,
  targetValue: string,
  auditType: string,
  verdict: Verdict,
  findingCount: FindingCount,
  vulnerabilities: Vulnerability[],
  declaration: IndependenceDeclaration
): string {
  const verdictEmoji: Record<Verdict, string> = {
    BLOCKED: '🔴', REVIEW: '🟠', CAUTION: '🟡', CLEAR: '🟢', CLEAN: '✅',
  };

  const lines: string[] = [
    `# AgentxploiTor Security Audit Report`,
    ``,
    `**Target**: ${targetValue}`,
    `**Audit Type**: ${auditType}`,
    `**Verdict**: ${verdictEmoji[verdict]} ${verdict}`,
    `**Generated**: ${declaration.timestamp}`,
    `**Audit ID**: ${jobId}`,
    ``,
    `---`,
    ``,
    `## Independence Declaration`,
    ``,
    `\`\`\``,
    declaration.text,
    `\`\`\``,
    ``,
    `---`,
    ``,
    `## Findings Summary`,
    ``,
    `| Severity | Count |`,
    `|----------|-------|`,
    `| 🔴 CRITICAL | ${findingCount.critical} |`,
    `| 🟠 HIGH | ${findingCount.high} |`,
    `| 🟡 MEDIUM | ${findingCount.medium} |`,
    `| 🟢 LOW | ${findingCount.low} |`,
    `| ℹ️ INFO | ${findingCount.info} |`,
    ``,
    `---`,
    ``,
    `## Detailed Findings`,
    ``,
  ];

  if (vulnerabilities.length === 0) {
    lines.push(`*No vulnerabilities detected. The contract passed all analysis checks.*`);
  } else {
    for (const v of vulnerabilities) {
      lines.push(
        `### [${v.severity}] ${v.title}`,
        ``,
        `**Location**: ${v.location}`,
        `**CVSS Score**: ${v.cvssScore}`,
        `**Analyzer**: ${v.analyzer}`,
        ``,
        `**Description**:`,
        `${v.description}`,
        ``,
        `**Attack Scenario**: ${v.exploitScenario}`,
        ``,
        `**Recommendation**: ${v.aiSuggestion ?? v.expectedOutcome}`,
        ``,
        `---`,
        ``,
      );
    }
  }

  lines.push(
    `## Disclaimer`,
    ``,
    `This report was produced by an automated AI system. It is provided for informational`,
    `purposes only and does not constitute professional security advice. Independent`,
    `verification by a qualified security professional is recommended before making`,
    `investment or deployment decisions.`,
    ``,
    `*Powered by EntityHex Security Agent + HexStrike 12-agent intelligence*`,
  );

  return lines.join('\n');
}

// ─── Main Builder ─────────────────────────────────────────────────────────────

export function buildReport(params: {
  jobId: string;
  targetValue: string;
  auditType: string;
  chain: string;
  requestedByFid: number;
  hexStrikeFindings: HexStrikeFinding[];
  agentsUsed?: string[];
}): BuiltReport {
  const { jobId, targetValue, auditType, chain, requestedByFid, hexStrikeFindings, agentsUsed } = params;

  const overallSeverity = calculateOverallSeverity(hexStrikeFindings);
  const verdict = severityToVerdict(overallSeverity);
  const findingCount = countFindings(hexStrikeFindings);
  const declaration = generateDeclaration(requestedByFid, targetValue, auditType, chain);
  const vulnerabilities = hexStrikeFindings.map(mapFinding);

  const report: AuditReport = {
    id: `report-${jobId}`,
    jobId,
    targetUrl: targetValue,
    summary: {
      critical: findingCount.critical,
      high: findingCount.high,
      medium: findingCount.medium,
      low: findingCount.low,
      info: findingCount.info,
    },
    vulnerabilities,
    exploits: [],
    verifications: [],
    evaluation: {
      satisfactory: overallSeverity === null || overallSeverity === 'INFO' || overallSeverity === 'LOW',
      confidence: 0.85,
      issues: hexStrikeFindings.filter(f => ['critical','high'].includes(f.severity?.toLowerCase())).map(f => f.title),
      evidence: agentsUsed ?? [],
    },
    createdAt: declaration.timestamp,
  };

  const markdownReport = buildMarkdownReport(
    jobId, targetValue, auditType, verdict, findingCount, vulnerabilities, declaration
  );

  return { report, verdict, findingCount, declaration, markdownReport };
}
