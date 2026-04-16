"use client";

import { Vulnerability } from '~/lib/types';
import { Verdict, FindingCount, IndependenceDeclaration } from '~/lib/report-builder';
import { AuditReport } from '~/lib/types';
import ReportHeader from './ReportHeader';
import ReportDownload from './ReportDownload';
import SolanaAuditResult from './SolanaAuditResult';

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

// ─── On-Chain State Panel ──────────────────────────────────────────────────────

function OnChainStatePanel({ state, chain }: { state: OnChainState; chain?: string }) {
  return (
    <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-5">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-[#00ff41]">⛓</span> On-Chain State Analysis
        {chain && <span className="text-xs text-gray-500 font-mono">({chain})</span>}
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <div className="text-gray-500 mb-1">Bytecode Size</div>
          <div className="text-white font-mono">{state.bytecodeLength.toLocaleString()} bytes</div>
        </div>

        <div>
          <div className="text-gray-500 mb-1">Proxy Pattern</div>
          {state.isProxy ? (
            <div className="text-yellow-400 font-medium">{state.proxyType.toUpperCase()}</div>
          ) : (
            <div className="text-[#00ff41]">None (Direct)</div>
          )}
        </div>

        {state.implementation && (
          <div>
            <div className="text-gray-500 mb-1">Implementation</div>
            <div className="text-gray-300 font-mono text-xs">{state.implementation.slice(0, 10)}...{state.implementation.slice(-6)}</div>
          </div>
        )}

        <div>
          <div className="text-gray-500 mb-1">Admin / Owner</div>
          {state.admin ? (
            <div className="text-gray-300 font-mono text-xs">{state.admin.slice(0, 10)}...{state.admin.slice(-6)}</div>
          ) : (
            <div className="text-[#00ff41]">No admin detected</div>
          )}
        </div>
      </div>

      {state.isProxy && state.implementation && (
        <div className="mt-3 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded text-xs text-yellow-400">
          ⚠️ This is a proxy contract. Analysis covers the proxy, not the implementation.
          Implementation: <span className="font-mono">{state.implementation}</span>
        </div>
      )}
    </div>
  );
}

// ─── Trace Visualization ──────────────────────────────────────────────────────

interface TraceCall {
  from: string;
  to: string;
  value: string;
  gasUsed: string;
  type: string;
  error?: string;
  calls?: TraceCall[];
}

interface TraceData {
  txHash: string;
  totalGasUsed: string;
  callTree: TraceCall;
  reentrancyFlags: string[];
  externalCallsBeforeState: Array<{ observation: string }>;
}

function TraceCallNode({ call, depth = 0 }: { call: TraceCall; depth?: number }) {
  const typeColors: Record<string, string> = {
    CALL: 'text-blue-400',
    STATICCALL: 'text-green-400',
    DELEGATECALL: 'text-yellow-400',
    CREATE: 'text-purple-400',
  };

  return (
    <div className={`${depth > 0 ? 'ml-4 border-l border-gray-700 pl-3' : ''}`}>
      <div className="flex items-center gap-2 text-xs py-1">
        <span className={`font-mono font-bold ${typeColors[call.type] || 'text-gray-400'}`}>
          {call.type}
        </span>
        <span className="text-gray-400 font-mono">
          {call.from.slice(0, 6)}...{call.from.slice(-4)} → {call.to.slice(0, 6)}...{call.to.slice(-4)}
        </span>
        <span className="text-gray-500">gas: {call.gasUsed}</span>
        {call.error && <span className="text-red-400">✗ {call.error}</span>}
      </div>
      {call.calls?.map((sub, i) => (
        <TraceCallNode key={i} call={sub} depth={depth + 1} />
      ))}
    </div>
  );
}

function TraceVisualization({ trace }: { trace: TraceData }) {
  return (
    <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-5">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-blue-400">🔬</span> Transaction Trace
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <div className="text-gray-500 mb-1">Transaction</div>
          <div className="text-gray-300 font-mono text-xs">{trace.txHash.slice(0, 16)}...{trace.txHash.slice(-8)}</div>
        </div>
        <div>
          <div className="text-gray-500 mb-1">Total Gas</div>
          <div className="text-white font-mono">{trace.totalGasUsed}</div>
        </div>
      </div>

      {trace.reentrancyFlags.length > 0 && (
        <div className="mb-4 p-3 bg-red-500/5 border border-red-500/20 rounded text-xs">
          <div className="text-red-400 font-semibold mb-1">⚠ Reentrancy Detected</div>
          {trace.reentrancyFlags.map((flag, i) => (
            <div key={i} className="text-red-300">{flag}</div>
          ))}
        </div>
      )}

      {trace.externalCallsBeforeState.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded text-xs">
          <div className="text-yellow-400 font-semibold mb-1">⚠ External Calls Before State Update</div>
          {trace.externalCallsBeforeState.map((finding, i) => (
            <div key={i} className="text-yellow-300">{finding.observation}</div>
          ))}
        </div>
      )}

      <div className="bg-[#0a0e27] rounded p-3 overflow-x-auto">
        <TraceCallNode call={trace.callTree} />
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface OnChainState {
  bytecodeLength: number;
  isProxy: boolean;
  proxyType: string;
  implementation: string | null;
  admin: string | null;
}

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
  onChainState?: OnChainState | null;
  trace?: TraceData | null;
  solanaData?: {
    programId: string;
    dataSize: number;
    isUpgradeable: boolean;
    upgradeAuthority: string | null;
    owner: string;
  } | null;
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
  onChainState,
  trace,
  solanaData,
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

      {/* On-Chain State Analysis (from QuickNode) */}
      {onChainState && (
        <OnChainStatePanel state={onChainState} chain={chain} />
      )}

      {/* Transaction Trace Visualization (from QuickNode) */}
      {trace && (
        <TraceVisualization trace={trace} />
      )}

      {/* Solana-Specific Audit Result (from QuickNode + HexStrike) */}
      {solanaData && (
        <SolanaAuditResult
          programData={solanaData}
          findings={vulnerabilities
            .filter(v => v.title.toLowerCase().includes('solana') || v.title.toLowerCase().includes('signer') || v.title.toLowerCase().includes('anchor'))
            .map(v => ({ id: v.id, title: v.title, severity: v.severity, description: v.description }))
          }
        />
      )}

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
        targetUrl={targetValue}
        findings={vulnerabilities}
        summary={report.summary ?? {}}
        confidence={report.evaluation?.confidence ?? 0}
        createdAt={completedAt ?? new Date().toISOString()}
        reporterFid={requestedByFid}
      />

    </div>
  );
}
