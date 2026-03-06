import { NextRequest, NextResponse } from 'next/server';
import { TargetType, ResolvedTarget } from '~/lib/types';

// ─── Input Detection ─────────────────────────────────────────────────────────

function detectInputType(raw: string): { type: TargetType | 'plain_name'; chain?: string } {
  const trimmed = raw.trim();

  // EVM contract address: 0x + 40 hex chars
  if (/^0x[0-9a-fA-F]{40}$/.test(trimmed)) {
    return { type: 'contract_evm', chain: 'base' };
  }

  // Solana program address: base58, 32–44 chars
  if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed) && !trimmed.startsWith('http')) {
    return { type: 'contract_solana' };
  }

  // GitHub repo URL
  if (/^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+/.test(trimmed)) {
    return { type: 'github_repo' };
  }

  // HTTPS URL (miniapp)
  if (/^https?:\/\//.test(trimmed)) {
    return { type: 'miniapp_url' };
  }

  // Plain name — needs discovery
  return { type: 'plain_name' };
}

// ─── Tier 1: Warpcast API ────────────────────────────────────────────────────

async function resolveViaWarpcast(name: string): Promise<ResolvedTarget | null> {
  try {
    // Search Warpcast for miniapps matching the name
    const res = await fetch(
      `https://api.warpcast.com/v2/search-frames?q=${encodeURIComponent(name)}`,
      {
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(5000),
      }
    );
    if (!res.ok) return null;
    const data = await res.json();

    // First result that has a valid HTTPS URL
    const frame = data?.result?.frames?.[0];
    if (frame?.homeUrl) {
      return {
        type: 'miniapp_url',
        value: frame.homeUrl,
        confirmedByUser: false,
      };
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Tier 2: GitHub Search API ───────────────────────────────────────────────

async function resolveViaGitHub(name: string): Promise<ResolvedTarget | null> {
  try {
    const res = await fetch(
      `https://api.github.com/search/repositories?q=${encodeURIComponent(name)}+topic:farcaster+topic:base&sort=stars&per_page=1`,
      {
        headers: {
          'Accept': 'application/vnd.github+json',
          ...(process.env.GITHUB_TOKEN
            ? { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` }
            : {}),
        },
        signal: AbortSignal.timeout(5000),
      }
    );
    if (!res.ok) return null;
    const data = await res.json();

    const repo = data?.items?.[0];
    if (repo?.html_url) {
      return {
        type: 'github_repo',
        value: repo.html_url,
        confirmedByUser: false,
      };
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Route Handler ────────────────────────────────────────────────────────────

export async function POST(req: NextRequest) {
  try {
    const { rawInput } = await req.json();

    if (!rawInput || typeof rawInput !== 'string' || rawInput.trim().length === 0) {
      return NextResponse.json({ error: 'rawInput is required' }, { status: 400 });
    }

    const trimmed = rawInput.trim();
    const detected = detectInputType(trimmed);

    // ── Direct resolution (no discovery needed) ──────────────────────────────
    if (detected.type !== 'plain_name') {
      // Chain support check
      if (detected.type === 'contract_evm' && detected.chain) {
        const supportedChains = ['base'];
        const comingSoon = ['ethereum', 'arbitrum', 'optimism', 'polygon', 'bsc'];

        if (!supportedChains.includes(detected.chain)) {
          const isComingSoon = comingSoon.includes(detected.chain);
          return NextResponse.json({
            resolved: false,
            reason: isComingSoon
              ? `${detected.chain} support coming soon — Base is currently supported`
              : 'unsupported_chain',
            tier: 0,
          });
        }
      }

      return NextResponse.json({
        resolved: true,
        target: {
          type: detected.type,
          value: trimmed,
          chain: detected.chain,
          confirmedByUser: false,
        } satisfies ResolvedTarget,
        tier: 0, // Direct — no discovery needed
      });
    }

    // ── Tier 1: Warpcast API ─────────────────────────────────────────────────
    const warpcastResult = await resolveViaWarpcast(trimmed);
    if (warpcastResult) {
      return NextResponse.json({
        resolved: true,
        target: warpcastResult,
        tier: 1,
        source: 'warpcast',
      });
    }

    // ── Tier 2: GitHub Search ────────────────────────────────────────────────
    const githubResult = await resolveViaGitHub(trimmed);
    if (githubResult) {
      return NextResponse.json({
        resolved: true,
        target: githubResult,
        tier: 2,
        source: 'github',
      });
    }

    // ── Tier 3: Ask user ─────────────────────────────────────────────────────
    return NextResponse.json({
      resolved: false,
      reason: 'not_found',
      tier: 3,
      message: `Could not automatically resolve "${trimmed}". Please provide a direct URL or contract address.`,
    });
  } catch (err) {
    console.error('[discover] error:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
