import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@farcaster/quick-auth';
import { validateTargetUrl, generateSecureAuditId } from '~/lib/security';
import { verifyBNKRPayment, PAYMENT_CONFIG } from '~/lib/payment';
import { createJob, jobStore } from '~/lib/storage';
import type { JobSession } from '~/lib/types';

const client = createClient();

function getUrlHost(request: NextRequest): string {
  const origin = request.headers.get('origin');
  if (origin) {
    try {
      const url = new URL(origin);
      return url.host;
    } catch {
      // fall through
    }
  }

  const host = request.headers.get('host');
  if (host) {
    return host;
  }

  let urlValue: string;
  if (process.env.VERCEL_ENV === 'production') {
    urlValue = process.env.NEXT_PUBLIC_URL!;
  } else if (process.env.VERCEL_URL) {
    urlValue = `https://${process.env.VERCEL_URL}`;
  } else {
    urlValue = 'http://localhost:3000';
  }

  const url = new URL(urlValue);
  return url.host;
}

async function verifyAuth(request: NextRequest): Promise<{ fid: string } | null> {
  const authorization = request.headers.get('Authorization');
  
  if (!authorization || !authorization.startsWith('Bearer ')) {
    return null;
  }

  try {
    const payload = await client.verifyJwt({
      token: authorization.split(' ')[1],
      domain: getUrlHost(request),
    });
    return { fid: String(payload.sub) };
  } catch {
    return null;
  }
}

export async function POST(request: NextRequest) {
  try {
    const auth = await verifyAuth(request);
    if (!auth) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const body = await request.json();

    const {
      // Original fields
      targetUrl,
      contractAddress,
      scope,
      priority,
      paymentTxHash,
      paymentAmount,
      walletAddress,
      // New fields — Group 2
      auditType,       // 'contract_basic' | 'contract_deep' | 'miniapp' | 'full_stack'
      targetType,      // 'contract_evm' | 'contract_solana' | 'github_repo' | 'miniapp_url'
      githubUrl,       // GitHub repo URL (alternative to targetUrl)
      blockchain,      // 'base' | 'ethereum' | 'solana' etc.
      rawInput,        // exactly what user typed in the input field
      resolvedTarget,  // confirmed resolved target object
      discoveryTier,   // 1 | 2 | 3 — which tier found the target
      paymentToken,    // 'eth' | 'usdc' | 'bnkr'
      // FarCaster Miniapp Auditor fields
      persona,         // 'researcher' | 'developer' | 'contract_dev'
      mode,           // 'self_audit' | 'research' | 'contract'
      analysisType,   // 'contract' | 'frontend' | 'full_stack'
    } = body;

    // At least one target input required
    const hasTarget = targetUrl || contractAddress || githubUrl
    if (!hasTarget || !priority) {
      return NextResponse.json(
        { error: 'Missing required fields: at least one of targetUrl, contractAddress, githubUrl; and priority' },
        { status: 400 }
      );
    }

    if (!walletAddress) {
      return NextResponse.json(
        { error: 'Wallet address required' },
        { status: 400 }
      );
    }

    // Validate URL targets (skip for contract addresses and GitHub URLs)
    if (targetUrl) {
      const urlValidation = validateTargetUrl(targetUrl);
      if (!urlValidation.valid) {
        return NextResponse.json(
          { error: urlValidation.error },
          { status: 400 }
        );
      }
    }

    let paymentVerified = false;
    if (paymentTxHash) {
      const verification = await verifyBNKRPayment(
        paymentTxHash as `0x${string}`,
        walletAddress as `0x${string}`
      );

      if (!verification.valid) {
        return NextResponse.json(
          { error: `Payment verification failed: ${verification.error}` },
          { status: 400 }
        );
      }

      paymentVerified = true;
    }

    const auditId = generateSecureAuditId();
    const status: JobSession['status'] = paymentVerified ? 'payment_verified' : 'pending_payment';

    const job = await createJob({
      id: auditId,
      targetUrl: targetUrl || githubUrl || contractAddress,
      contractAddress,
      githubUrl,
      blockchain: blockchain || 'base',
      auditType: auditType || 'contract_basic',
      targetType: targetType || (contractAddress?.startsWith('0x') ? 'contract_evm' : 'miniapp_url'),
      rawInput,
      resolvedTarget,
      discoveryTier,
      paymentToken: paymentToken || 'usdc',
      scope: scope || auditType || 'full',
      priority,
      status,
      createdBy: auth.fid,
      requestedByFid: parseInt(auth.fid, 10),
      walletAddress,
      paymentTxHash,
      paymentAmount,
      paymentVerified,
      // FarCaster Miniapp Auditor fields
      persona,
      mode,
      analysisType,
    });

    // Sync to global store for audit worker
    if (typeof global !== 'undefined' && global.__auditJobStore) {
      global.__auditJobStore.set(auditId, {
        ...job,
        requestedByFid: parseInt(auth.fid, 10),
      });
    }

    if (paymentVerified) {
      await jobStore.enqueue(auditId);
    }

    console.log('[AuditRequest] Created:', {
      id: auditId,
      fid: auth.fid,
      auditType,
      targetType,
      status,
      paymentToken,
      paymentVerified,
    });

    return NextResponse.json({
      auditId,
      status: job.status,
      queuePosition: paymentVerified ? 1 : undefined,
      estimatedStart: paymentVerified
        ? new Date(Date.now() + 5 * 60 * 1000).toISOString()
        : undefined,
      paymentRequired: !paymentVerified,
      treasuryAddress: PAYMENT_CONFIG.treasuryAddress,
      bnkrContract: PAYMENT_CONFIG.bnkrContract,
      minAmount: PAYMENT_CONFIG.minAuditPrice.toString(),
    });

  } catch (error) {
    console.error('Error creating audit request:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const walletAddress = searchParams.get('wallet');
    
    const jobs = await jobStore.list(walletAddress || undefined);
    
    return NextResponse.json({
      jobs: jobs.slice(0, 20).map(j => ({
        id: j.id,
        targetUrl: j.targetUrl,
        status: j.status,
        createdAt: j.createdAt,
        findingsCount: j.findingsCount,
      })),
      total: jobs.length,
    });
  } catch (error) {
    console.error('Error listing jobs:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
