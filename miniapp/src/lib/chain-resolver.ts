/**
 * chain-resolver.ts
 * Resolves audit targets to their source code / bytecode for analysis.
 *
 * Tier 1: EVM contract → QuickNode eth_getCode (bytecode) + Basescan verified source
 * Tier 2: Unverified EVM → QuickNode bytecode only (Mythril handles it)
 * Tier 3: GitHub repo → .sol / .rs file list
 * Tier 4: Solana program → program account data
 */

import { TargetType, ResolvedTarget } from './types';
import { getBytecode, type SupportedChain } from './blockchain/quicknode-client';
import { analyzeContractState } from './blockchain/state-analyzer';

// ─── Config ───────────────────────────────────────────────────────────────────

const BASESCAN_API = 'https://api.basescan.org/api';
const ETHERSCAN_API = 'https://api.etherscan.io/api';
const API_KEY = process.env.BASESCAN_API_KEY || process.env.ETHERSCAN_API_KEY || '';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';

// ─── Types ────────────────────────────────────────────────────────────────────

export type SourceType = 'verified_solidity' | 'bytecode_only' | 'github_repo' | 'solana_program';

export interface ResolvedSource {
  targetType: TargetType;
  sourceType: SourceType;
  contractAddress?: string;
  // Verified Solidity
  sourceFiles?: Record<string, string>;   // filename → source code
  contractName?: string;
  compilerVersion?: string;
  abi?: Record<string, unknown>[];
  // Bytecode
  bytecode?: string;
  // On-chain state (from QuickNode)
  onChainState?: {
    bytecodeLength: number;
    isProxy: boolean;
    proxyType: string;
    implementation: string | null;
    admin: string | null;
  };
  // GitHub
  repoUrl?: string;
  solFiles?: string[];                    // URLs to .sol / .rs files
  defaultBranch?: string;
  // Solana
  programId?: string;
  programData?: string;
  // Metadata
  chain: string;
  verified: boolean;
  resolvedAt: string;
}

// ─── EVM Contract Resolution ──────────────────────────────────────────────────

async function fetchVerifiedSource(
  address: string,
  chain: string
): Promise<{ sourceFiles: Record<string, string>; contractName: string; compilerVersion: string; abi: Record<string, unknown>[] } | null> {
  const baseUrl = chain === 'base' ? BASESCAN_API : ETHERSCAN_API;

  try {
    const url = `${baseUrl}?module=contract&action=getsourcecode&address=${address}&apikey=${API_KEY}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return null;

    const data = await res.json();
    if (data.status !== '1' || !data.result?.[0]) return null;

    const result = data.result[0];
    if (!result.SourceCode || result.SourceCode === '') return null;

    // Parse source — can be single file or JSON blob (Hardhat/Foundry style)
    const sourceFiles: Record<string, string> = {};
    const raw = result.SourceCode as string;

    if (raw.startsWith('{{')) {
      // Hardhat/Foundry multi-file: `{{...}}` double-braced JSON
      try {
        const parsed = JSON.parse(raw.slice(1, -1));
        const sources = parsed.sources ?? parsed;
        for (const [filename, obj] of Object.entries(sources)) {
          sourceFiles[filename] = (obj as Record<string, unknown>).content as string ?? '';
        }
      } catch {
        sourceFiles['contract.sol'] = raw;
      }
    } else if (raw.startsWith('{')) {
      // Standard JSON sources
      try {
        const parsed = JSON.parse(raw);
        for (const [filename, obj] of Object.entries(parsed)) {
          sourceFiles[filename] = (obj as Record<string, unknown>).content as string ?? String(obj);
        }
      } catch {
        sourceFiles['contract.sol'] = raw;
      }
    } else {
      sourceFiles['contract.sol'] = raw;
    }

    return {
      sourceFiles,
      contractName: result.ContractName || 'Unknown',
      compilerVersion: result.CompilerVersion || 'unknown',
      abi: result.ABI && result.ABI !== 'Contract source code not verified'
        ? JSON.parse(result.ABI)
        : [],
    };
  } catch {
    return null;
  }
}

// fetchBytecode was replaced by QuickNode getBytecode() — removed

export async function resolveEvmContract(
  address: string,
  chain: string = 'base'
): Promise<ResolvedSource> {
  const base: Partial<ResolvedSource> = {
    targetType: 'contract_evm',
    contractAddress: address,
    chain,
    resolvedAt: new Date().toISOString(),
  };

  // QuickNode: fetch bytecode + on-chain state (primary — rate-unlimited)
  const [bytecode, stateAnalysis] = await Promise.all([
    getBytecode(address as `0x${string}`, chain as SupportedChain),
    analyzeContractState(address as `0x${string}`, chain as SupportedChain),
  ]);

  const onChainState = {
    bytecodeLength: stateAnalysis.bytecodeLength,
    isProxy: stateAnalysis.proxy.isProxy,
    proxyType: stateAnalysis.proxy.proxyType,
    implementation: stateAnalysis.proxy.implementation,
    admin: stateAnalysis.admin.adminAddress ?? stateAnalysis.admin.ownerAddress,
  };

  // Basescan: try verified source (secondary — rate-limited)
  const verified = await fetchVerifiedSource(address, chain);
  if (verified) {
    return {
      ...base,
      sourceType: 'verified_solidity',
      sourceFiles: verified.sourceFiles,
      contractName: verified.contractName,
      compilerVersion: verified.compilerVersion,
      abi: verified.abi,
      bytecode: bytecode ?? undefined,
      onChainState,
      verified: true,
    } as ResolvedSource;
  }

  // Bytecode only (from QuickNode — preferred over Basescan for bytecode)
  return {
    ...base,
    sourceType: 'bytecode_only',
    bytecode: bytecode ?? '0x',
    onChainState,
    verified: false,
  } as ResolvedSource;
}

// ─── GitHub Repo Resolution ───────────────────────────────────────────────────

export async function resolveGitHubRepo(repoUrl: string): Promise<ResolvedSource> {
  // Extract owner/repo from URL
  const match = repoUrl.match(/github\.com\/([^/]+)\/([^/]+)/);
  if (!match) {
    return {
      targetType: 'github_repo',
      sourceType: 'github_repo',
      repoUrl,
      solFiles: [],
      chain: 'base',
      verified: false,
      resolvedAt: new Date().toISOString(),
    };
  }

  const [, owner, repo] = match;
  const headers: Record<string, string> = { 'Accept': 'application/vnd.github+json' };
  if (GITHUB_TOKEN) headers['Authorization'] = `Bearer ${GITHUB_TOKEN}`;

  try {
    // Get default branch
    const repoRes = await fetch(`https://api.github.com/repos/${owner}/${repo}`, {
      headers,
      signal: AbortSignal.timeout(8_000),
    });
    const repoData = repoRes.ok ? await repoRes.json() : {};
    const defaultBranch = repoData.default_branch ?? 'main';

    // Search for .sol and .rs files via git trees
    const treeRes = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/git/trees/${defaultBranch}?recursive=1`,
      { headers, signal: AbortSignal.timeout(10_000) }
    );

    let solFiles: string[] = [];
    if (treeRes.ok) {
      const treeData = await treeRes.json();
      solFiles = (treeData.tree ?? [])
        .filter((f: Record<string, unknown>) => f.type === 'blob' && (String(f.path ?? '').endsWith('.sol') || String(f.path ?? '').endsWith('.rs')))
        .map((f: Record<string, unknown>) => `https://raw.githubusercontent.com/${owner}/${repo}/${defaultBranch}/${String(f.path)}`)
        .slice(0, 50); // Cap at 50 files
    }

    return {
      targetType: 'github_repo',
      sourceType: 'github_repo',
      repoUrl,
      solFiles,
      defaultBranch,
      chain: 'base',
      verified: false,
      resolvedAt: new Date().toISOString(),
    };
  } catch {
    return {
      targetType: 'github_repo',
      sourceType: 'github_repo',
      repoUrl,
      solFiles: [],
      chain: 'base',
      verified: false,
      resolvedAt: new Date().toISOString(),
    };
  }
}

// ─── Solana Program Resolution ────────────────────────────────────────────────

import { getSolanaProgram as fetchSolanaProgram } from './blockchain/solana-client';

export async function resolveSolanaProgram(programId: string): Promise<ResolvedSource> {
  // Fetch on-chain program data via QuickNode
  const programInfo = await fetchSolanaProgram(programId);

  return {
    targetType: 'contract_solana',
    sourceType: 'solana_program',
    programId,
    chain: 'solana',
    verified: false,
    onChainState: programInfo ? {
      bytecodeLength: programInfo.dataSize,
      isProxy: false,
      proxyType: 'none',
      implementation: null,
      admin: programInfo.upgradeAuthority,
    } : undefined,
    resolvedAt: new Date().toISOString(),
  };
}

// ─── Unified Resolver ─────────────────────────────────────────────────────────

export async function resolveSource(target: ResolvedTarget): Promise<ResolvedSource> {
  switch (target.type) {
    case 'contract_evm':
      return resolveEvmContract(target.value, target.chain ?? 'base');
    case 'github_repo':
      return resolveGitHubRepo(target.value);
    case 'contract_solana':
      return resolveSolanaProgram(target.value);
    case 'miniapp_url':
      // Miniapp URL resolution handled by Group 4 (agent-browser)
      return {
        targetType: 'miniapp_url',
        sourceType: 'github_repo', // placeholder — actual analysis in Group 4
        repoUrl: target.value,
        chain: 'base',
        verified: false,
        resolvedAt: new Date().toISOString(),
      };
    default:
      throw new Error(`Unsupported target type: ${target.type}`);
  }
}
