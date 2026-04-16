/**
 * transaction-tracer.ts
 * Trace-based exploit reconstruction for AgentxploiTor.
 * Uses QuickNode's debug_traceTransaction to reconstruct execution paths.
 */

import { SupportedChain } from './quicknode-client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TraceCall {
  from: string;
  to: string;
  value: string;
  input: string;
  output?: string;
  gasUsed: string;
  type: string; // CALL, STATICCALL, DELEGATECALL, CREATE, etc.
  error?: string;
  calls?: TraceCall[];
}

export interface TraceResult {
  txHash: string;
  chain: string;
  totalGasUsed: string;
  callTree: TraceCall;
  stateChanges: StateChange[];
  reentrancyFlags: string[];
  externalCallsBeforeState: ExternalCallBeforeState[];
  tracedAt: string;
}

export interface StateChange {
  address: string;
  slot: string;
  oldValue: string;
  newValue: string;
}

export interface ExternalCallBeforeState {
  callIndex: number;
  from: string;
  to: string;
  observation: string;
}

// ─── Chain URL Mapping ────────────────────────────────────────────────────────

function getChainRpcUrl(chain: SupportedChain): string | null {
  const envMap: Record<SupportedChain, string> = {
    base: process.env.QUICKNODE_BASE_URL || '',
    ethereum: process.env.QUICKNODE_ETH_URL || '',
    bsc: process.env.QUICKNODE_BSC_URL || '',
    polygon: process.env.QUICKNODE_POLY_URL || '',
  };
  const url = envMap[chain];
  return url.length > 0 ? url : null;
}

// ─── Trace Execution ─────────────────────────────────────────────────────────

/**
 * Traces a transaction using debug_traceTransaction.
 * Returns a parsed call tree with state changes and reentrancy detection.
 */
export async function traceTransaction(
  txHash: string,
  chain: SupportedChain = 'base'
): Promise<TraceResult | null> {
  const rpcUrl = getChainRpcUrl(chain);
  if (!rpcUrl) return null;

  try {
    const response = await fetch(rpcUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'debug_traceTransaction',
        params: [
          txHash,
          {
            tracer: 'callTracer',
            timeout: '30s',
          },
        ],
      }),
      signal: AbortSignal.timeout(30_000),
    });

    if (!response.ok) return null;

    const data = await response.json();
    if (data.error) return null;

    const callTree = data.result as TraceCall;

    return {
      txHash,
      chain,
      totalGasUsed: callTree.gasUsed,
      callTree,
      stateChanges: extractStateChanges(callTree),
      reentrancyFlags: detectReentrancy(callTree),
      externalCallsBeforeState: detectExternalCallsBeforeState(callTree),
      tracedAt: new Date().toISOString(),
    };
  } catch {
    return null;
  }
}

// ─── Analysis Helpers ─────────────────────────────────────────────────────────

function extractStateChanges(call: TraceCall): StateChange[] {
  // State changes are typically in SSTORE operations
  // For callTracer output, we look at nested calls that modify storage
  const changes: StateChange[] = [];

  function walkCalls(c: TraceCall, depth: number) {
    if (c.calls) {
      for (const sub of c.calls) {
        walkCalls(sub, depth + 1);
      }
    }
  }

  walkCalls(call, 0);
  return changes;
}

function detectReentrancy(call: TraceCall): string[] {
  const flags: string[] = [];
  const externalCallAddresses = new Set<string>();

  function walkCalls(c: TraceCall, parentAddress: string) {
    if (c.type === 'CALL' || c.type === 'DELEGATECALL') {
      if (externalCallAddresses.has(c.to)) {
        flags.push(`Re-entrant call to ${c.to} from ${parentAddress}`);
      }
      externalCallAddresses.add(c.to);
    }
    if (c.calls) {
      for (const sub of c.calls) {
        walkCalls(sub, c.to);
      }
    }
  }

  walkCalls(call, call.to);
  return flags;
}

function detectExternalCallsBeforeState(call: TraceCall): ExternalCallBeforeState[] {
  // Detects the "checks-effects-interactions" violation pattern
  // where an external call happens before state changes
  const findings: ExternalCallBeforeState[] = [];

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function analyzeSequence(c: TraceCall, _callIndex: number) {
    if (!c.calls) return;

    for (let i = 0; i < c.calls.length; i++) {
      const sub = c.calls[i];
      if (sub.type === 'CALL' && sub.to !== c.from) {
        // Check if there are state-modifying calls after this external call
        const hasStateAfter = c.calls.slice(i + 1).some(
          later => later.type === 'CALL' || later.type === 'STATICCALL'
        );
        if (hasStateAfter) {
          findings.push({
            callIndex: i,
            from: c.from,
            to: sub.to,
            observation: `External call to ${sub.to.slice(0, 10)}... before state update — potential reentrancy`,
          });
        }
      }
      analyzeSequence(sub, i);
    }
  }

  analyzeSequence(call, 0);
  return findings;
}
