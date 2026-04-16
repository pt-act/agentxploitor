/**
 * quicknode-client.ts
 * Multi-chain EVM RPC wrapper for AgentxploiTor.
 * Uses viem (already in project) for type-safe chain interactions.
 *
 * Primary: QuickNode endpoints (reliable, rate-unlimited)
 * Fallback: Public RPCs (rate-limited, but functional)
 */

import { createPublicClient, http, Hex, PublicClient, Chain } from 'viem';
import { base, mainnet, bsc, polygon } from 'viem/chains';

// ─── Config ───────────────────────────────────────────────────────────────────

type SupportedChain = 'base' | 'ethereum' | 'bsc' | 'polygon';

interface ChainConfig {
  chain: Chain;
  quicknodeEnvVar: string;
  fallbackUrl: string;
}

const CHAIN_CONFIGS: Record<SupportedChain, ChainConfig> = {
  base: {
    chain: base,
    quicknodeEnvVar: 'QUICKNODE_BASE_URL',
    fallbackUrl: 'https://mainnet.base.org',
  },
  ethereum: {
    chain: mainnet,
    quicknodeEnvVar: 'QUICKNODE_ETH_URL',
    fallbackUrl: 'https://eth.llamarpc.com',
  },
  bsc: {
    chain: bsc,
    quicknodeEnvVar: 'QUICKNODE_BSC_URL',
    fallbackUrl: 'https://bsc-dataseed.binance.org',
  },
  polygon: {
    chain: polygon,
    quicknodeEnvVar: 'QUICKNODE_POLY_URL',
    fallbackUrl: 'https://polygon-rpc.com',
  },
};

// ─── Client Factory ──────────────────────────────────────────────────────────

const clientCache = new Map<SupportedChain, PublicClient>();

function getClient(chain: SupportedChain = 'base'): PublicClient {
  const cached = clientCache.get(chain);
  if (cached) return cached;

  const config = CHAIN_CONFIGS[chain];
  const quicknodeUrl = process.env[config.quicknodeEnvVar];
  const rpcUrl = quicknodeUrl && quicknodeUrl.length > 0 ? quicknodeUrl : config.fallbackUrl;

  const client = createPublicClient({
    chain: config.chain,
    transport: http(rpcUrl),
  });

  clientCache.set(chain, client);
  return client;
}

// ─── RPC Methods ─────────────────────────────────────────────────────────────

/**
 * Fetches deployed bytecode for a contract address.
 * eth_getCode — primary method for on-chain verification.
 */
export async function getBytecode(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<Hex | null> {
  try {
    const client = getClient(chain);
    const code = await client.getBytecode({ address });
    return code && code !== '0x' ? code : null;
  } catch {
    return null;
  }
}

/**
 * Reads a storage slot from a contract.
 * eth_getStorageAt — used for proxy detection, admin role reads, etc.
 */
export async function getStorageSlot(
  address: `0x${string}`,
  slot: Hex,
  chain: SupportedChain = 'base'
): Promise<Hex | null> {
  try {
    const client = getClient(chain);
    const value = await client.getStorageAt({ address, slot });
    return value ?? null;
  } catch {
    return null;
  }
}

/**
 * Fetches the ETH/token balance of an address.
 * eth_getBalance — used for wallet analysis.
 */
export async function getBalance(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<bigint | null> {
  try {
    const client = getClient(chain);
    const balance = await client.getBalance({ address });
    return balance;
  } catch {
    return null;
  }
}

/**
 * Gets the current block number.
 * eth_blockNumber — used for monitoring and block-range queries.
 */
export async function getBlockNumber(
  chain: SupportedChain = 'base'
): Promise<bigint | null> {
  try {
    const client = getClient(chain);
    const blockNumber = await client.getBlockNumber();
    return blockNumber;
  } catch {
    return null;
  }
}

/**
 * Calls a contract view function.
 * eth_call — used for reading contract state (owner, paused, etc.)
 */
export async function callContract(
  address: `0x${string}`,
  data: Hex,
  chain: SupportedChain = 'base'
): Promise<Hex | null> {
  try {
    const client = getClient(chain);
    const result = await client.call({
      account: address,
      to: address,
      data,
    });
    return result.data ?? null;
  } catch {
    return null;
  }
}

/**
 * Checks if an address is a contract (has code) or an EOA.
 */
export async function isContract(
  address: `0x${string}`,
  chain: SupportedChain = 'base'
): Promise<boolean> {
  const code = await getBytecode(address, chain);
  return code !== null && code !== '0x';
}

export type { SupportedChain };
