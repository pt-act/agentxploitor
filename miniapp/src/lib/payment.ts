/**
 * Payment verification for AgentxploiTor
 * Verifies BNKR/ERC-20 transfers on Base network
 */

import { createPublicClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';

const ERC20_ABI = parseAbi([
  'function transfer(address to, uint256 amount) returns (bool)',
  'function transferFrom(address from, address to, uint256 amount) returns (bool)',
  'event Transfer(address indexed from, address indexed to, uint256 value)',
]);

const BNKR_CONTRACT = (process.env.NEXT_PUBLIC_BNKR_CONTRACT_ADDRESS || '0x') as `0x${string}`;
const TREASURY_ADDRESS = (process.env.NEXT_PUBLIC_TREASURY_ADDRESS || '0x') as `0x${string}`;
const BASE_RPC_URL = process.env.NEXT_PUBLIC_BASE_RPC_URL || 'https://mainnet.base.org';
const MIN_AUDIT_PRICE_BNKR = BigInt(process.env.MIN_AUDIT_PRICE_BNKR || '100000000000000000000'); // 100 BNKR default

interface PaymentVerificationResult {
  valid: boolean;
  amount?: bigint;
  blockNumber?: bigint;
  confirmations?: number;
  error?: string;
}

// TransferEvent type removed — not currently used

function getBaseClient() {
  return createPublicClient({
    chain: base,
    transport: http(BASE_RPC_URL),
  });
}

export async function verifyBNKRPayment(
  txHash: `0x${string}`,
  expectedSender: `0x${string}`,
  minAmount?: bigint
): Promise<PaymentVerificationResult> {
  const client = getBaseClient();
  const minRequired = minAmount || MIN_AUDIT_PRICE_BNKR;
  
  try {
    const receipt = await client.getTransactionReceipt({ hash: txHash });
    
    if (!receipt) {
      return { valid: false, error: 'Transaction not found' };
    }
    
    const currentBlock = await client.getBlockNumber();
    const confirmations = Number(currentBlock - receipt.blockNumber) + 1;
    
    if (receipt.status !== 'success') {
      return { valid: false, error: 'Transaction failed', confirmations };
    }
    
    if (!receipt.to || receipt.to.toLowerCase() !== BNKR_CONTRACT.toLowerCase()) {
      return { valid: false, error: 'Not a BNKR transfer', confirmations };
    }
    
    const transferTopic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
    
    for (const log of receipt.logs) {
      if (log.address.toLowerCase() !== BNKR_CONTRACT.toLowerCase()) continue;
      if (!log.topics || log.topics.length < 3 || log.topics[0] !== transferTopic) continue;
      
      const from = `0x${log.topics[1]!.slice(26)}` as `0x${string}`;
      const to = `0x${log.topics[2]!.slice(26)}` as `0x${string}`;
      const value = BigInt(log.data);
      
      if (
        from.toLowerCase() === expectedSender.toLowerCase() &&
        to.toLowerCase() === TREASURY_ADDRESS.toLowerCase()
      ) {
        if (value >= minRequired) {
          return {
            valid: true,
            amount: value,
            blockNumber: receipt.blockNumber,
            confirmations,
          };
        } else {
          return {
            valid: false,
            amount: value,
            error: `Insufficient amount. Required: ${minRequired.toString()}, got: ${value.toString()}`,
            confirmations,
          };
        }
      }
    }
    
    return {
      valid: false,
      error: 'No valid BNKR transfer to treasury found',
      confirmations,
    };
    
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { valid: false, error: `Verification failed: ${message}` };
  }
}

export async function verifyERC20Payment(
  txHash: `0x${string}`,
  tokenAddress: `0x${string}`,
  expectedSender: `0x${string}`,
  recipientAddress: `0x${string}`,
  minAmount: bigint
): Promise<PaymentVerificationResult> {
  const client = getBaseClient();
  
  try {
    const receipt = await client.getTransactionReceipt({ hash: txHash });
    
    if (!receipt) {
      return { valid: false, error: 'Transaction not found' };
    }
    
    const currentBlock = await client.getBlockNumber();
    const confirmations = Number(currentBlock - receipt.blockNumber) + 1;
    
    if (receipt.status !== 'success') {
      return { valid: false, error: 'Transaction failed', confirmations };
    }
    
    const transferTopic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
    
    for (const log of receipt.logs) {
      if (log.address.toLowerCase() !== tokenAddress.toLowerCase()) continue;
      if (!log.topics || log.topics.length < 3 || log.topics[0] !== transferTopic) continue;
      
      const from = `0x${log.topics[1]!.slice(26)}` as `0x${string}`;
      const to = `0x${log.topics[2]!.slice(26)}` as `0x${string}`;
      const value = BigInt(log.data);
      
      if (
        from.toLowerCase() === expectedSender.toLowerCase() &&
        to.toLowerCase() === recipientAddress.toLowerCase()
      ) {
        if (value >= minAmount) {
          return {
            valid: true,
            amount: value,
            blockNumber: receipt.blockNumber,
            confirmations,
          };
        } else {
          return {
            valid: false,
            amount: value,
            error: `Insufficient amount. Required: ${minAmount.toString()}, got: ${value.toString()}`,
            confirmations,
          };
        }
      }
    }
    
    return {
      valid: false,
      error: 'No valid transfer found',
      confirmations,
    };
    
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { valid: false, error: `Verification failed: ${message}` };
  }
}

export async function getBNKRBalance(address: `0x${string}`): Promise<bigint> {
  const client = getBaseClient();
  
  try {
    const balance = await client.readContract({
      address: BNKR_CONTRACT,
      abi: ERC20_ABI,
      functionName: 'balanceOf',
      args: [address],
    });
    
    return balance as bigint;
  } catch {
    return BigInt(0);
  }
}

export function formatBNKR(amount: bigint): string {
  const decimals = 18n;
  const divisor = 10n ** decimals;
  const whole = amount / divisor;
  const fraction = amount % divisor;
  
  if (fraction === 0n) {
    return whole.toString();
  }
  
  const fractionStr = fraction.toString().padStart(18, '0').replace(/0+$/, '');
  return `${whole}.${fractionStr}`;
}

export const PAYMENT_CONFIG = {
  bnkrContract: BNKR_CONTRACT,
  treasuryAddress: TREASURY_ADDRESS,
  minAuditPrice: MIN_AUDIT_PRICE_BNKR,
  requiredConfirmations: 3,
};
