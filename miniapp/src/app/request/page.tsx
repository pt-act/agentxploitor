"use client";

import AuditRequestForm, { AuditFormData } from '~/components/AuditRequestForm';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useAccount, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther, parseUnits } from 'viem';

// ─── Constants ────────────────────────────────────────────────────────────────

// Base chain contract addresses — set via env
const AGENT_WALLET  = process.env.NEXT_PUBLIC_AGENT_WALLET_ADDRESS as `0x${string}` | undefined;
const USDC_ADDRESS  = process.env.NEXT_PUBLIC_USDC_ADDRESS  as `0x${string}` | undefined;
const BNKR_ADDRESS  = process.env.NEXT_PUBLIC_BNKR_ADDRESS  as `0x${string}` | undefined;

const ERC20_TRANSFER_ABI = [
  {
    name: 'transfer',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'to',     type: 'address' },
      { name: 'amount', type: 'uint256' },
    ],
    outputs: [{ type: 'bool' }],
  },
] as const;

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function RequestAuditPage() {
  const router = useRouter();
  const { address, isConnected } = useAccount();
  const { writeContractAsync } = useWriteContract();
  const [pendingHash, setPendingHash] = useState<`0x${string}` | undefined>();

  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({ hash: pendingHash });

  const handleSubmit = async (formData: AuditFormData) => {
    if (!isConnected || !address) {
      alert('Please connect your wallet first');
      return;
    }

    if (!AGENT_WALLET) {
      console.error('NEXT_PUBLIC_AGENT_WALLET_ADDRESS not set');
      alert('Payment destination not configured. Please contact support.');
      return;
    }

    try {
      let txHash: `0x${string}` | undefined;

      // ── ETH payment ──────────────────────────────────────────────────────
      // Note: In production, you'd convert USD to ETH using an oracle price feed
      // For now, we approximate: $1 = 0.0004 ETH (~$2500/ETH)
      if (formData.paymentToken === 'eth') {
        const ethAmount = (formData.priceUsd / 2500).toFixed(6);
        txHash = await writeContractAsync({
          address: AGENT_WALLET,
          abi: [],
          functionName: '',
          value: parseEther(ethAmount),
        } as any);
      }

      // ── USDC payment ─────────────────────────────────────────────────────
      if (formData.paymentToken === 'usdc') {
        if (!USDC_ADDRESS) throw new Error('USDC contract address not configured');
        txHash = await writeContractAsync({
          address: USDC_ADDRESS,
          abi: ERC20_TRANSFER_ABI,
          functionName: 'transfer',
          args: [AGENT_WALLET, parseUnits(formData.priceUsd.toString(), 6)], // USDC = 6 decimals
        });
      }

      // ── BNKR payment ─────────────────────────────────────────────────────
      if (formData.paymentToken === 'bnkr') {
        if (!BNKR_ADDRESS) throw new Error('BNKR contract address not configured');
        txHash = await writeContractAsync({
          address: BNKR_ADDRESS,
          abi: ERC20_TRANSFER_ABI,
          functionName: 'transfer',
          args: [AGENT_WALLET, parseUnits(formData.priceUsd.toString(), 18)], // BNKR = 18 decimals
        });
      }

      if (txHash) setPendingHash(txHash);

      // ── Create audit job ──────────────────────────────────────────────────
      const response = await fetch('/api/audit/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Target
          rawInput:        formData.rawInput,
          resolvedTarget:  formData.resolvedTarget,
          targetUrl:       formData.resolvedTarget.value,
          contractAddress: formData.resolvedTarget.type.startsWith('contract')
                             ? formData.resolvedTarget.value
                             : undefined,
          blockchain:      formData.resolvedTarget.chain ?? 'base',
          targetType:      formData.resolvedTarget.type,
          // Audit
          auditType:       formData.auditType,
          scope:           formData.scope,
          priority:        'high',
          // Payment
          paymentToken:    formData.paymentToken,
          paymentTxHash:   txHash ?? 'pending',
          paymentAmount:   formData.priceUsd,
          walletAddress:   address,
          // FarCaster Miniapp Auditor fields
          persona:         formData.persona,
          mode:            formData.mode,
          analysisType:    formData.analysisType,
        }),
      });

      const data = await response.json();

      if (data.auditId) {
        router.push(`/audit/${data.auditId}`);
      } else {
        throw new Error(data.error ?? 'Failed to create audit job');
      }

    } catch (error: any) {
      console.error('Audit request error:', error);
      alert(`Error: ${error?.message ?? 'Something went wrong. Please try again.'}`);
    }
  };

  return (
    <div>
      {!isConnected && (
        <div className="fixed top-4 right-4 z-50 bg-yellow-500/20 border border-yellow-500 text-yellow-500 px-4 py-2 rounded-lg text-sm">
          ⚠️ Connect your wallet to pay & submit
        </div>
      )}

      <AuditRequestForm onSubmit={handleSubmit} />

      {isConfirming && (
        <div className="fixed bottom-4 right-4 z-50 bg-blue-500/20 border border-blue-500 text-blue-500 px-4 py-2 rounded-lg text-sm">
          ⏳ Waiting for transaction confirmation...
        </div>
      )}

      {isConfirmed && (
        <div className="fixed bottom-4 right-4 z-50 bg-green-500/20 border border-green-500 text-green-500 px-4 py-2 rounded-lg text-sm">
          ✅ Payment confirmed! Redirecting...
        </div>
      )}
    </div>
  );
}
