import { NextRequest, NextResponse } from 'next/server';

const mockAudits = [
  {
    id: 'audit-001',
    targetUrl: 'https://example.com/dapp',
    status: 'completed',
    findingsCount: { critical: 2, high: 5, medium: 8, low: 3 },
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    completedAt: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'audit-002',
    targetUrl: 'https://protocol.example.com',
    status: 'in_progress',
    findingsCount: { critical: 1, high: 2, medium: 0, low: 0 },
    createdAt: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 'audit-003',
    targetUrl: 'https://dao.example.org',
    status: 'queued',
    findingsCount: { critical: 0, high: 0, medium: 0, low: 0 },
    createdAt: new Date(Date.now() - 1800000).toISOString(),
  },
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '10', 10);
    const status = searchParams.get('status');

    let audits = mockAudits;

    if (status) {
      audits = audits.filter((a) => a.status === status);
    }

    audits = audits.slice(0, limit);

    return NextResponse.json({ audits });
  } catch (error) {
    console.error('Error fetching audits:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
