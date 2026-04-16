"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import type { JobStatus } from '~/lib/types';

export interface DashboardProps {
  workspaceId?: string;
  userId?: string;
  className?: string;
}

interface AuditSummary {
  id: string;
  targetUrl: string;
  status: JobStatus;
  findingsCount: Record<string, number>;
  createdAt: string;
  completedAt?: string;
}

interface DashboardStats {
  activeAudits: number;
  completedToday: number;
  criticalFindings: number;
  totalFindings: number;
}

const AMBIENT_COLORS: Record<JobStatus, string> = {
  pending_payment: 'from-[#0a0e27] to-[#1a0a27]',
  payment_verified: 'from-[#0a0e27] to-[#0a1a27]',
  queued: 'from-[#0a0e27] to-[#1a1a0a]',
  in_progress: 'from-[#0a0e27] to-[#0a271a]',
  completed: 'from-[#0a0e27] to-[#002a10]',
  failed: 'from-[#0a0e27] to-[#2a0a0a]',
  cancelled: 'from-[#0a0e27] to-[#1a1a1a]',
};

export function FocusDashboard({
  workspaceId: _workspaceId = '',
  userId: _userId = '',
  className = '',
}: DashboardProps) {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats>({
    activeAudits: 0,
    completedToday: 0,
    criticalFindings: 0,
    totalFindings: 0,
  });
  const [recentAudits, setRecentAudits] = useState<AuditSummary[]>([]);
  const [focusMode, setFocusMode] = useState(false);
  const [activeAudit, setActiveAudit] = useState<AuditSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true); // kept for mobile toggle
  void _workspaceId; void _userId; void sidebarOpen;
  const prefersReducedMotion = useRef(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    prefersReducedMotion.current = mediaQuery.matches;
    
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [statsRes, auditsRes] = await Promise.all([
        fetch('/api/dashboard/stats'),
        fetch('/api/dashboard/audits?limit=10'),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (auditsRes.ok) {
        const auditsData = await auditsRes.json();
        setRecentAudits(auditsData.audits || []);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'f' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setFocusMode((prev) => !prev);
      }
      if (e.key === 'Escape' && focusMode) {
        setFocusMode(false);
        setActiveAudit(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusMode]);

  const getAmbientColor = () => {
    if (activeAudit) {
      return AMBIENT_COLORS[activeAudit.status];
    }
    if (stats.criticalFindings > 0) {
      return 'from-[#0a0e27] to-[#2a0a0a]';
    }
    if (stats.activeAudits > 0) {
      return 'from-[#0a0e27] to-[#0a271a]';
    }
    return 'from-[#0a0e27] to-[#1a1f3a]';
  };

  const handleAuditClick = (audit: AuditSummary) => {
    if (focusMode) {
      setActiveAudit(audit);
    } else {
      router.push(`/audit/${audit.id}`);
    }
  };

  if (isLoading) {
    return (
      <div 
        className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white flex items-center justify-center"
        role="status"
        aria-live="polite"
        aria-label="Loading dashboard"
      >
        <div className="text-center">
          <div className={`inline-block text-4xl mb-4 ${!prefersReducedMotion.current ? 'animate-spin' : ''}`}>⏳</div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen bg-gradient-to-b ${getAmbientColor()} text-white transition-colors duration-1000 ${className}`}
    >
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {!focusMode && !activeAudit && (
          <>
            <header className="mb-12">
              <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl sm:text-3xl font-bold">Dashboard</h1>
                <button
                  onClick={() => setFocusMode(true)}
                  className="text-sm text-gray-500 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-2 focus:ring-offset-[#0a0e27] rounded px-2 py-1"
                  title="Focus Mode (⌘F)"
                  aria-label="Enter Focus Mode"
                >
                  Focus Mode
                </button>
              </div>
              <p className="text-gray-400">
                Your security audit command center
              </p>
            </header>

            <StatsGrid stats={stats} />

            <section className="mt-8 sm:mt-12" aria-labelledby="recent-audits-heading">
              <h2 id="recent-audits-heading" className="text-lg sm:text-xl font-semibold mb-4">Recent Audits</h2>
              <div className="space-y-3" role="list" aria-label="Recent security audits">
                {recentAudits.map((audit) => (
                  <AuditRow
                    key={audit.id}
                    audit={audit}
                    onClick={() => handleAuditClick(audit)}
                  />
                ))}
                {recentAudits.length === 0 && (
                  <div className="text-center py-8 text-gray-500" role="status">
                    No audits yet. Start your first security audit.
                  </div>
                )}
              </div>
            </section>

            <div className="mt-8">
              <button
                onClick={() => router.push('/request')}
                className="w-full py-4 bg-[#00ff41] text-[#0a0e27] font-bold rounded-lg hover:bg-[#00dd35] transition-colors focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-2 focus:ring-offset-[#0a0e27]"
                aria-label="Start a new security audit"
              >
                Start New Audit
              </button>
            </div>
          </>
        )}

        {focusMode && !activeAudit && (
          <FocusModeView
            audits={recentAudits}
            onSelect={setActiveAudit}
            onExit={() => setFocusMode(false)}
          />
        )}

        {focusMode && activeAudit && (
          <ActiveAuditView
            audit={activeAudit}
            onBack={() => setActiveAudit(null)}
          />
        )}

        <div className="fixed bottom-4 right-4 text-xs text-gray-600" aria-hidden="true">
          Press ⌘F for focus mode
        </div>
      </div>
    </div>
  );
}

function StatsGrid({ stats }: { stats: DashboardStats }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4" role="region" aria-label="Dashboard statistics">
      <StatCard
        label="Active"
        value={stats.activeAudits}
        color="text-blue-400"
      />
      <StatCard
        label="Completed Today"
        value={stats.completedToday}
        color="text-green-400"
      />
      <StatCard
        label="Critical"
        value={stats.criticalFindings}
        color="text-red-400"
        highlight={stats.criticalFindings > 0}
      />
      <StatCard
        label="Total Findings"
        value={stats.totalFindings}
        color="text-yellow-400"
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
  highlight = false,
}: {
  label: string;
  value: number;
  color: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`bg-[#1a1f3a] border ${
        highlight ? 'border-red-500/50 animate-pulse' : 'border-gray-800'
      } rounded-lg p-3 sm:p-4`}
      role="stat"
      aria-label={`${label}: ${value}`}
    >
      <div className={`text-xl sm:text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  );
}

function AuditRow({
  audit,
  onClick,
}: {
  audit: AuditSummary;
  onClick: () => void;
}) {
  const statusColors: Record<string, string> = {
    completed: 'text-green-500',
    in_progress: 'text-blue-500',
    failed: 'text-red-500',
    queued: 'text-yellow-500',
  };

  const totalFindings = Object.values(audit.findingsCount).reduce(
    (a, b) => a + b,
    0
  );

  return (
    <div
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-3 sm:p-4 hover:border-gray-700 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-2 focus:ring-offset-[#0a0e27]"
      role="listitem"
      tabIndex={0}
      aria-label={`Audit: ${audit.targetUrl}, Status: ${audit.status}, Findings: ${totalFindings}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-semibold truncate">{audit.targetUrl}</div>
          <div className="text-sm text-gray-500">
            {new Date(audit.createdAt).toLocaleDateString()}
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <div className="text-sm">
            <span className="text-gray-500 sm:hidden">Findings:</span>{' '}
            <span className="text-white">{totalFindings}</span>
          </div>
          <div className={`text-sm capitalize ${statusColors[audit.status] || 'text-gray-500'}`} aria-label={`Status: ${audit.status}`}>
            {audit.status.replace('_', ' ')}
          </div>
        </div>
      </div>
    </div>
  );
}

function FocusModeView({
  audits,
  onSelect,
  onExit,
}: {
  audits: AuditSummary[];
  onSelect: (audit: AuditSummary) => void;
  onExit: () => void;
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, audits.length - 1));
      } else if (e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        if (audits[selectedIndex]) {
          onSelect(audits[selectedIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [audits, selectedIndex, onSelect]);

  return (
    <div className="py-4 sm:py-8" role="region" aria-label="Focus Mode">
      <div className="text-center mb-6 sm:mb-8">
        <h2 className="text-xl sm:text-2xl font-bold mb-2">Focus Mode</h2>
        <p className="text-gray-400 text-sm" aria-hidden="true">
          Use ↑↓ or j/k to navigate, Enter to select, Esc to exit
        </p>
      </div>

      <div className="space-y-2" role="listbox" aria-label="Select an audit" tabIndex={0}>
        {audits.map((audit, index) => (
          <div
            key={audit.id}
            onClick={() => onSelect(audit)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(audit);
              }
            }}
            role="option"
            aria-selected={index === selectedIndex}
            tabIndex={0}
            className={`p-3 sm:p-4 rounded-lg cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-2 focus:ring-offset-[#0a0e27] ${
              index === selectedIndex
                ? 'bg-[#00ff41]/10 border border-[#00ff41]'
                : 'bg-[#1a1f3a] border border-gray-800'
            }`}
          >
            <div className="font-semibold">{audit.targetUrl}</div>
            <div className="text-sm text-gray-400 capitalize">
              {audit.status.replace('_', ' ')}
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={onExit}
        className="mt-6 w-full py-2 text-gray-500 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-[#00ff41] rounded"
        aria-label="Exit Focus Mode"
      >
        Press Esc to exit
      </button>
    </div>
  );
}

function ActiveAuditView({
  audit,
  onBack,
}: {
  audit: AuditSummary;
  onBack: () => void;
}) {
  return (
    <div className="py-4 sm:py-8" role="region" aria-label={`Active Audit: ${audit.targetUrl}`}>
      <button
        onClick={onBack}
        className="text-gray-500 hover:text-gray-300 mb-4 focus:outline-none focus:ring-2 focus:ring-[#00ff41] rounded px-2 py-1"
        aria-label="Go back to audit list"
      >
        ← Back
      </button>

      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-4 sm:p-6">
        <h2 className="text-lg sm:text-xl font-bold mb-2">{audit.targetUrl}</h2>
        <div className="text-sm text-gray-400 mb-4">
          Status: <span className="capitalize">{audit.status.replace('_', ' ')}</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6" role="list" aria-label="Findings by severity">
          {Object.entries(audit.findingsCount).map(([severity, count]) => (
            <div key={severity} className="text-center" role="listitem">
              <div className="text-xl sm:text-2xl font-bold">{count}</div>
              <div className="text-xs text-gray-500 uppercase">{severity}</div>
            </div>
          ))}
        </div>

        <button
          onClick={() => (window.location.href = `/audit/${audit.id}`)}
          className="w-full py-3 bg-[#00ff41] text-[#0a0e27] font-bold rounded-lg hover:bg-[#00dd35] transition-colors focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-2 focus:ring-offset-[#1a1f3a]"
          aria-label={`View full report for ${audit.targetUrl}`}
        >
          View Full Report →
        </button>
      </div>
    </div>
  );
}

export default FocusDashboard;
