"use client";

import { useState, useCallback } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { AuditType, TargetType, PaymentToken, ResolvedTarget, Persona, AuditMode, AnalysisType } from '~/lib/types';
import {
  PRICES, AUDIT_TYPE_LABELS, displayPrice, defaultAuditType,
  DetectionBadge, AuditTypeCard, PaymentTokenSelector,
} from './audit-form/AuditFormParts';
import PersonaSelector from './audit-request/PersonaSelector';
import ModeSelector from './audit-request/ModeSelector';
import AnalysisTypeSelector from './audit-request/AnalysisTypeSelector';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AuditFormData {
  rawInput: string;
  resolvedTarget: ResolvedTarget;
  auditType: AuditType;
  paymentToken: PaymentToken;
  priceUsd: number;
  scope: string;
  // FarCaster Miniapp Auditor fields
  persona?: Persona;
  mode?: AuditMode;
  analysisType?: AnalysisType;
}

interface AuditRequestFormProps {
  onSubmit?: (data: AuditFormData) => void;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function AuditRequestForm({ onSubmit }: AuditRequestFormProps) {
  const [rawInput, setRawInput]               = useState('');
  const [detectedType, setDetectedType]       = useState<TargetType | 'unknown'>('unknown');
  const [resolvedTarget, setResolvedTarget]   = useState<ResolvedTarget | null>(null);
  const [resolveError, setResolveError]       = useState<string | null>(null);
  const [isResolving, setIsResolving]         = useState(false);
  const [debounceTimer, setDebounceTimer]     = useState<ReturnType<typeof setTimeout> | null>(null);

  const [auditType, setAuditType]             = useState<AuditType>('contract_deep');
  const [paymentToken, setPaymentToken]       = useState<PaymentToken>('eth');
  const [isSubmitting, setIsSubmitting]       = useState(false);

  // FarCaster Miniapp Auditor - Persona/Mode/Analysis
  const [persona, setPersona]                 = useState<Persona | undefined>();
  const [mode, setMode]                       = useState<AuditMode | undefined>();
  const [analysisType, setAnalysisType]       = useState<AnalysisType | undefined>();

  // ── Input detection & resolution ─────────────────────────────────────────

  const resolveInput = useCallback(async (value: string) => {
    setResolveError(null);
    setResolvedTarget(null);

    if (!value.trim()) {
      setDetectedType('unknown');
      return;
    }

    setIsResolving(true);
    try {
      const res = await fetch('/api/audit/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rawInput: value }),
      });
      const data = await res.json();

      if (data.resolved && data.target) {
        setResolvedTarget(data.target);
        setDetectedType(data.target.type as TargetType);
        setAuditType(defaultAuditType(data.target.type));
      } else if (data.reason === 'not_found') {
        setDetectedType('unknown');
        setResolveError(data.message ?? 'Could not resolve. Please provide a direct URL or address.');
      } else if (data.reason?.includes('coming soon')) {
        setDetectedType('unknown');
        setResolveError(data.reason);
      }
    } catch {
      setDetectedType('unknown');
    } finally {
      setIsResolving(false);
    }
  }, []);

  const onRawInputChange = (value: string) => {
    setRawInput(value);
    if (debounceTimer) clearTimeout(debounceTimer);
    const t = setTimeout(() => resolveInput(value), 600);
    setDebounceTimer(t);
  };

  // ── Submit ────────────────────────────────────────────────────────────────

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvedTarget || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmit?.({
        rawInput,
        resolvedTarget,
        auditType,
        paymentToken,
        priceUsd: PRICES[auditType] * (paymentToken === 'bnkr' ? 0.8 : 1),
        scope: auditType,
        // FarCaster Miniapp Auditor fields
        persona,
        mode,
        analysisType,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const canSubmit = !!resolvedTarget && !isResolving && !isSubmitting;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white py-16">
      <div className="container mx-auto px-4 max-w-2xl">

        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-3">Request Security Audit</h1>
          <p className="text-gray-400 max-w-md mx-auto">
            Independent AI-powered audit. Base-native. No affiliation with the audited project.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 space-y-8">

          {/* ── Step 1: Target Input ── */}
          <section>
            <Label htmlFor="rawInput" className="text-white mb-2 block text-base font-semibold">
              1. What would you like to audit? <span className="text-red-500">*</span>
            </Label>
            <Input
              id="rawInput"
              type="text"
              placeholder="Enter contract address, URL, GitHub repo, or miniapp name"
              value={rawInput}
              onChange={(e) => onRawInputChange(e.target.value)}
              className="bg-[#0a0e27] border-gray-700 text-white placeholder-gray-500"
              autoComplete="off"
              spellCheck={false}
            />

            {/* Detection status row */}
            <div className="mt-2 flex items-center gap-2 min-h-[24px]">
              {isResolving && <DetectionBadge type="resolving" />}
              {!isResolving && detectedType !== 'unknown' && <DetectionBadge type={detectedType} />}
              {!isResolving && resolvedTarget && resolvedTarget.value !== rawInput.trim() && (
                <span className="text-xs text-gray-400 truncate max-w-[300px]">
                  → {resolvedTarget.value}
                </span>
              )}
              {!isResolving && resolveError && (
                <span className="text-xs text-yellow-400">{resolveError}</span>
              )}
            </div>

            <p className="text-xs text-gray-500 mt-1">
              Accepts: EVM/Solana address · HTTPS URL · github.com/… · plain miniapp name
            </p>
          </section>

          {/* ── Step 2: Audit Type ── */}
          <section>
            <Label className="text-white mb-3 block text-base font-semibold">
              2. Select audit type <span className="text-red-500">*</span>
            </Label>
            <div className="space-y-3">
              {(Object.keys(AUDIT_TYPE_LABELS) as AuditType[]).map((type) => (
                <AuditTypeCard
                  key={type}
                  type={type}
                  selected={auditType === type}
                  token={paymentToken}
                  onClick={() => setAuditType(type)}
                />
              ))}
            </div>
          </section>

          {/* ── Step 3: Payment Token ── */}
          <section>
            <Label className="text-white mb-3 block text-base font-semibold">
              3. Pay with
            </Label>
            <PaymentTokenSelector selected={paymentToken} onChange={setPaymentToken} />
          </section>

          {/* ── Step 4: Persona Selection (FarCaster Miniapp Auditor) ── */}
          <section>
            <Label className="text-white mb-3 block text-base font-semibold">
              4. Select your role
            </Label>
            <PersonaSelector
              value={persona}
              onChange={setPersona}
              disabled={isSubmitting}
            />
          </section>

          {/* ── Step 5: Audit Mode (FarCaster Miniapp Auditor) ── */}
          {persona && (
            <section>
              <Label className="text-white mb-3 block text-base font-semibold">
                5. Select audit mode
              </Label>
              <ModeSelector
                value={mode}
                onChange={setMode}
                disabled={isSubmitting}
              />
            </section>
          )}

          {/* ── Step 6: Analysis Type (FarCaster Miniapp Auditor) ── */}
          {mode && (
            <section>
              <Label className="text-white mb-3 block text-base font-semibold">
                6. Analysis type
              </Label>
              <AnalysisTypeSelector
                value={analysisType}
                onChange={setAnalysisType}
                disabled={isSubmitting}
              />
            </section>
          )}

          {/* ── Summary ── */}
          <div className="bg-[#0a0e27] border border-gray-700 rounded-lg p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Audit type</span>
              <span className="text-white font-semibold text-sm">
                {AUDIT_TYPE_LABELS[auditType].title}
              </span>
            </div>
            {persona && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Role</span>
                <span className="text-white text-sm capitalize">{persona}</span>
              </div>
            )}
            {mode && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Mode</span>
                <span className="text-white text-sm capitalize">{mode.replace('_', ' ')}</span>
              </div>
            )}
            {analysisType && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Analysis</span>
                <span className="text-white text-sm capitalize">{analysisType}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Chain</span>
              <span className="text-white text-sm">Base (EVM)</span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-gray-700">
              <span className="text-gray-400 text-sm">Total</span>
              <div className="text-right">
                <span className="text-[#00ff41] font-bold text-xl">
                  {displayPrice(auditType, paymentToken)}
                </span>
                {paymentToken === 'bnkr' && (
                  <span className="text-gray-500 text-xs line-through ml-2">
                    ${PRICES[auditType]}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* ── Submit ── */}
          <div>
            <Button
              type="submit"
              disabled={!canSubmit}
              className="w-full bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] text-lg py-6 font-bold disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block animate-spin">⏳</span> Processing...
                </span>
              ) : !resolvedTarget ? (
                'Enter a target to continue'
              ) : (
                `Pay ${displayPrice(auditType, paymentToken)} & Start Audit`
              )}
            </Button>

            {!resolvedTarget && rawInput.length > 0 && !isResolving && (
              <p className="text-center text-xs text-yellow-400 mt-2">
                ⚠ Target could not be resolved — please try a direct URL or address
              </p>
            )}
          </div>

          {/* ── Independence notice ── */}
          <div className="text-center text-xs text-gray-500 pt-2 border-t border-gray-800 space-y-1">
            <p>✓ Independent audit — no affiliation with the audited project</p>
            <p>✓ Visual proof screenshots · On-chain independence declaration</p>
            <p>✓ No refunds — peace of mind is the product regardless of outcome</p>
          </div>

        </form>
      </div>
    </div>
  );
}
