/**
 * chain-resolver.ts
 * Resolves audit targets to their source code / bytecode for analysis.
 *
 * Tier 1: EVM contract → Basescan/Etherscan verified source
 * Tier 2: Unverified EVM → bytecode only (Mythril handles it)
 * Tier 3: GitHub repo → .sol / .rs file list
 * Tier 4: Solana program → program account data
 */

import { TargetType, ResolvedTarget } from './types';

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
  abi?: any[];
  // Bytecode
  bytecode?: string;
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
): Promise<{ sourceFiles: Record<string, string>; contractName: string; compilerVersion: string; abi: any[] } | null> {
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
    let sourceFiles: Record<string, string> = {};
    const raw = result.SourceCode as string;

    if (raw.startsWith('{{')) {
      // Hardhat/Foundry multi-file: `{{...}}` double-braced JSON
      try {
        const parsed = JSON.parse(raw.slice(1, -1));
        const sources = parsed.sources ?? parsed;
        for (const [filename, obj] of Object.entries(sources)) {
          sourceFiles[filename] = (obj as any).content ?? '';
        }
      } catch {
        sourceFiles['contract.sol'] = raw;
      }
    } else if (raw.startsWith('{')) {
      // Standard JSON sources
      try {
        const parsed = JSON.parse(raw);
        for (const [filename, obj] of Object.entries(parsed)) {
          sourceFiles[filename] = (obj as any).content ?? String(obj);
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

async function fetchBytecode(address: string, chain: string): Promise<string | null> {
  const baseUrl = chain === 'base' ? BASESCAN_API : ETHERSCAN_API;
  try {
    const url = `${baseUrl}?module=proxy&action=eth_getCode&address=${address}&tag=latest&apikey=${API_KEY}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) return null;
    const data = await res.json();
    const code = data.result as string;
    return code && code !== '0x' ? code : null;
  } catch {
    return null;
  }
}

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

  // Try verified source first
  const verified = await fetchVerifiedSource(address, chain);
  if (verified) {
    return {
      ...base,
      sourceType: 'verified_solidity',
      sourceFiles: verified.sourceFiles,
      contractName: verified.contractName,
      compilerVersion: verified.compilerVersion,
      abi: verified.abi,
      verified: true,
    } as ResolvedSource;
  }

  // Fall back to bytecode
  const bytecode = await fetchBytecode(address, chain);
  return {
    ...base,
    sourceType: 'bytecode_only',
    bytecode: bytecode ?? '0x',
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
        .filter((f: any) => f.type === 'blob' && (f.path?.endsWith('.sol') || f.path?.endsWith('.rs')))
        .map((f: any) => `https://raw.githubusercontent.com/${owner}/${repo}/${defaultBranch}/${f.path}`)
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

export async function resolveSolanaProgram(programId: string): Promise<ResolvedSource> {
  // Solana program accounts are not human-readable source — pass ID for HexStrike Solana path
  return {
    targetType: 'contract_solana',
    sourceType: 'solana_program',
    programId,
    chain: 'solana',
    verified: false,
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
      throw new Error(`Unsupported target type: ${(target as any).type}`);
  }
}
