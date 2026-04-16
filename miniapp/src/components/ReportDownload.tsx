"use client";

import { useState } from 'react';
import { Button } from './ui/Button';
import type { Vulnerability } from '~/lib/types';

interface ReportDownloadProps {
  auditId: string;
  targetUrl: string;
  findings: Partial<Vulnerability>[];
  summary: Record<string, number>;
  confidence: number;
  createdAt: string;
  reporterFid?: number;
}

export default function ReportDownload({
  auditId,
  targetUrl,
  findings,
  summary,
  confidence,
  createdAt,
  reporterFid,
}: ReportDownloadProps) {
  const [downloading, setDownloading] = useState<'json' | 'markdown' | null>(null);

  const generateJsonReport = () => {
    const report = {
      audit: {
        id: auditId,
        targetUrl,
        createdAt,
        confidence: confidence,
        reporterFid,
      },
      summary: {
        ...summary,
        total: Object.values(summary).reduce((a, b) => a + b, 0),
      },
      findings: findings.map(f => ({
        id: f.id,
        title: f.title,
        severity: f.severity,
        cvssScore: f.cvssScore,
        description: f.description,
        location: f.location,
        expectedOutcome: f.expectedOutcome,
        exploitScenario: f.exploitScenario,
        confidence: f.confidence,
      })),
      attribution: `Audited by AgentxploiTor via Farcaster | Reporter FID: ${reporterFid || 'Anonymous'}`,
    };

    return JSON.stringify(report, null, 2);
  };

  const generateMarkdownReport = () => {
    const severityOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
    const lines = [
      `# Security Audit Report`,
      ``,
      `**Audit ID:** ${auditId}`,
      `**Target:** ${targetUrl}`,
      `**Date:** ${new Date(createdAt).toLocaleDateString()}`,
      `**Confidence:** ${Math.round(confidence * 100)}%`,
      `**Reporter:** ${reporterFid ? `FID ${reporterFid}` : 'Anonymous'}`,
      ``,
      `---`,
      ``,
      `## Summary`,
      ``,
      `| Severity | Count |`,
      `|----------|-------|`,
      ...severityOrder.map(sev => `| ${sev} | ${summary[sev] || 0} |`),
      ``,
      `---`,
      ``,
      `## Findings`,
      ``,
    ];

    for (const severity of severityOrder) {
      const sevFindings = findings.filter(f => f.severity === severity);
      if (sevFindings.length > 0) {
        lines.push(`### ${severity} (${sevFindings.length})`);
        lines.push(``);
        
        for (const f of sevFindings) {
          lines.push(`#### ${f.title}`);
          lines.push(``);
          lines.push(`- **CVSS:** ${f.cvssScore?.toFixed(1) || 'N/A'}`);
          lines.push(`- **Location:** ${f.location || 'N/A'}`);
          lines.push(``);
          lines.push(`**Description:**`);
          lines.push(``);
          lines.push(f.description || 'No description');
          lines.push(``);
          
          if (f.expectedOutcome) {
            lines.push(`**Recommended Fix:**`);
            lines.push(``);
            lines.push(f.expectedOutcome);
            lines.push(``);
          }
          
          if (f.exploitScenario) {
            lines.push(`**Exploit Scenario:**`);
            lines.push(``);
            lines.push(f.exploitScenario);
            lines.push(``);
          }
          
          lines.push(`---`);
          lines.push(``);
        }
      }
    }

    lines.push(`## Attribution`);
    lines.push(``);
    lines.push(`*Audited by AgentxploiTor via Farcaster | Reporter FID: ${reporterFid || 'Anonymous'}*`);
    lines.push(``);
    lines.push(`*Independent security audit - no affiliation with the audited project*`);

    return lines.join('\n');
  };

  const downloadJson = () => {
    setDownloading('json');
    const blob = new Blob([generateJsonReport()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-${auditId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloading(null);
  };

  const downloadMarkdown = () => {
    setDownloading('markdown');
    const blob = new Blob([generateMarkdownReport()], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-${auditId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloading(null);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">📥 Download Report</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* JSON Report */}
        <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">📋</span>
            <div>
              <h4 className="text-white font-medium">JSON Report</h4>
              <p className="text-gray-500 text-xs">Machine-readable format</p>
            </div>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Includes: audit metadata, resolved targets, all findings, visual proof paths, confidence scores
          </p>
          <Button
            onClick={downloadJson}
            disabled={downloading !== null}
            className="w-full bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] disabled:opacity-50"
          >
            {downloading === 'json' ? '⏳ Generating...' : 'Download JSON'}
          </Button>
        </div>

        {/* Markdown Report */}
        <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">📝</span>
            <div>
              <h4 className="text-white font-medium">Markdown Report</h4>
              <p className="text-gray-500 text-xs">Human-readable format</p>
            </div>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Includes: severity table, finding descriptions, fix recommendations, full attribution
          </p>
          <Button
            onClick={downloadMarkdown}
            disabled={downloading !== null}
            className="w-full bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] disabled:opacity-50"
          >
            {downloading === 'markdown' ? '⏳ Generating...' : 'Download Markdown'}
          </Button>
        </div>
      </div>

      {/* Attribution Notice */}
      <div className="text-center text-xs text-gray-500 pt-2 border-t border-gray-700">
        <p>Audited by AgentxploiTor via Farcaster | Reporter FID: {reporterFid || 'Anonymous'}</p>
      </div>
    </div>
  );
}
