"use client";

import { useState } from 'react';
import { Button } from './ui/Button';
import { AuditReport } from '~/lib/types';
import { IndependenceDeclaration, Verdict, FindingCount } from '~/lib/report-builder';

interface ReportDownloadProps {
  auditId: string;
  targetValue: string;
  verdict: Verdict;
  report: AuditReport;
  declaration: IndependenceDeclaration;
  findingCount: FindingCount;
  markdownReport: string;
}

export default function ReportDownload({
  auditId,
  targetValue,
  verdict,
  report,
  declaration,
  findingCount,
  markdownReport,
}: ReportDownloadProps) {
  const [copied, setCopied] = useState(false);

  const downloadJson = () => {
    const payload = {
      auditId,
      targetValue,
      verdict,
      findingCount,
      declaration,
      report,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agentxploitor-audit-${auditId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdown = () => {
    const blob = new Blob([markdownReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agentxploitor-audit-${auditId.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyDeclaration = async () => {
    await navigator.clipboard.writeText(declaration.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareOnFarcaster = () => {
    const verdictEmoji: Record<string, string> = {
      BLOCKED: '🔴', REVIEW: '🟠', CAUTION: '🟡', CLEAR: '🟢', CLEAN: '✅',
    };
    const text = [
      `${verdictEmoji[verdict] ?? '⚡'} Just audited ${targetValue} with @agentxploitor`,
      ``,
      `Verdict: ${verdict}`,
      `Critical: ${findingCount.critical} | High: ${findingCount.high} | Medium: ${findingCount.medium}`,
      ``,
      `Independently verified — not affiliated with the project.`,
      `Audit ID: ${auditId.slice(0, 8)}`,
    ].join('\n');

    const castUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(text)}`;
    window.open(castUrl, '_blank');
  };

  return (
    <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
      <h3 className="text-white font-semibold mb-4">Download & Share</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* JSON Download */}
        <Button
          onClick={downloadJson}
          className="flex flex-col items-center gap-1 py-4 bg-[#0a0e27] border border-gray-700 hover:border-[#00ff41] text-gray-300 hover:text-[#00ff41] text-sm"
        >
          <span className="text-xl">{ }</span>
          <span>JSON Report</span>
        </Button>

        {/* Markdown Download */}
        <Button
          onClick={downloadMarkdown}
          className="flex flex-col items-center gap-1 py-4 bg-[#0a0e27] border border-gray-700 hover:border-[#00ff41] text-gray-300 hover:text-[#00ff41] text-sm"
        >
          <span className="text-xl">#</span>
          <span>Markdown</span>
        </Button>

        {/* Copy Declaration */}
        <Button
          onClick={copyDeclaration}
          className="flex flex-col items-center gap-1 py-4 bg-[#0a0e27] border border-gray-700 hover:border-[#00ff41] text-gray-300 hover:text-[#00ff41] text-sm"
        >
          <span className="text-xl">{copied ? '✓' : '⧉'}</span>
          <span>{copied ? 'Copied!' : 'Declaration'}</span>
        </Button>

        {/* Share on Farcaster */}
        <Button
          onClick={shareOnFarcaster}
          className="flex flex-col items-center gap-1 py-4 bg-[#0a0e27] border border-gray-700 hover:border-purple-400 text-gray-300 hover:text-purple-400 text-sm"
        >
          <span className="text-xl">⬡</span>
          <span>Cast Result</span>
        </Button>
      </div>

      <p className="text-xs text-gray-600 mt-3">
        Reports are generated at download time. Audit ID serves as permanent reference.
      </p>
    </div>
  );
}
