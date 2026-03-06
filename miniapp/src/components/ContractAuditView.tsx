"use client";

import { Vulnerability } from '~/lib/types';
import { Verdict, FindingCount, IndependenceDeclaration } from '~/lib/report-builder';
import { AuditReport } from '~/lib/types';
import ReportHeader from './ReportHeader';
import ReportDownload from './ReportDownload';

// ─── Severity Bar ─────────────────────────────────────────────────────────────

function SeverityBar({ findingCount }: { findingCount: FindingCount }) {
  const total = Object.values(findingCount).reduce((a, b) => a + b, 0);
  const bars = [
    { key: 'critical', label: 'CRITICAL', color: 'bg-red-500',    count: findingCount.critical },
    { key: 'high',     label: 'HIGH',     color: 'bg-orange-500', count: findingCount.high },
    { key: 'medium',   label: 'MEDIUM',   color: 'bg-yellow-500', count: findingCount.medium },
    { key: 'low',      label: 'LOW',      color: 'bg-green-500',  count: findingCount.low },
    { key: 'info',     label: 'INFO',     color: 'bg-gray-500',   count: findingCount.info },
  ];

  return (
    <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-5">
      <h3 className="text-white font-semibold mb-4">Findings Summary</h3>

      {/* Count badges */}
      <div className="flex flex-wrap gap-3 mb-4">
        {bars.map(({ key, label, color, count }) => (
          <div key={key} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-sm ${color}`} />
            <span className="text-gray-400 text-sm">{label}</span>
            <span className="font-bold text-white text-lg">{count}</span>
          </div>
        ))}
      </div>

      {/* Stacked bar */}
      {total > 0 && (
        <div className="flex h-3 rounded-full overflow-hidden gap-px">
          {bars.map(({ key, color, count }) =>
            count > 0 ? (
              <div
                key={key}
                className={color}
                style={{ width: `${(count / total) * 100}%` }}
                title={`${count} ${key}`}
              />
            ) : null
          )}
        </div>
      )}

      {total === 0 && (
        <div className="text-[#00ff41] text-sm">✓ Zero findings — contract is clean</div>
      )}
    </div>
  );
}

// ─── Finding Card ─────────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, { border: string; badge: string; icon: string }> = {
  CRITICAL: { border: 'border-red-500/50',    badge: 'bg-red-500/20 text-red-400',      icon: '🔴' },
  HIGH:     { border: 'border-orange-500/50', badge: 'bg-orange-500/20 text-orange-400', icon: '🟠' },
  MEDIUM:   { border: 'border-yellow-500/50', badge: 'bg-yellow-500/20 text-yellow-400', icon: '🟡' },
  LOW:      { border: 'border-green-500/50',  badge: 'bg-green-500/20 text-green-400',   icon: '🟢' },
  INFO:     { border: 'border-gray-600',       badge: 'bg-gray-700 text-gray-400',        icon: 'ℹ️' },
};

function FindingItem({ finding, index }: { finding: Vulnerability; index: number }) {
  const style = SEVERITY_STYLES[finding.severity] ?? SEVERITY_STYLES.INFO;

  return (
    <div className={`bg-[#0a0e27] border rounded-lg p-5 ${style.border}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${style.badge}`}>
            {style.icon} {finding.severity}
          </span>
          <h4 className="text-white font-semibold">{finding.title}</h4>
        </div>
        <div className="text-xs text-gray-500 shrink-0">#{index + 1}</div>
      </div>

      <p className="text-gray-300 text-sm mb-3 leading-relaxed">{finding.description}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        {finding.location && finding.location !== 'Unknown' && (
          <div>
            <span className="text-gray-500">Location: </span>
            <span className="text-gray-300 font-mono">{finding.location}</span>
          </div>
        )}
        {finding.cvssScore > 0 && (
          <div>
            <span className="text-gray-500">CVSS: </span>
            <span className="text-gray-300">{finding.cvssScore.toFixed(1)}</span>
          </div>
        )}
        {finding.analyzer && (
          <div>
            <span className="text-gray-500">Analyzer: </span>
            <span className="text-gray-300">{finding.analyzer}</span>
          </div>
        )}
        {finding.confidence && (
          <div>
            <span className="text-gray-500">Confidence: </span>
            <span className="text-gray-300">{Math.round(finding.confidence * 100)}%</span>
          </div>
        )}
      </div>

      {finding.exploitScenario && finding.exploitScenario !== 'See description' && (
        <div className="mt-3 p-3 bg-red-500/5 border border-red-500/20 rounded">
          <div className="text-xs text-red-400 font-semibold mb-1">Attack Scenario</div>
          <div className="text-sm text-gray-300">{finding.exploitScenario}</div>
        </div>
      )}

      {finding.aiSuggestion && (
        <div className="mt-3 p-3 bg-[#00ff41]/5 border border-[#00ff41]/20 rounded">
          <div className="text-xs text-[#00ff41] font-semibold mb-1">Recommendation</div>
          <div className="text-sm text-gray-300">{finding.aiSuggestion}</div>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface ContractAuditViewProps {
  auditId: string;
  targetValue: string;
  targetType?: string;
  auditType?: string;
  chain?: string;
  requestedByFid?: number;
  completedAt?: string;
  verdict: Verdict;
  findingCount: FindingCount;
  report: AuditReport;
  declaration: IndependenceDeclaration;
  markdownReport: string;
}

export default function ContractAuditView({
  auditId,
  targetValue,
  targetType,
  auditType,
  chain,
  requestedByFid,
  completedAt,
  verdict,
  findingCount,
  report,
  declaration,
  markdownReport,
}: ContractAuditViewProps) {
  const vulnerabilities = report.vulnerabilities ?? [];

  // Sort: critical first, then high, medium, low, info
  const severityOrder: Record<string, number> = {
    CRITICAL: 5, HIGH: 4, MEDIUM: 3, LOW: 2, INFO: 1,
  };
  const sorted = [...vulnerabilities].sort(
    (a, b) => (severityOrder[b.severity] ?? 0) - (severityOrder[a.severity] ?? 0)
  );

  return (
    <div className="space-y-6">

      {/* Header — verdict banner + meta + independence declaration */}
      <ReportHeader
        auditId={auditId}
        targetValue={targetValue}
        targetType={targetType}
        auditType={auditType}
        chain={chain}
        requestedByFid={requestedByFid}
        completedAt={completedAt}
        verdict={verdict}
        declaration={declaration}
      />

      {/* Severity Summary Bar */}
      <SeverityBar findingCount={findingCount} />

      {/* Findings List */}
      <div className="space-y-4">
        <h3 className="text-white font-semibold text-lg">
          Detailed Findings
          <span className="text-gray-500 font-normal text-base ml-2">
            ({vulnerabilities.length} total)
          </span>
        </h3>

        {sorted.length === 0 ? (
          <div className="bg-[#1a1f3a] border border-[#00ff41]/30 rounded-lg p-8 text-center">
            <div className="text-4xl mb-3">✅</div>
            <div className="text-[#00ff41] font-semibold text-lg mb-2">No Vulnerabilities Detected</div>
            <div className="text-gray-400 text-sm max-w-md mx-auto">
              The contract passed all analysis checks including static analysis,
              symbolic execution, and HexStrike 12-agent intelligence.
            </div>
          </div>
        ) : (
          sorted.map((v, i) => (
            <FindingItem key={v.id} finding={v} index={i} />
          ))
        )}
      </div>

      {/* Download + Share */}
      <ReportDownload
        auditId={auditId}
        targetValue={targetValue}
        verdict={verdict}
        report={report}
        declaration={declaration}
        findingCount={findingCount}
        markdownReport={markdownReport}
      />

    </div>
  );
}
