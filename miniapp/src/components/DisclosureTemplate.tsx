"use client";

import { useState, useEffect } from 'react';
import { Button } from './ui/Button';

interface DisclosureFinding {
  id: string;
  title: string;
  severity: string;
  location?: string;
  description?: string;
  recommendedFix?: string;
  cvssScore?: number;
}

interface DisclosureData {
  auditId: string;
  targetUrl: string;
  targetType?: string;
  blockchain?: string;
  reporterFid?: number;
  auditMode?: string;
  analysisType?: string;
  createdAt?: string;
  disclosureGeneratedAt?: string;
  findingsCount: {
    critical: number;
    high: number;
    medium: number;
  };
  findings: DisclosureFinding[];
  socialSummary: string;
  castComposerUrl: string;
  developerContact: {
    note: string;
    suggestion: string;
  };
  fullTemplate: string;
  hasFindings?: boolean;
  message?: string;
}

interface DisclosureTemplateProps {
  auditId: string;
}

export default function DisclosureTemplate({ auditId }: DisclosureTemplateProps) {
  const [disclosure, setDisclosure] = useState<DisclosureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchDisclosure();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auditId]);

  const fetchDisclosure = async () => {
    try {
      const res = await fetch(`/api/disclosure/${auditId}`);
      const data = await res.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setDisclosure(data.disclosure);
      }
    } catch {
      setError('Failed to load disclosure');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!disclosure?.fullTemplate) return;
    
    try {
      await navigator.clipboard.writeText(disclosure.fullTemplate);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = disclosure.fullTemplate;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 text-center">
        <div className="animate-pulse text-gray-400">Loading disclosure...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#1a1f3a] border border-red-900/50 rounded-lg p-8 text-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!disclosure?.findings?.length || disclosure.hasFindings === false) {
    return (
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-400">
          {disclosure?.message || 'No actionable vulnerabilities found for disclosure.'}
        </p>
        <p className="text-gray-500 text-sm mt-2">
          Disclosure is only available for research mode audits with medium+ severity findings.
        </p>
      </div>
    );
  }

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">Responsible Disclosure</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Audit ID</span>
            <p className="text-white font-mono text-xs">{disclosure.auditId}</p>
          </div>
          <div>
            <span className="text-gray-400">Target</span>
            <p className="text-white text-xs truncate">{disclosure.targetUrl}</p>
          </div>
          <div>
            <span className="text-gray-400">Reporter FID</span>
            <p className="text-white">{disclosure.reporterFid || 'Anonymous'}</p>
          </div>
          <div>
            <span className="text-gray-400">Generated</span>
            <p className="text-white text-xs">
              {new Date(disclosure.disclosureGeneratedAt || '').toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Findings count */}
        <div className="flex gap-4 mt-4 pt-4 border-t border-gray-700">
          {disclosure.findingsCount.critical > 0 && (
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${severityColor('CRITICAL')}`}>
              {disclosure.findingsCount.critical} CRITICAL
            </span>
          )}
          {disclosure.findingsCount.high > 0 && (
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${severityColor('HIGH')}`}>
              {disclosure.findingsCount.high} HIGH
            </span>
          )}
          {disclosure.findingsCount.medium > 0 && (
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${severityColor('MEDIUM')}`}>
              {disclosure.findingsCount.medium} MEDIUM
            </span>
          )}
        </div>
      </div>

      {/* Findings list */}
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Findings</h3>
        
        <div className="space-y-4">
          {disclosure.findings.map((finding) => (
            <div 
              key={finding.id} 
              className={`border rounded-lg p-4 ${severityColor(finding.severity)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-semibold">{finding.title}</h4>
                <span className="text-xs font-medium px-2 py-1 rounded">
                  {finding.severity}
                  {finding.cvssScore && ` (${finding.cvssScore.toFixed(1)})`}
                </span>
              </div>
              
              {finding.location && (
                <p className="text-xs opacity-70 mb-2 font-mono">
                  📍 {finding.location}
                </p>
              )}
              
              {finding.description && (
                <p className="text-sm opacity-80 mb-2">
                  {finding.description.slice(0, 200)}
                  {finding.description.length > 200 ? '...' : ''}
                </p>
              )}
              
              {finding.recommendedFix && (
                <div className="mt-2 pt-2 border-t border-current/20">
                  <p className="text-xs font-medium">💡 Recommended Fix:</p>
                  <p className="text-sm opacity-80">{finding.recommendedFix}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Copy to clipboard */}
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Full Template</h3>
          <p className="text-gray-400 text-sm mb-4">
            Copy the complete disclosure template to share with the project team.
          </p>
          <Button
            onClick={copyToClipboard}
            className="w-full bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35]"
          >
            {copied ? '✓ Copied!' : 'Copy to Clipboard'}
          </Button>
        </div>

        {/* Share to Warpcast */}
        <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🐦 Share on Warpcast</h3>
          <p className="text-gray-400 text-sm mb-4">
            Share a non-sensitive summary on Warpcast.
          </p>
          <a
            href={disclosure.castComposerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full text-center"
          >
            <Button className="w-full bg-[#6366f1] hover:bg-[#4f46e5] text-white">
              Open Warpcast Composer
            </Button>
          </a>
        </div>
      </div>

      {/* Developer contact */}
      <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-2">👤 Contact Developer</h3>
        <p className="text-gray-400 text-sm">{disclosure.developerContact.note}</p>
        <p className="text-gray-500 text-xs mt-2">
          💡 {disclosure.developerContact.suggestion}
        </p>
      </div>

      {/* Disclaimer */}
      <div className="text-center text-xs text-gray-500 pt-4 border-t border-gray-800">
        <p>Generated by AgentxploiTor • Independent security audit</p>
        <p>No affiliation with the audited project</p>
      </div>
    </div>
  );
}
