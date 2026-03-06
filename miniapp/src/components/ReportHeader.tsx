"use client";

import { IndependenceDeclaration, Verdict } from '~/lib/report-builder';

// ─── Verdict display config ───────────────────────────────────────────────────

const VERDICT_CONFIG: Record<Verdict, { label: string; color: string; bg: string; border: string; icon: string }> = {
  BLOCKED: { label: 'BLOCKED',  color: 'text-red-400',    bg: 'bg-red-400/10',    border: 'border-red-400',    icon: '🔴' },
  REVIEW:  { label: 'REVIEW',   color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400', icon: '🟠' },
  CAUTION: { label: 'CAUTION',  color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400', icon: '🟡' },
  CLEAR:   { label: 'CLEAR',    color: 'text-green-400',  bg: 'bg-green-400/10',  border: 'border-green-400',  icon: '🟢' },
  CLEAN:   { label: 'CLEAN',    color: 'text-[#00ff41]',  bg: 'bg-[#00ff41]/10', border: 'border-[#00ff41]',  icon: '✅' },
};

const VERDICT_DESCRIPTION: Record<Verdict, string> = {
  BLOCKED: 'Critical vulnerabilities found. Do not interact with this contract.',
  REVIEW:  'High-severity issues found. Requires expert review before use.',
  CAUTION: 'Medium-severity issues found. Proceed with caution.',
  CLEAR:   'Low-severity issues only. Generally safe with minor improvements recommended.',
  CLEAN:   'No significant vulnerabilities detected. Contract passed all analysis checks.',
};

// ─── Props ────────────────────────────────────────────────────────────────────

interface ReportHeaderProps {
  auditId: string;
  targetValue: string;
  targetType?: string;
  auditType?: string;
  chain?: string;
  requestedByFid?: number;
  completedAt?: string;
  verdict: Verdict;
  declaration: IndependenceDeclaration;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ReportHeader({
  auditId,
  targetValue,
  targetType,
  auditType,
  chain = 'base',
  requestedByFid,
  completedAt,
  verdict,
  declaration,
}: ReportHeaderProps) {
  const config = VERDICT_CONFIG[verdict];

  const formatTarget = (value: string, type?: string) => {
    if (type === 'contract_evm' && value.startsWith('0x')) {
      return `${value.slice(0, 6)}...${value.slice(-4)}`;
    }
    try {
      return new URL(value).hostname;
    } catch {
      return value;
    }
  };

  const formatDate = (iso?: string) => {
    if (!iso) return 'Unknown';
    return new Date(iso).toLocaleString('en-US', {
      dateStyle: 'medium', timeStyle: 'short'
    });
  };

  return (
    <div className="space-y-4">

      {/* Verdict Banner */}
      <div className={`rounded-xl border-2 p-6 ${config.bg} ${config.border}`}>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <span className="text-5xl">{config.icon}</span>
            <div>
              <div className={`text-3xl font-bold ${config.color}`}>{config.label}</div>
              <p className="text-gray-300 mt-1 max-w-md">{VERDICT_DESCRIPTION[verdict]}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Audit ID</div>
            <div className="font-mono text-sm text-gray-400">{auditId}</div>
          </div>
        </div>
      </div>

      {/* Target + Meta */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#0a0e27] border border-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Target</div>
          <div className="text-white text-sm font-mono truncate" title={targetValue}>
            {formatTarget(targetValue, targetType)}
          </div>
        </div>
        <div className="bg-[#0a0e27] border border-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Audit Type</div>
          <div className="text-white text-sm capitalize">{auditType?.replace('_', ' ') ?? 'N/A'}</div>
        </div>
        <div className="bg-[#0a0e27] border border-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Chain</div>
          <div className="text-white text-sm capitalize">{chain}</div>
        </div>
        <div className="bg-[#0a0e27] border border-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Completed</div>
          <div className="text-white text-sm">{formatDate(completedAt)}</div>
        </div>
      </div>

      {/* Independence Declaration */}
      <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[#00ff41] text-sm font-semibold">⚖ Independence Declaration</span>
          {requestedByFid && (
            <span className="text-xs text-gray-500">· Requested by FID:{requestedByFid}</span>
          )}
        </div>
        <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed">
          {declaration.text}
        </pre>
      </div>

    </div>
  );
}
