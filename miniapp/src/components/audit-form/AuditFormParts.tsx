"use client";

import { AuditType, PaymentToken } from '~/lib/types';

// ─── Pricing ──────────────────────────────────────────────────────────────────

export const PRICES: Record<AuditType, number> = {
  contract_basic: 79,
  contract_deep:  199,
  miniapp:        79,
  full_stack:     349,
};

export const AUDIT_TYPE_LABELS: Record<AuditType, { title: string; description: string; badge?: string }> = {
  contract_basic: {
    title: 'Contract Basic',
    description: 'Slither + Mythril static analysis. Severity-ranked findings, independence declaration.',
  },
  contract_deep: {
    title: 'Contract Deep',
    description: 'Full HexStrike 12-agent analysis + CVE matching + attack chains. Most thorough.',
    badge: 'MOST POPULAR',
  },
  miniapp: {
    title: 'Miniapp Audit',
    description: 'UI surface audit with agent-browser. Visual proof screenshots before/after.',
  },
  full_stack: {
    title: 'Full Stack',
    description: 'Miniapp UI audit + all smart contracts. Competitive with human audit firms.',
    badge: 'COMPREHENSIVE',
  },
};

export const PAYMENT_LABELS: Record<PaymentToken, string> = {
  eth:  'ETH',
  usdc: 'USDC',
  bnkr: 'BNKR (20% off)',
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function displayPrice(auditType: AuditType, token: PaymentToken): string {
  const base = PRICES[auditType];
  const final = token === 'bnkr' ? Math.round(base * 0.8) : base;
  return `$${final}`;
}

export function defaultAuditType(targetType: string): AuditType {
  if (targetType === 'miniapp_url') return 'miniapp';
  if (targetType === 'contract_evm' || targetType === 'contract_solana') return 'contract_deep';
  if (targetType === 'github_repo') return 'contract_basic';
  return 'contract_basic';
}

// ─── DetectionBadge ───────────────────────────────────────────────────────────

export function DetectionBadge({ type }: { type: string }) {
  const labels: Record<string, { text: string; color: string }> = {
    contract_evm:    { text: '⬡ EVM Contract · Base',  color: 'text-blue-400 border-blue-400/40 bg-blue-400/10' },
    contract_solana: { text: '◎ Solana Program',        color: 'text-purple-400 border-purple-400/40 bg-purple-400/10' },
    github_repo:     { text: '⌥ GitHub Repository',     color: 'text-gray-300 border-gray-600 bg-gray-800' },
    miniapp_url:     { text: '⬡ Farcaster Miniapp',     color: 'text-green-400 border-green-400/40 bg-green-400/10' },
    resolving:       { text: '⟳ Resolving...',          color: 'text-yellow-400 border-yellow-400/40 bg-yellow-400/10' },
  };
  const label = labels[type];
  if (!label) return null;
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-mono ${label.color}`}>
      {label.text}
    </span>
  );
}

// ─── AuditTypeCard ────────────────────────────────────────────────────────────

export function AuditTypeCard({
  type, selected, token, onClick,
}: {
  type: AuditType; selected: boolean; token: PaymentToken; onClick: () => void;
}) {
  const meta = AUDIT_TYPE_LABELS[type];
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border transition-all ${
        selected
          ? 'border-[#00ff41] bg-[#00ff41]/10'
          : 'border-gray-700 hover:border-gray-500 bg-[#0a0e27]'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-white">{meta.title}</span>
            {meta.badge && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-[#00ff41]/20 text-[#00ff41] font-mono border border-[#00ff41]/30">
                {meta.badge}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-400 leading-snug">{meta.description}</p>
        </div>
        <div className="shrink-0 text-right">
          <div className={`font-bold text-lg ${selected ? 'text-[#00ff41]' : 'text-gray-300'}`}>
            {displayPrice(type, token)}
          </div>
          {token === 'bnkr' && (
            <div className="text-xs text-gray-500 line-through">${PRICES[type]}</div>
          )}
        </div>
      </div>
    </button>
  );
}

// ─── PaymentTokenSelector ─────────────────────────────────────────────────────

export function PaymentTokenSelector({
  selected, onChange,
}: {
  selected: PaymentToken; onChange: (t: PaymentToken) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex gap-3">
        {(Object.keys(PAYMENT_LABELS) as PaymentToken[]).map((token) => (
          <button
            key={token}
            type="button"
            onClick={() => onChange(token)}
            className={`flex-1 py-2.5 px-3 rounded-lg border text-sm font-semibold transition-all ${
              selected === token
                ? 'border-[#00ff41] bg-[#00ff41]/10 text-[#00ff41]'
                : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            {PAYMENT_LABELS[token]}
          </button>
        ))}
      </div>
      {selected === 'bnkr' && (
        <p className="text-xs text-[#00ff41]/80">
          ✓ 20% community discount applied — supporting the AgentxploiTor ecosystem
        </p>
      )}
    </div>
  );
}
