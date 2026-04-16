"use client";

import { useState, useRef, useEffect } from 'react';
import type { Vulnerability } from '~/lib/types';

export type FindingStatus = 'open' | 'acknowledged' | 'fixed' | 'wont_fix' | 'false_positive';

export interface FindingCardProps {
  finding: Vulnerability;
  expanded?: boolean;
  onStatusChange?: (status: FindingStatus) => void;
  onAssign?: (userId: string) => void;
  className?: string;
}

export function FindingCard({
  finding,
  expanded: initialExpanded = false,
  onStatusChange,
  onAssign,
  className = '',
}: FindingCardProps) {
  const [expanded, setExpanded] = useState(initialExpanded);
  const [status, setStatus] = useState<FindingStatus>(
    (finding.status as FindingStatus) || 'open'
  );
  const cardRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useRef(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    prefersReducedMotion.current = mediaQuery.matches;
  }, []);

  const getSeverityConfig = (severity: string) => {
    const configs: Record<string, {
      bg: string;
      border: string;
      text: string;
      icon: string;
    }> = {
      CRITICAL: {
        bg: 'bg-red-500/10',
        border: 'border-red-500',
        text: 'text-red-500',
        icon: '🚨',
      },
      HIGH: {
        bg: 'bg-orange-500/10',
        border: 'border-orange-500',
        text: 'text-orange-500',
        icon: '⚠️',
      },
      MEDIUM: {
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500',
        text: 'text-yellow-500',
        icon: '⚡',
      },
      LOW: {
        bg: 'bg-blue-500/10',
        border: 'border-blue-500',
        text: 'text-blue-500',
        icon: '📝',
      },
      INFO: {
        bg: 'bg-gray-500/10',
        border: 'border-gray-500',
        text: 'text-gray-500',
        icon: 'ℹ️',
      },
    };
    return configs[severity.toUpperCase()] || configs.INFO;
  };

  const severityConfig = getSeverityConfig(finding.severity);

  const handleStatusChange = (newStatus: FindingStatus) => {
    setStatus(newStatus);
    onStatusChange?.(newStatus);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setExpanded(!expanded);
    }
  };

  return (
    <article
      ref={cardRef}
      className={`bg-[#1a1f3a] border ${severityConfig.border} rounded-lg overflow-hidden ${className}`}
      aria-labelledby={`finding-title-${finding.id}`}
    >
      <div
        className="flex items-start gap-2 sm:gap-4 p-3 sm:p-4 cursor-pointer hover:bg-[#1a1f3a]/80 focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-inset"
        onClick={() => setExpanded(!expanded)}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        aria-controls={`finding-details-${finding.id}`}
      >
        <div className="flex-shrink-0 text-xl sm:text-2xl" aria-hidden="true">{severityConfig.icon}</div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-1">
            <SeverityBadge severity={finding.severity} config={severityConfig} />
            <span className="text-xs text-gray-500">
              CVSS {finding.cvssScore?.toFixed(1) || 'N/A'}
            </span>
            {finding.confidence !== undefined && (
              <ConfidenceIndicator confidence={finding.confidence} />
            )}
          </div>

          <h3 
            id={`finding-title-${finding.id}`}
            className="text-base sm:text-lg font-bold text-white truncate"
          >
            {finding.title}
          </h3>

          {!expanded && (
            <p className="text-sm text-gray-400 truncate mt-1">
              {finding.description}
            </p>
          )}

          {finding.location && (
            <div className="text-xs text-gray-500 mt-1 font-mono truncate">
              {finding.location}
            </div>
          )}
        </div>

        <div className="flex-shrink-0 hidden sm:block">
          <StatusBadge status={status} />
        </div>

        <div 
          className="flex-shrink-0 text-gray-500 transition-transform duration-200"
          aria-hidden="true"
          style={{ 
            transform: !prefersReducedMotion.current && expanded ? 'rotate(90deg)' : 'rotate(0deg)'
          }}
        >
          {expanded ? '▼' : '▶'}
        </div>
      </div>

      {expanded && (
        <div 
          id={`finding-details-${finding.id}`}
          className="border-t border-gray-700 p-3 sm:p-4 space-y-4"
          role="region"
          aria-label="Finding details"
        >
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Description</h4>
            <p className="text-gray-300 text-sm sm:text-base">{finding.description}</p>
          </div>

          {finding.exploitScenario && (
            <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-3 sm:p-4">
              <h4 className="text-sm font-semibold text-red-400 mb-2">
                🔓 Exploit Scenario
              </h4>
              <p className="text-sm text-gray-300 font-mono">
                {finding.exploitScenario}
              </p>
            </div>
          )}

          {finding.aiSuggestion && (
            <AISuggestionSection suggestion={finding.aiSuggestion} />
          )}

          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Expected Outcome</h4>
            <p className="text-sm sm:text-base text-[#00ff41]">{finding.expectedOutcome}</p>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 pt-2">
            <StatusSelector status={status} onChange={handleStatusChange} />
            {onAssign && <AssignButton onAssign={onAssign} />}
          </div>

          {finding.analyzer && (
            <div className="text-xs text-gray-500">
              Detected by: <span className="text-gray-400">{finding.analyzer}</span>
            </div>
          )}

          <div className="sm:hidden">
            <StatusBadge status={status} />
          </div>
        </div>
      )}
    </article>
  );
}

function SeverityBadge({
  severity,
  config,
}: {
  severity: string;
  config: { bg: string; border: string; text: string };
}) {
  return (
    <span
      className={`px-2 py-0.5 rounded border text-xs font-bold ${config.bg} ${config.border} ${config.text}`}
      aria-label={`Severity: ${severity}`}
    >
      {severity.toUpperCase()}
    </span>
  );
}

function StatusBadge({ status }: { status: FindingStatus }) {
  const configs: Record<FindingStatus, { bg: string; text: string; label: string }> = {
    open: { bg: 'bg-yellow-500/20', text: 'text-yellow-500', label: 'Open' },
    acknowledged: { bg: 'bg-blue-500/20', text: 'text-blue-500', label: 'Ack' },
    fixed: { bg: 'bg-green-500/20', text: 'text-green-500', label: 'Fixed' },
    wont_fix: { bg: 'bg-gray-500/20', text: 'text-gray-500', label: "Won't Fix" },
    false_positive: { bg: 'bg-purple-500/20', text: 'text-purple-500', label: 'FP' },
  };

  const config = configs[status];

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}
      aria-label={`Status: ${config.label}`}
    >
      {config.label}
    </span>
  );
}

function ConfidenceIndicator({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  const color = percentage >= 80 ? 'text-green-500' : percentage >= 50 ? 'text-yellow-500' : 'text-red-500';

  return (
    <span className={`text-xs ${color}`} aria-label={`Confidence: ${percentage}%`}>
      {percentage}%
    </span>
  );
}

function AISuggestionSection({ suggestion }: { suggestion: string }) {
  return (
    <div className="bg-[#00ff41]/5 border border-[#00ff41]/30 rounded-lg p-3 sm:p-4">
      <h4 className="text-sm font-semibold text-[#00ff41] mb-2">
        🤖 AI Suggestion
      </h4>
      <p className="text-sm text-gray-300">{suggestion}</p>
    </div>
  );
}

function StatusSelector({
  status,
  onChange,
}: {
  status: FindingStatus;
  onChange: (status: FindingStatus) => void;
}) {
  const options: FindingStatus[] = ['open', 'acknowledged', 'fixed', 'wont_fix', 'false_positive'];

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="status-select" className="text-sm text-gray-400">
        Status:
      </label>
      <select
        id="status-select"
        value={status}
        onChange={(e) => onChange(e.target.value as FindingStatus)}
        className="bg-[#0a0e27] border border-gray-700 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-[#00ff41]"
        aria-label="Change finding status"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
          </option>
        ))}
      </select>
    </div>
  );
}

function AssignButton({ onAssign }: { onAssign: (userId: string) => void }) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onAssign('current-user');
      }}
      className="text-sm text-[#00ff41] hover:text-[#00ff41]/80 focus:outline-none focus:ring-2 focus:ring-[#00ff41] rounded px-2 py-1"
      aria-label="Assign this finding"
    >
      👤 Assign
    </button>
  );
}

export default FindingCard;
