/**
 * monitoring/route.ts
 * API endpoints for contract monitoring management.
 *
 * POST /api/monitoring/watch — add a contract to the watch list
 * GET  /api/monitoring/watch — list watched contracts
 * DELETE /api/monitoring/watch — remove a contract from the watch list
 * GET  /api/monitoring/events — get recent monitoring events
 */

import { NextRequest, NextResponse } from 'next/server';

// ─── In-Memory Monitoring State ───────────────────────────────────────────────

interface WatchedContract {
  address: string;
  chain: string;
  label: string;
  addedAt: string;
  lastChecked: string | null;
  lastBytecodeHash: string | null;
  active: boolean;
}

interface MonitorEvent {
  id: string;
  type: 'bytecode_change' | 'admin_transfer' | 'proxy_upgrade' | 'new_block';
  address: string;
  chain: string;
  timestamp: string;
  details: Record<string, string>;
}

declare global {
  // eslint-disable-next-line no-var
  var __watchedContracts: Map<string, WatchedContract> | undefined;
  // eslint-disable-next-line no-var
  var __monitorEvents: MonitorEvent[] | undefined;
}

function getWatchedContracts(): Map<string, WatchedContract> {
  if (!globalThis.__watchedContracts) {
    globalThis.__watchedContracts = new Map();
  }
  return globalThis.__watchedContracts;
}

function getMonitorEvents(): MonitorEvent[] {
  if (!globalThis.__monitorEvents) {
    globalThis.__monitorEvents = [];
  }
  return globalThis.__monitorEvents;
}

// ─── Handlers ─────────────────────────────────────────────────────────────────

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  if (action === 'events') {
    const events = getMonitorEvents();
    const limit = parseInt(searchParams.get('limit') || '50', 10);
    const address = searchParams.get('address');

    let filtered = events;
    if (address) {
      filtered = events.filter(e => e.address.toLowerCase() === address.toLowerCase());
    }

    return NextResponse.json({
      events: filtered.slice(-limit),
      total: filtered.length,
    });
  }

  // Default: list watched contracts
  const contracts = Array.from(getWatchedContracts().values())
    .filter(c => c.active);

  return NextResponse.json({
    contracts,
    total: contracts.length,
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { address, chain, label } = body;

    if (!address || !chain) {
      return NextResponse.json(
        { error: 'address and chain are required' },
        { status: 400 }
      );
    }

    const key = `${chain}:${address.toLowerCase()}`;
    const contracts = getWatchedContracts();

    if (contracts.has(key)) {
      const existing = contracts.get(key)!;
      existing.active = true;
      existing.label = label || existing.label;
      return NextResponse.json({ contract: existing, action: 'updated' });
    }

    const contract: WatchedContract = {
      address: address.toLowerCase(),
      chain,
      label: label || address.slice(0, 10) + '...',
      addedAt: new Date().toISOString(),
      lastChecked: null,
      lastBytecodeHash: null,
      active: true,
    };

    contracts.set(key, contract);

    return NextResponse.json({ contract, action: 'created' }, { status: 201 });
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json();
    const { address, chain } = body;

    if (!address || !chain) {
      return NextResponse.json(
        { error: 'address and chain are required' },
        { status: 400 }
      );
    }

    const key = `${chain}:${address.toLowerCase()}`;
    const contracts = getWatchedContracts();

    if (!contracts.has(key)) {
      return NextResponse.json({ error: 'Contract not found' }, { status: 404 });
    }

    const contract = contracts.get(key)!;
    contract.active = false;

    return NextResponse.json({ contract, action: 'deactivated' });
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}
