import { NextRequest, NextResponse } from 'next/server';
import { getJob } from '~/lib/storage';
import type { JobSession, Severity } from '~/lib/types';

/**
 * GET /api/disclosure/[id]
 * 
 * Generates a responsible disclosure template from audit results.
 * 
 * Requirements:
 * - Only accessible when mode = "research" 
 * - Only shows findings with severity >= MEDIUM
 * - Includes: finding summary, severity, recommended fix, reporter FID, timestamp
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const job = await getJob(id);
    
    if (!job) {
      return NextResponse.json(
        { error: 'Audit not found' },
        { status: 404 }
      );
    }
    
    // Only allow disclosure for research mode
    if (job.mode !== 'research') {
      return NextResponse.json(
        { error: 'Disclosure only available for research mode audits' },
        { status: 403 }
      );
    }
    
    // Get findings with severity >= MEDIUM
    const findings = job.findings || [];
    const severityOrder: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
    const minSeverityIndex = severityOrder.indexOf('MEDIUM');
    
    const actionableFindings = findings.filter((finding: any) => {
      const findingSeverity = finding.severity || 'INFO';
      return severityOrder.indexOf(findingSeverity) <= minSeverityIndex;
    });
    
    if (actionableFindings.length === 0) {
      return NextResponse.json({
        disclosure: {
          hasFindings: false,
          message: 'No actionable vulnerabilities found for disclosure.',
          auditId: job.id,
          targetUrl: job.targetUrl,
          mode: job.mode,
        }
      });
    }
    
    // Generate disclosure template
    const timestamp = new Date().toISOString();
    const reporterFid = job.requestedByFid;
    
    // Generate non-sensitive summary for social media
    const summary = generateSummary(actionableFindings);
    
    // Generate detailed disclosure
    const disclosure = {
      // Metadata
      auditId: job.id,
      targetUrl: job.targetUrl,
      targetType: job.targetType,
      blockchain: job.blockchain,
      reporterFid,
      auditMode: job.mode,
      analysisType: job.analysisType,
      createdAt: job.createdAt,
      disclosureGeneratedAt: timestamp,
      
      // Findings summary
      findingsCount: {
        critical: actionableFindings.filter((f: any) => f.severity === 'CRITICAL').length,
        high: actionableFindings.filter((f: any) => f.severity === 'HIGH').length,
        medium: actionableFindings.filter((f: any) => f.severity === 'MEDIUM').length,
      },
      
      // Detailed findings for disclosure
      findings: actionableFindings.map((finding: any) => ({
        id: finding.id,
        title: finding.title,
        severity: finding.severity,
        location: finding.location,
        description: finding.description,
        recommendedFix: finding.expectedOutcome || finding.aiSuggestion,
        cvssScore: finding.cvssScore,
      })),
      
      // Social media friendly summary
      socialSummary: summary,
      
      // Faroaster cast composer URL
      castComposerUrl: generateCastComposerUrl(summary, job.targetUrl),
      
      // Developer contact info
      developerContact: {
        note: 'Contact the development team through official channels.',
        suggestion: 'Search for the project on Warpcast or GitHub to find the appropriate contact.',
      },
      
      // Full text template
      fullTemplate: generateFullTemplate(job, actionableFindings, timestamp),
    };
    
    return NextResponse.json({ disclosure });
    
  } catch (error) {
    console.error('Error generating disclosure:', error);
    return NextResponse.json(
      { error: 'Failed to generate disclosure' },
      { status: 500 }
    );
  }
}

function generateSummary(findings: any[]): string {
  const bySeverity = {
    critical: findings.filter(f => f.severity === 'CRITICAL').length,
    high: findings.filter(f => f.severity === 'HIGH').length,
    medium: findings.filter(f => f.severity === 'MEDIUM').length,
  };
  
  const parts = [];
  if (bySeverity.critical > 0) parts.push(`${bySeverity.critical} CRITICAL`);
  if (bySeverity.high > 0) parts.push(`${bySeverity.high} HIGH`);
  if (bySeverity.medium > 0) parts.push(`${bySeverity.medium} MEDIUM`);
  
  return `Security audit found: ${parts.join(', ')} vulnerability${parts.length > 1 ? 's' : ''}. Full report available.`;
}

function generateCastComposerUrl(summary: string, targetUrl: string): string {
  const baseUrl = 'https://warpcast.com/compose';
  const text = encodeURIComponent(`${summary}\n\nTarget: ${targetUrl}`);
  return `${baseUrl}?text=${text}`;
}

function generateFullTemplate(job: JobSession, findings: any[], timestamp: string): string {
  const lines = [
    '# Responsible Security Disclosure',
    '',
    `**Audit ID:** ${job.id}`,
    `**Target:** ${job.targetUrl}`,
    `**Blockchains:** ${job.blockchain || 'N/A'}`,
    `**Reported By FID:** ${job.requestedByFid || 'Anonymous'}`,
    `**Audit Mode:** ${job.mode}`,
    `**Date:** ${timestamp}`,
    '',
    '---',
    '',
    '## Vulnerability Summary',
    '',
  ];
  
  const severityOrder = ['CRITICAL', 'HIGH', 'MEDIUM'];
  
  for (const severity of severityOrder) {
    const sevFindings = findings.filter(f => f.severity === severity);
    if (sevFindings.length > 0) {
      lines.push(`### ${severity} Severity (${sevFindings.length})`);
      lines.push('');
      for (const f of sevFindings) {
        lines.push(`- **${f.title}**`);
        lines.push(`  - Location: ${f.location || 'N/A'}`);
        lines.push(`  - Description: ${f.description?.slice(0, 200)}...`);
        lines.push(`  - Recommended Fix: ${f.expectedOutcome || f.aiSuggestion || 'See full report'}`);
        lines.push('');
      }
    }
  }
  
  lines.push('---');
  lines.push('');
  lines.push('*This disclosure was generated by AgentxploiTor.*');
  lines.push('*Independent security audit - no affiliation with the audited project.*');
  
  return lines.join('\n');
}
