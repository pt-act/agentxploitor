"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '~/components/ui/Button';
import type { Vulnerability, AuditReport } from '~/lib/types';
import DisclosureTemplate from '~/components/DisclosureTemplate';
import ReportDownload from '~/components/ReportDownload';

export default function AuditResultsPage() {
  const params = useParams();
  const router = useRouter();
  const auditId = params.id as string;
  
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDisclosure, setShowDisclosure] = useState(false);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`/api/audit/results/${auditId}`);
        const data = await response.json();
        
        if (!response.ok) {
          if (data.status && data.status !== 'completed') {
            router.push(`/audit/${auditId}`);
            return;
          }
          setError(data.error || 'Failed to load results');
          return;
        }
        
        setReport(data);
      } catch (err) {
        setError('Failed to load audit results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [auditId, router]);

  const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'text-red-500 border-red-500 bg-red-500/10';
      case 'HIGH': return 'text-orange-500 border-orange-500 bg-orange-500/10';
      case 'MEDIUM': return 'text-yellow-500 border-yellow-500 bg-yellow-500/10';
      default: return 'text-gray-500 border-gray-500 bg-gray-500/10';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-400">Loading audit results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-red-400">{error}</p>
          <Button onClick={() => router.push('/')} className="mt-4">
            Return Home
          </Button>
        </div>
      </div>
    );
  }

  if (!report) {
    return null;
  }

  const criticalCount = report.summary?.CRITICAL || 0;
  const highCount = report.summary?.HIGH || 0;
  const mediumCount = report.summary?.MEDIUM || 0;
  const lowCount = report.summary?.LOW || 0;
  const totalFindings = criticalCount + highCount + mediumCount + lowCount;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        
        {/* Header */}
        <div className="mb-8">
          <Button 
            onClick={() => router.push(`/audit/${auditId}`)}
            className="mb-4"
          >
            ← Back to Status
          </Button>
          <h1 className="text-3xl font-bold mb-2">Security Audit Report</h1>
          <p className="text-gray-400">Audit ID: {auditId}</p>
          <p className="text-gray-500 text-sm">Target: {report.targetUrl}</p>
        </div>

        {/* Summary */}
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <div className="text-sm text-gray-400 mb-1">Status</div>
              <div className="text-xl font-bold text-[#00ff41]">✓ Complete</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Vulnerabilities</div>
              <div className="text-xl font-bold">{totalFindings} Found</div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Confidence</div>
              <div className="text-xl font-bold text-[#00ff41]">
                {Math.round(report.evaluation?.confidence * 100 || 0)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-1">Completed</div>
              <div className="text-xl font-bold">
                {new Date(report.createdAt).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>

        {/* Visual Proof */}
        {report.verifications && report.verifications.length > 0 && (
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">Visual Proof ⭐</h2>
            <p className="text-gray-400 mb-6">
              Before/after screenshots captured by AgentxploiTor showing the exploit verification
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Before */}
              <div className="border border-gray-700 rounded-lg overflow-hidden">
                <div className="bg-[#0a0e27] px-4 py-2 border-b border-gray-700">
                  <span className="text-sm font-semibold text-gray-400">BEFORE Exploit</span>
                </div>
                <div className="bg-gray-900 aspect-video flex items-center justify-center p-8">
                  <div className="text-center">
                    <div className="text-6xl mb-4">📸</div>
                    <div className="text-gray-400">Initial State</div>
                    <div className="text-sm text-gray-500 mt-2">
                      {report.verifications[0]?.beforeUrl || 'Captured'}
                    </div>
                  </div>
                </div>
              </div>

              {/* After */}
              <div className="border border-gray-700 rounded-lg overflow-hidden">
                <div className="bg-[#0a0e27] px-4 py-2 border-b border-gray-700">
                  <span className="text-sm font-semibold text-gray-400">AFTER Exploit</span>
                </div>
                <div className="bg-gray-900 aspect-video flex items-center justify-center p-8">
                  <div className="text-center">
                    <div className="text-6xl mb-4">📸</div>
                    <div className="text-gray-400">Exploited State</div>
                    <div className="text-sm text-red-500 mt-2">
                      Visual Diff: {report.verifications[0]?.visualDiff?.toFixed(1) || 0}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {report.verifications[0]?.success && (
              <div className="mt-6 p-4 bg-[#00ff41]/10 border border-[#00ff41] rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">✓</span>
                  <div>
                    <div className="font-semibold text-[#00ff41]">
                      Visual Diff: {report.verifications[0].visualDiff.toFixed(1)}% changed
                    </div>
                    <div className="text-sm text-gray-400">Agent autonomously verified exploit success</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Vulnerabilities */}
        <div className="space-y-6 mb-8">
          <h2 className="text-2xl font-bold">Vulnerabilities Found</h2>
          
          {report.vulnerabilities?.map((vuln: Vulnerability) => (
            <div key={vuln.id} className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className={`px-3 py-1 rounded-full border text-sm font-bold ${getSeverityColor(vuln.severity)}`}>
                    {vuln.severity}
                  </div>
                </div>
                
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-xl font-bold">{vuln.title}</h3>
                    <div className="text-gray-400 text-sm">CVSS {vuln.cvssScore}</div>
                  </div>
                  
                  <div className="text-sm text-gray-500 mb-3">{vuln.location}</div>
                  
                  <p className="text-gray-300 mb-4">{vuln.description}</p>
                  
                  <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4">
                    <div className="text-sm font-semibold text-[#00ff41] mb-2">Remediation:</div>
                    <p className="text-sm text-gray-400">{vuln.expectedOutcome}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!report.vulnerabilities || report.vulnerabilities.length === 0) && (
            <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">✅</div>
              <p className="text-[#00ff41]">No vulnerabilities found!</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Actions</h3>
          
          {/* Report Download */}
          <ReportDownload
            auditId={auditId}
            targetUrl={report.targetUrl}
            findings={report.vulnerabilities || []}
            summary={report.summary || {}}
            confidence={report.evaluation?.confidence || 0}
            createdAt={report.createdAt}
            reporterFid={report.meta?.requestedByFid}
          />

          {/* Request new audit */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <Button 
              onClick={() => router.push('/request')}
              className="w-full border border-gray-700"
            >
              🔄 Request New Audit
            </Button>
          </div>

          {/* Responsible Disclosure - Only for research mode with medium+ findings */}
          {report.meta?.mode === 'research' && totalFindings > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-lg font-semibold mb-3">🔐 Responsible Disclosure</h4>
              <p className="text-gray-400 text-sm mb-4">
                Generate a responsible disclosure template to safely report vulnerabilities to the project team.
              </p>
              <DisclosureTemplate auditId={auditId} />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
