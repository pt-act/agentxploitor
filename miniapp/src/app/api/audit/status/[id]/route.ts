import { NextRequest, NextResponse } from 'next/server';
import { validateAuditId } from '~/lib/security';
import { getJob } from '~/lib/storage';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    if (!validateAuditId(id)) {
      return NextResponse.json(
        { error: 'Invalid audit ID format' },
        { status: 400 }
      );
    }

    const job = await getJob(id);
    
    if (!job) {
      return NextResponse.json(
        { error: 'Audit not found' },
        { status: 404 }
      );
    }

    const response = {
      id: job.id,
      targetUrl: job.targetUrl,
      status: job.status,
      queuePosition: job.status === 'queued' ? 1 : 0,
      progress: calculateProgress(job.status),
      findings: job.findingsCount || { critical: 0, high: 0, medium: 0, low: 0 },
      paymentVerified: job.paymentVerified,
      error: job.error,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      completedAt: job.status === 'completed' ? job.updatedAt : undefined,
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error fetching audit status:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

function calculateProgress(status: string): number {
  const progressMap: Record<string, number> = {
    pending_payment: 0,
    payment_verified: 10,
    queued: 15,
    in_progress: 50,
    completed: 100,
    failed: 100,
    cancelled: 100,
  };
  return progressMap[status] || 0;
}
