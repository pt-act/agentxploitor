/**
 * state-analyzer.ts
 * On-chain state analysis for AgentxploiTor.
 * Detects proxy patterns, admin roles, and pause state.
 *
 * Uses QuickNode client for direct on-chain reads.
 */

import { getStorageSlot, getBytecode } from './quicknode-client';
import type { SupportedChain } from './quicknode-client';
import { Hex } from 'viem';

// ─── EIP-1967 Proxy Slots ────────────────────────────────────────────────────

// https://eips.ethereum.org/EIPS/eip-1967
const IMPLEMENTATION_SLOT: Hex =
  '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc';
const ADMIN_SLOT: Hex =
  '0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103';
const BEACON_SLOT: Hex =
  '0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ProxyInfo {
  isProxy: boolean;
  proxyType: 'eip1967' | 'transparent' | 'uups' | 'beacon' | 'none';
  implementation: string | null;
  admin: string | null;
}

export interface AdminInfo {
  hasOwner: boolean;
  ownerAddress: string | null;
  isAdminSlot: boolean;
  adminAddress: string | null;
}

export interface StateAnalysis {
  proxy: ProxyInfo;
  admin: AdminInfo;
  bytecodeLength: number;
  isContract: boolean;
  chain: string;
  analyzedAt: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function slotToAddress(slotValue: Hex): string | null {
  if (!slotValue || slotValue === '0x' + '0'.repeat(64)) return null;
  // Last 20 bytes of the 32-byte slot = address
  return '0x' + slotValue.slice(-40);
}

// ─── Proxy Detection ─────────────────────────────────────────────────────────

export async function detectProxy(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<ProxyInfo> {
  const result: ProxyInfo = {
    isProxy: false,
    proxyType: 'none',
    implementation: null,
    admin: null,
  };

  // Check EIP-1967 implementation slot
  const implSlot = await getStorageSlot(address, IMPLEMENTATION_SLOT, chain);
  if (implSlot) {
    const implAddress = slotToAddress(implSlot);
    if (implAddress && implAddress !== '0x' + '0'.repeat(40)) {
      result.isProxy = true;
      result.proxyType = 'eip1967';
      result.implementation = implAddress;

      // Check admin slot
      const adminSlot = await getStorageSlot(address, ADMIN_SLOT, chain);
      if (adminSlot) {
        const adminAddress = slotToAddress(adminSlot);
        if (adminAddress) {
          result.admin = adminAddress;
          result.proxyType = 'transparent'; // EIP-1967 with admin = transparent proxy
        }
      }

      return result;
    }
  }

  // Check beacon slot
  const beaconSlot = await getStorageSlot(address, BEACON_SLOT, chain);
  if (beaconSlot) {
    const beaconAddress = slotToAddress(beaconSlot);
    if (beaconAddress && beaconAddress !== '0x' + '0'.repeat(40)) {
      result.isProxy = true;
      result.proxyType = 'beacon';
      return result;
    }
  }

  return result;
}

// ─── Admin Detection ─────────────────────────────────────────────────────────

export async function detectAdmin(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<AdminInfo> {
  const result: AdminInfo = {
    hasOwner: false,
    ownerAddress: null,
    isAdminSlot: false,
    adminAddress: null,
  };

  // Check EIP-1967 admin slot
  const adminSlot = await getStorageSlot(address, ADMIN_SLOT, chain);
  if (adminSlot) {
    const adminAddress = slotToAddress(adminSlot);
    if (adminAddress && adminAddress !== '0x' + '0'.repeat(40)) {
      result.isAdminSlot = true;
      result.adminAddress = adminAddress;
    }
  }

  // Check Ownable.owner() — storage slot 0 for standard Ownable
  const ownerSlot = await getStorageSlot(
    address,
    '0x0000000000000000000000000000000000000000000000000000000000000000',
    chain
  );
  if (ownerSlot) {
    const ownerAddress = slotToAddress(ownerSlot);
    if (ownerAddress && ownerAddress !== '0x' + '0'.repeat(40)) {
      result.hasOwner = true;
      result.ownerAddress = ownerAddress;
    }
  }

  return result;
}

// ─── Full Analysis ────────────────────────────────────────────────────────────

export async function analyzeContractState(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<StateAnalysis> {
  const [proxy, admin, bytecode] = await Promise.all([
    detectProxy(address, chain),
    detectAdmin(address, chain),
    getBytecode(address, chain),
  ]);

  return {
    proxy,
    admin,
    bytecodeLength: bytecode ? (bytecode.length - 2) / 2 : 0, // hex chars to bytes
    isContract: bytecode !== null && bytecode !== '0x',
    chain,
    analyzedAt: new Date().toISOString(),
  };
}
