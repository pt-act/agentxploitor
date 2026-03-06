"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '~/components/ui/Button';
import type { JobSession } from '~/lib/types';

interface AuditStatus extends JobSession {
  progress?: number;
  queuePosition?: number;
  completedAt?: string;
}

export default function AuditStatusPage() {
  const params = useParams();
  const router = useRouter();
  const auditId = params.id as string;
  
  const [audit, setAudit] = useState<AuditStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([
    '> Initializing AgentxploiTor...',
    '> Loading browser perception module...',
    '> Connecting to target...',
  ]);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`/api/audit/status/${auditId}`);
        const data = await response.json();
        
        if (response.ok) {
          setAudit(data);
          
          if (data.status === 'in_progress') {
            setTimeout(() => setLogs(prev => [...prev, '> Scanning for vulnerabilities...']), 1000);
            setTimeout(() => setLogs(prev => [...prev, '> Found potential vulnerability...']), 2000);
            setTimeout(() => setLogs(prev => [...prev, '> Generating exploit...']), 3000);
          }
          
          if (data.status === 'completed') {
            setPolling(false);
          }
        }
      } catch (err) {
        console.error('Error fetching audit status:', err);
      }
    };

    fetchStatus();
    
    if (polling) {
      const interval = setInterval(fetchStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [auditId, router, polling]);

  if (!audit) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-400">Loading audit status...</p>
        </div>
      </div>
    );
  }

  const isCompleted = audit.status === 'completed';
  const isQueued = audit.status === 'queued';
  const isInProgress = audit.status === 'in_progress';

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        
        {/* Header */}
        <div className="mb-8">
          <Button 
            onClick={() => router.push('/')}
            className="mb-4"
          >
            ← Back to Home
          </Button>
          <h1 className="text-3xl font-bold">Audit Status</h1>
          <p className="text-gray-400">ID: {auditId}</p>
        </div>

        {/* Status Card */}
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 mb-6">
          
          {/* Completed Status */}
          {isCompleted && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-[#00ff41] rounded-full flex items-center justify-center">
                    <span className="text-2xl">✓</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-[#00ff41]">Audit Complete</h2>
                    <p className="text-gray-400">Completed at {new Date(audit.completedAt || audit.updatedAt).toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {/* Findings Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-[#0a0e27] border border-red-500/30 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-red-500">{audit.findingsCount?.critical || 0}</div>
                  <div className="text-sm text-gray-400">CRITICAL</div>
                </div>
                <div className="bg-[#0a0e27] border border-orange-500/30 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-orange-500">{audit.findingsCount?.high || 0}</div>
                  <div className="text-sm text-gray-400">HIGH</div>
                </div>
                <div className="bg-[#0a0e27] border border-yellow-500/30 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-yellow-500">{audit.findingsCount?.medium || 0}</div>
                  <div className="text-sm text-gray-400">MEDIUM</div>
                </div>
                <div className="bg-[#0a0e27] border border-gray-500/30 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-gray-400">{audit.findingsCount?.low || 0}</div>
                  <div className="text-sm text-gray-400">LOW</div>
                </div>
              </div>

              <Button 
                onClick={() => router.push(`/audit/${auditId}/results`)}
                className="w-full bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] text-lg py-4"
              >
                View Full Report →
              </Button>
            </div>
          )}

          {/* In Progress Status */}
          {isInProgress && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-[#00ff41]/20 rounded-full flex items-center justify-center">
                  <span className="text-2xl animate-pulse">🤖</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[#00ff41]">Agent Working...</h2>
                  <p className="text-gray-400">Autonomous security audit in progress</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-[#00ff41]">{audit.progress || 0}%</span>
                </div>
                <div className="w-full bg-[#0a0e27] rounded-full h-3">
                  <div 
                    className="bg-[#00ff41] h-3 rounded-full transition-all duration-500"
                    style={{ width: `${audit.progress || 0}%` }}
                  />
                </div>
              </div>

              {/* Live Console */}
              <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4 font-mono text-sm max-h-64 overflow-y-auto">
                {logs.map((log, i) => (
                  <div key={i} className="text-[#00ff41] mb-1">{log}</div>
                ))}
                <div className="text-[#00ff41] animate-pulse">▊</div>
              </div>
            </div>
          )}

          {/* Queued Status */}
          {isQueued && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📋</div>
              <h2 className="text-2xl font-bold mb-2">Audit Queued</h2>
              <p className="text-gray-400">Position in queue: #{audit.queuePosition}</p>
              <p className="text-sm text-gray-500 mt-2">Estimated start: 5 minutes</p>
            </div>
          )}

          {/* Pending Payment Status */}
          {audit.status === 'pending_payment' && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">💳</div>
              <h2 className="text-2xl font-bold mb-2">Payment Required</h2>
              <p className="text-gray-400 mb-4">Complete the payment to start your audit</p>
              <Button 
                onClick={() => router.push('/request')}
                className="mt-4"
              >
                Go to Payment
              </Button>
            </div>
          )}

        </div>

        {/* Info Box */}
        <div className="bg-[#00ff41]/10 border border-[#00ff41] rounded-lg p-4 text-sm">
          <div className="font-semibold text-[#00ff41] mb-2">What's happening?</div>
          <ul className="text-gray-300 space-y-1">
            <li>✓ AgentxploiTor is scanning your code autonomously</li>
            <li>✓ Browser perception will capture visual proof</li>
            <li>✓ Before/after screenshots will be saved</li>
            <li>✓ Self-evaluation will verify confidence</li>
          </ul>
        </div>

      </div>
    </div>
  );
}
