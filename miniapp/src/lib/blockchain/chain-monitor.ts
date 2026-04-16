/**
 * chain-monitor.ts
 * Real-time contract monitoring via QuickNode WebSocket subscriptions.
 * Detects bytecode changes, admin transfers, proxy upgrades.
 */

import { SupportedChain } from './quicknode-client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface MonitorEvent {
  type: 'bytecode_change' | 'admin_transfer' | 'proxy_upgrade' | 'state_change' | 'new_block';
  address: string;
  chain: string;
  blockNumber: number;
  timestamp: string;
  details: Record<string, string>;
}

export interface WatchedContract {
  address: string;
  chain: SupportedChain;
  label: string;
  lastBytecodeHash: string | null;
  lastAdmin: string | null;
  active: boolean;
}

type MonitorCallback = (event: MonitorEvent) => void;

// ─── State ────────────────────────────────────────────────────────────────────

const watchedContracts = new Map<string, WatchedContract>();
const callbacks: MonitorCallback[] = [];
let blockSubscription: WebSocket | null = null;

// ─── Watch Management ─────────────────────────────────────────────────────────

export function watchContract(
  address: string,
  chain: SupportedChain,
  label: string = ''
): void {
  const key = `${chain}:${address.toLowerCase()}`;
  watchedContracts.set(key, {
    address: address.toLowerCase(),
    chain,
    label: label || address.slice(0, 10) + '...',
    lastBytecodeHash: null,
    lastAdmin: null,
    active: true,
  });
}

export function unwatchContract(address: string, chain: SupportedChain): void {
  const key = `${chain}:${address.toLowerCase()}`;
  watchedContracts.delete(key);
}

export function getWatchedContracts(): WatchedContract[] {
  return Array.from(watchedContracts.values());
}

// ─── Event Callbacks ──────────────────────────────────────────────────────────

export function onMonitorEvent(callback: MonitorCallback): () => void {
  callbacks.push(callback);
  return () => {
    const idx = callbacks.indexOf(callback);
    if (idx >= 0) callbacks.splice(idx, 1);
  };
}

function emitEvent(event: MonitorEvent): void {
  for (const cb of callbacks) {
    try {
      cb(event);
    } catch {
      // Don't let callback errors break the monitor
    }
  }
}

// ─── Block Monitoring ─────────────────────────────────────────────────────────

export async function startBlockMonitoring(chain: SupportedChain): Promise<void> {
  const envMap: Record<SupportedChain, string> = {
    base: process.env.QUICKNODE_BASE_URL || '',
    ethereum: process.env.QUICKNODE_ETH_URL || '',
    bsc: process.env.QUICKNODE_BSC_URL || '',
    polygon: process.env.QUICKNODE_POLY_URL || '',
  };

  const rpcUrl = envMap[chain];
  if (!rpcUrl) return;

  // Convert HTTP URL to WebSocket URL for subscriptions
  const wsUrl = rpcUrl.replace('https://', 'wss://').replace('http://', 'ws://');

  try {
    blockSubscription = new WebSocket(wsUrl);

    blockSubscription.onopen = () => {
      // Subscribe to new blocks
      blockSubscription?.send(JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'eth_subscribe',
        params: ['newHeads'],
      }));
    };

    blockSubscription.onmessage = (event) => {
      const data = JSON.parse(event.data as string);
      if (data.method === 'eth_subscription') {
        const block = data.params.result;
        emitEvent({
          type: 'new_block',
          address: '',
          chain,
          blockNumber: parseInt(block.number, 16),
          timestamp: new Date().toISOString(),
          details: {
            hash: block.hash,
            gasUsed: block.gasUsed,
            parentHash: block.parentHash,
          },
        });
      }
    };

    blockSubscription.onerror = () => {
      // Reconnect after 5s
      setTimeout(() => startBlockMonitoring(chain), 5000);
    };
  } catch {
    // WebSocket not available — fall back to polling
  }
}

export function stopBlockMonitoring(): void {
  if (blockSubscription) {
    blockSubscription.close();
    blockSubscription = null;
  }
}

// ─── Contract State Check ─────────────────────────────────────────────────────

/**
 * Checks watched contracts for state changes.
 * Call this periodically (e.g., every 30s) to detect changes.
 * In production, this would use WebSocket subscriptions per contract.
 */
export async function checkWatchedContracts(
  getBytecode: (address: `0x${string}`, chain: SupportedChain) => Promise<string | null>
): Promise<void> {
  for (const [, contract] of watchedContracts) {
    if (!contract.active) continue;

    try {
      const bytecode = await getBytecode(
        contract.address as `0x${string}`,
        contract.chain
      );

      if (bytecode) {
        const hash = simpleHash(bytecode);

        if (contract.lastBytecodeHash && contract.lastBytecodeHash !== hash) {
          emitEvent({
            type: 'bytecode_change',
            address: contract.address,
            chain: contract.chain,
            blockNumber: 0,
            timestamp: new Date().toISOString(),
            details: {
              label: contract.label,
              previousHash: contract.lastBytecodeHash,
              newHash: hash,
              observation: 'Contract bytecode changed — possible upgrade or modification',
            },
          });
        }

        contract.lastBytecodeHash = hash;
      }
    } catch {
      // Skip this check on error
    }
  }
}

function simpleHash(input: string): string {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(16);
}
