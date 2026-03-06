import { NextRequest, NextResponse } from 'next/server';

const mockReasoningEvents: ReasoningEvent[] = [
  {
    id: 'evt-001',
    timestamp: new Date().toISOString(),
    type: 'thought',
    content: 'Analyzing target URL for potential vulnerabilities...',
    metadata: { step: 1, totalSteps: 5 },
  },
  {
    id: 'evt-002',
    timestamp: new Date().toISOString(),
    type: 'action',
    content: 'Running Slither static analysis...',
    metadata: { analyzer: 'slither', step: 2, totalSteps: 5 },
  },
  {
    id: 'evt-003',
    timestamp: new Date().toISOString(),
    type: 'observation',
    content: 'Found 3 high-severity issues in reentrancy pattern',
    metadata: { analyzer: 'slither', confidence: 0.95 },
  },
  {
    id: 'evt-004',
    timestamp: new Date().toISOString(),
    type: 'decision',
    content: 'Prioritizing reentrancy vulnerability for exploit generation',
    metadata: { confidence: 0.92 },
  },
  {
    id: 'evt-005',
    timestamp: new Date().toISOString(),
    type: 'action',
    content: 'Generating exploit proof-of-concept...',
    metadata: { step: 3, totalSteps: 5 },
  },
];

interface ReasoningEvent {
  id: string;
  timestamp: string;
  type: 'thought' | 'action' | 'observation' | 'decision' | 'error';
  content: string;
  metadata?: {
    step?: number;
    totalSteps?: number;
    analyzer?: string;
    confidence?: number;
    duration?: number;
  };
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const since = searchParams.get('since');
    const limit = parseInt(searchParams.get('limit') || '50', 10);

    let events = mockReasoningEvents;

    if (since) {
      const sinceDate = new Date(since);
      events = events.filter((e) => new Date(e.timestamp) > sinceDate);
    }

    events = events.slice(0, limit);

    return NextResponse.json({
      auditId: id,
      events,
      hasMore: false,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error fetching reasoning events:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
