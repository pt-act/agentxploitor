import { NextRequest, NextResponse } from 'next/server';

const MOCK_METRICS = `# HELP agentxploitor_jobs_total Total number of jobs processed
# TYPE agentxploitor_jobs_total counter
agentxploitor_jobs_total{status="completed",priority="normal",workspace_id="ws-001"} 42
agentxploitor_jobs_total{status="failed",priority="high",workspace_id="ws-001"} 3

# HELP agentxploitor_job_latency_seconds Job processing latency in seconds
# TYPE agentxploitor_job_latency_seconds histogram
agentxploitor_job_latency_seconds_bucket{status="completed",priority="normal",le="1"} 5
agentxploitor_job_latency_seconds_bucket{status="completed",priority="normal",le="5"} 15
agentxploitor_job_latency_seconds_bucket{status="completed",priority="normal",le="10"} 30
agentxploitor_job_latency_seconds_bucket{status="completed",priority="normal",le="+Inf"} 42

# HELP agentxploitor_queue_depth Current number of jobs in queue
# TYPE agentxploitor_queue_depth gauge
agentxploitor_queue_depth{priority="normal"} 5
agentxploitor_queue_depth{priority="high"} 2
agentxploitor_queue_depth{priority="low"} 8

# HELP agentxploitor_processing_jobs Number of jobs currently being processed
# TYPE agentxploitor_processing_jobs gauge
agentxploitor_processing_jobs 3

# HELP agentxploitor_analyzer_runs_total Total number of analyzer runs
# TYPE agentxploitor_analyzer_runs_total counter
agentxploitor_analyzer_runs_total{analyzer="slither",result="success"} 35
agentxploitor_analyzer_runs_total{analyzer="mythril",result="success"} 28
agentxploitor_analyzer_runs_total{analyzer="slither",result="error"} 2

# HELP agentxploitor_audits_completed_total Total number of completed audits
# TYPE agentxploitor_audits_completed_total counter
agentxploitor_audits_completed_total{workspace_id="ws-001"} 15

# HELP agentxploitor_audit_cost_dollars Cost per audit in dollars
# TYPE agentxploitor_audit_cost_dollars histogram
agentxploitor_audit_cost_dollars_bucket{workspace_id="ws-001",le="0.01"} 2
agentxploitor_audit_cost_dollars_bucket{workspace_id="ws-001",le="0.1"} 8
agentxploitor_audit_cost_dollars_bucket{workspace_id="ws-001",le="1"} 15

# HELP agentxploitor_active_workers Number of active worker processes
# TYPE agentxploitor_active_workers gauge
agentxploitor_active_workers 4

# HELP agentxploitor_circuit_breaker_state Circuit breaker state (0=closed, 1=half-open, 2=open)
# TYPE agentxploitor_circuit_breaker_state gauge
agentxploitor_circuit_breaker_state{service="slither"} 0
agentxploitor_circuit_breaker_state{service="mythril"} 0
agentxploitor_circuit_breaker_state{service="llm"} 0

# HELP agentxploitor_app_info AgentxploiTor application information
# TYPE agentxploitor_app_info info
agentxploitor_app_info{version="2.0.0",service="agentxploitor"} 1
`;

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'prometheus';

    if (format === 'json') {
      const metrics = {
        jobs: {
          completed: 42,
          failed: 3,
          total: 45,
        },
        queue: {
          normal: 5,
          high: 2,
          low: 8,
          processing: 3,
        },
        analyzers: {
          slither: { success: 35, error: 2 },
          mythril: { success: 28, error: 0 },
        },
        audits: {
          completed: 15,
          avgCost: 0.45,
        },
        workers: {
          active: 4,
        },
        circuitBreakers: {
          slither: 'closed',
          mythril: 'closed',
          llm: 'closed',
        },
        timestamp: new Date().toISOString(),
      };

      return NextResponse.json(metrics, {
        headers: {
          'Cache-Control': 'no-store',
        },
      });
    }

    return new NextResponse(MOCK_METRICS, {
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('Error fetching metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch metrics' },
      { status: 500 }
    );
  }
}

export async function HEAD() {
  return new NextResponse(null, {
    headers: {
      'Content-Type': 'text/plain',
    },
  });
}
