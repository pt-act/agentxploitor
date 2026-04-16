/**
 * solana-client.ts
 * Solana RPC wrapper for AgentxploiTor program analysis.
 * Uses QuickNode Solana endpoint for on-chain data.
 */

// ─── Config ───────────────────────────────────────────────────────────────────

const SOLANA_RPC_URL = process.env.QUICKNODE_SOLANA_URL || '';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SolanaRpcAccountValue {
  lamports: number;
  data: string | [string, string];
  owner: string;
  executable: boolean;
  rentEpoch: number;
}

interface SolanaAccountRpcResult {
  value: SolanaRpcAccountValue | null;
}

interface SolanaParsedAccountRpcResult {
  value: {
    lamports: number;
    data: {
      parsed?: {
        info?: {
          upgradeAuthority?: string;
        };
      };
    } & { [key: string]: unknown };
    owner: string;
    executable: boolean;
    rentEpoch: number;
  } | null;
}

interface SolanaMultipleAccountsRpcResult {
  value: (SolanaRpcAccountValue | null)[];
}

export interface SolanaAccountInfo {
  lamports: number;
  data: string; // base64 encoded
  owner: string;
  executable: boolean;
  rentEpoch: number;
}

export interface SolanaProgramInfo {
  programId: string;
  accountInfo: SolanaAccountInfo;
  dataSize: number;
  isUpgradeable: boolean;
  upgradeAuthority: string | null;
  dataLength: number;
}

// ─── RPC Helper ───────────────────────────────────────────────────────────────

async function solanaRpc<T = Record<string, unknown>>(method: string, params: unknown[] = []): Promise<T> {
  if (!SOLANA_RPC_URL) {
    throw new Error('QUICKNODE_SOLANA_URL not configured');
  }

  const response = await fetch(SOLANA_RPC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method,
      params,
    }),
    signal: AbortSignal.timeout(15_000),
  });

  if (!response.ok) {
    throw new Error(`Solana RPC ${response.status}`);
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(`Solana RPC error: ${data.error.message}`);
  }

  return data.result;
}

// ─── Account Queries ──────────────────────────────────────────────────────────

/**
 * Gets account info for a Solana address.
 * Use for program accounts, token accounts, or any on-chain data.
 */
export async function getAccountInfo(
  address: string,
  encoding: 'base64' | 'jsonParsed' = 'base64'
): Promise<SolanaAccountInfo | null> {
  try {
    const result = await solanaRpc<SolanaAccountRpcResult>('getAccountInfo', [
      address,
      { encoding, commitment: 'confirmed' },
    ]);

    if (!result?.value) return null;

    const v = result.value;
    return {
      lamports: v.lamports,
      data: Array.isArray(v.data) ? v.data[0] : v.data,
      owner: v.owner,
      executable: v.executable,
      rentEpoch: v.rentEpoch,
    };
  } catch {
    return null;
  }
}

/**
 * Gets program account info with upgrade authority detection.
 * For Anchor programs, checks if the program has an upgrade authority.
 */
export async function getSolanaProgram(
  programId: string
): Promise<SolanaProgramInfo | null> {
  const accountInfo = await getAccountInfo(programId);
  if (!accountInfo) return null;

  // Check for upgradeable loader (BPFLoaderUpgradeab1e11111111111111111111111)
  const isUpgradeable = accountInfo.owner === 'BPFLoaderUpgradeab1e11111111111111111111111';

  let upgradeAuthority: string | null = null;
  if (isUpgradeable) {
    // For upgradeable programs, the upgrade authority is stored in the program data account
    try {
      // The program data account PDA is derived from the program ID
      const programDataResult = await solanaRpc<SolanaParsedAccountRpcResult>('getAccountInfo', [
        programId,
        { encoding: 'jsonParsed', commitment: 'confirmed' },
      ]);

      if (programDataResult?.value?.data?.parsed?.info?.upgradeAuthority) {
        upgradeAuthority = programDataResult.value.data.parsed.info.upgradeAuthority;
      }
    } catch {
      // Could not read upgrade authority
    }
  }

  return {
    programId,
    accountInfo,
    dataSize: typeof accountInfo.data === 'string'
      ? Buffer.from(accountInfo.data, 'base64').length
      : 0,
    isUpgradeable,
    upgradeAuthority,
    dataLength: accountInfo.data.length,
  };
}

/**
 * Gets the current slot number.
 */
export async function getSlot(): Promise<number> {
  return solanaRpc<number>('getSlot', [{ commitment: 'confirmed' }]);
}

/**
 * Gets multiple accounts in a single RPC call.
 */
export async function getMultipleAccounts(
  addresses: string[],
  encoding: 'base64' | 'jsonParsed' = 'base64'
): Promise<(SolanaAccountInfo | null)[]> {
  try {
    const result = await solanaRpc<SolanaMultipleAccountsRpcResult>('getMultipleAccounts', [
      addresses,
      { encoding, commitment: 'confirmed' },
    ]);

    return (result?.value ?? []).map((v) =>
      v
        ? {
            lamports: v.lamports,
            data: Array.isArray(v.data) ? v.data[0] : v.data,
            owner: v.owner,
            executable: v.executable,
            rentEpoch: v.rentEpoch,
          }
        : null
    );
  } catch {
    return addresses.map(() => null);
  }
}
