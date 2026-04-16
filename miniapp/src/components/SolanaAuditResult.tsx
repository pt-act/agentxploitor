/**
 * SolanaAuditResult.tsx
 * Solana-specific audit result display.
 * Shows on-chain program data alongside static analysis findings.
 */

"use client";

interface SolanaProgramData {
  programId: string;
  dataSize: number;
  isUpgradeable: boolean;
  upgradeAuthority: string | null;
  owner: string;
}

interface SolanaAuditResultProps {
  programData: SolanaProgramData | null;
  findings: Array<{
    id: string;
    title: string;
    severity: string;
    description: string;
  }>;
}

export default function SolanaAuditResult({ programData, findings }: SolanaAuditResultProps) {
  return (
    <div className="space-y-6">
      {/* On-Chain Program Data */}
      {programData && (
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-5">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <span className="text-purple-400">◎</span> Solana Program Analysis
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-gray-500 mb-1">Program ID</div>
              <div className="text-white font-mono text-xs">
                {programData.programId.slice(0, 12)}...{programData.programId.slice(-8)}
              </div>
            </div>

            <div>
              <div className="text-gray-500 mb-1">Data Size</div>
              <div className="text-white font-mono">{programData.dataSize.toLocaleString()} bytes</div>
            </div>

            <div>
              <div className="text-gray-500 mb-1">Owner Program</div>
              <div className="text-gray-300 font-mono text-xs">
                {programData.owner.slice(0, 12)}...{programData.owner.slice(-6)}
              </div>
            </div>

            <div>
              <div className="text-gray-500 mb-1">Upgradeable</div>
              {programData.isUpgradeable ? (
                <div className="text-yellow-400 font-medium">Yes</div>
              ) : (
                <div className="text-[#00ff41]">No (Immutable)</div>
              )}
            </div>

            {programData.upgradeAuthority && (
              <div>
                <div className="text-gray-500 mb-1">Upgrade Authority</div>
                <div className="text-gray-300 font-mono text-xs">
                  {programData.upgradeAuthority.slice(0, 12)}...{programData.upgradeAuthority.slice(-6)}
                </div>
              </div>
            )}
          </div>

          {programData.isUpgradeable && programData.upgradeAuthority && (
            <div className="mt-3 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded text-xs text-yellow-400">
              ⚠️ This program is upgradeable. The upgrade authority can modify the program at any time.
              Verify the authority is a multisig or timelock before trusting.
            </div>
          )}
        </div>
      )}

      {/* Solana-Specific Findings */}
      {findings.length > 0 && (
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-5">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <span className="text-purple-400">🔍</span> Solana-Specific Checks
          </h3>

          <div className="space-y-3">
            {findings.map((finding) => {
              const severityColors: Record<string, string> = {
                CRITICAL: 'border-red-500/50 bg-red-500/5',
                HIGH: 'border-orange-500/50 bg-orange-500/5',
                MEDIUM: 'border-yellow-500/50 bg-yellow-500/5',
                LOW: 'border-green-500/50 bg-green-500/5',
                INFO: 'border-gray-600 bg-gray-800/50',
              };

              return (
                <div
                  key={finding.id}
                  className={`border rounded-lg p-3 ${severityColors[finding.severity] || severityColors.INFO}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono font-bold text-gray-400">{finding.severity}</span>
                    <span className="text-sm text-white font-medium">{finding.title}</span>
                  </div>
                  <p className="text-xs text-gray-400">{finding.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Solana Analyzer Reference */}
      <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4 text-xs text-gray-500">
        <div className="font-mono">
          <span className="text-purple-400">SolanaAnalyzerAdapter</span> checks:
          SOL-001 (Signer verification) · SOL-002 (Account ownership) · SOL-003 (PDA validation) ·
          SOL-004 (CPI safety) · SOL-005 (Reentrancy) · SOL-006 (Integer overflow) ·
          SOL-007 (Account data) · SOL-008 (Anchor constraints)
        </div>
      </div>
    </div>
  );
}
