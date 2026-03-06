import { NextRequest, NextResponse } from 'next/server';
import { jobStore } from '~/lib/storage';
import { buildReport, HexStrikeFinding } from '~/lib/report-builder';

// ─── GET /api/audit/results/[id] ─────────────────────────────────────────────
// Returns the full structured audit report for a completed job.
// Generates report on-the-fly from stored HexStrike findings.

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    // Load job from store
    const jobs = await jobStore.list();
    const job = jobs.find(j => j.id === id);

    if (!job) {
      return NextResponse.json({ error: 'Audit not found' }, { status: 404 });
    }

    if (job.status !== 'completed') {
      return NextResponse.json(
        { error: 'Audit not yet complete', status: job.status },
        { status: 202 }
      );
    }

    // Build report from stored findings
    const hexStrikeFindings: HexStrikeFinding[] = (job.findings ?? []) as HexStrikeFinding[];

    const built = buildReport({
      jobId: job.id,
      targetValue: job.targetUrl ?? job.contractAddress ?? 'unknown',
      auditType: job.auditType ?? 'contract_basic',
      chain: job.blockchain ?? 'base',
      requestedByFid: job.requestedByFid ?? 0,
      hexStrikeFindings,
      agentsUsed: job.agentsUsed,
    });

    return NextResponse.json({
      auditId: job.id,
      status: job.status,
      verdict: built.verdict,
      findingCount: built.findingCount,
      report: built.report,
      declaration: built.declaration,
      markdownReport: built.markdownReport,
      meta: {
        targetType: job.targetType,
        auditType: job.auditType,
        chain: job.blockchain ?? 'base',
        paymentToken: job.paymentToken,
        requestedByFid: job.requestedByFid,
        completedAt: job.updatedAt,
        // FarCaster Miniapp Auditor fields
        mode: job.mode,
        persona: job.persona,
        analysisType: job.analysisType,
      },
    });

  } catch (err) {
    console.error('[results] error:', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
