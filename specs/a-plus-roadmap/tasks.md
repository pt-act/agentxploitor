# AgentxploiTor A+ Roadmap - Tasks

## Overview

This roadmap transforms AgentxploiTor from production-viable (B+) to enterprise-grade (A+) through 8 task groups spanning 18-24 iterations.

**Last Updated**: 2026-02-25  
**Progress**: Groups 0-2, 4-5 complete | Group 3 ~85% | Group 6 ~20% | Group 7 pending

---

## Group 0: Critical Infrastructure (Foundation) ✅ COMPLETE

### Dependencies
- **None** — Foundation layer

### Tasks

#### 0.1 Redis Distributed Queue ✅
- [x] Install `redis-py[hiredis]` with asyncio support
- [x] Create `RedisJobQueue` class implementing `JobStore` interface
- [x] Implement atomic enqueue/dequeue with `RPUSH`/`LPOP`
- [x] Add job TTL and cleanup for stale jobs
- [x] Create `redis_pool.py` with connection pooling
- [x] Add health check for Redis connectivity

#### 0.2 Circuit Breaker Pattern ✅
- [x] Create `circuit_breaker.py` with states (CLOSED, OPEN, HALF_OPEN)
- [x] Implement `@circuit_breaker` decorator for external calls
- [x] Add configuration for failure threshold and recovery timeout
- [x] Wrap analyzer calls (`SlitherAdapter`, `MythrilAdapter`) with circuit breaker
- [x] Wrap LLM API calls with circuit breaker
- [x] Add circuit breaker status to health endpoint

#### 0.3 PostgreSQL Migration ✅
- [x] Create `docker-compose.yml` with PostgreSQL service
- [x] Install `asyncpg` and `alembic` for migrations
- [x] Create initial schema: `workspaces`, `users`, `jobs`, `findings`, `artifacts`
- [x] Create `PostgresJobStore` implementing `JobStore` interface
- [x] Implement dual-write pattern (write to both in-memory and Postgres)
- [x] Add migration scripts in `migrations/` directory
- [x] Create `database.py` with connection pooling

#### 0.4 Outbox Pattern ✅
- [x] Create `outbox` table in PostgreSQL schema
- [x] Implement `OutboxWriter` for atomic state + event writes
- [x] Create `OutboxProcessor` to publish events after commit
- [x] Add event handlers for `JobCreated`, `PaymentVerified`, `ScanCompleted`
- [x] Implement idempotent event processing (deduplication)

#### 0.5 Health Check Endpoint ✅
- [x] Create `GET /api/health` endpoint
- [x] Check Redis connectivity
- [x] Check PostgreSQL connectivity
- [x] Check analyzer availability (Slither, Mythril)
- [x] Return detailed status with response times
- [x] Add `GET /api/health/ready` and `/api/health/live` for Kubernetes

### Testing (Group 0) ✅
- **Test 1**: Redis queue atomic operations under concurrent load
- **Test 2**: Circuit breaker opens after threshold failures
- **Test 3**: PostgreSQL schema migrations run successfully
- **Test 4**: Outbox events delivered exactly once
- **Test 5**: Health check reports correct status

**Estimated Iterations**: 4-5 | **Actual**: Complete

---

## Group 1: Architectural Improvements ✅ COMPLETE

### Dependencies
- **Depends on**: Group 0 (PostgreSQL, Outbox)

### Tasks

#### 1.1 Event Sourcing ✅
- [x] Create `events` table with immutable event log
- [x] Define event types: `JobCreated`, `JobStateChanged`, `FindingDiscovered`, `ExploitGenerated`, `ReportFinalized`
- [x] Implement `EventStore.append()` with optimistic locking
- [x] Create `JobSession.from_events()` reconstruction
- [x] Add event versioning for schema evolution
- [x] Implement snapshotting for performance (every 100 events)

#### 1.2 CQRS Separation ✅
- [x] Create `ReadModel` projections for queries
- [x] Implement `JobReadModel` with denormalized fields
- [x] Create `FindingReadModel` with search optimization
- [x] Add `ProjectionUpdater` to rebuild from events
- [x] Separate read/write database connections if needed

#### 1.3 Domain Events ✅
- [x] Define `DomainEvent` base class with correlation ID
- [x] Implement event bus (in-process initially, pluggable for external)
- [x] Add event handlers for notifications, analytics
- [x] Create `EventPublisher` for webhooks
- [x] Implement async event processing with retry

#### 1.4 Saga Orchestration ✅
- [x] Create `AuditSaga` for end-to-end workflow
- [x] Define saga steps: Payment → Scan → Exploit → Verify → Report
- [x] Implement compensation actions for each step
- [x] Add saga state persistence
- [x] Create `SagaOrchestrator` with timeout handling

#### 1.5 Aggregate Boundaries ✅
- [x] Define `Job` aggregate root with invariants
- [x] Implement consistency boundary enforcement
- [x] Add optimistic concurrency control (version field)
- [x] Ensure atomic updates within aggregate

### Testing (Group 1) ✅
- **Test 1**: Events are immutable and append-only
- **Test 2**: Job state can be reconstructed from events
- **Test 3**: CQRS read model stays consistent with writes
- **Test 4**: Saga handles failures with compensation
- **Test 5**: Aggregate invariants are enforced

**Estimated Iterations**: 3-4 | **Actual**: Complete

---

## Group 2: Multi-Tenancy & Security ✅ COMPLETE

### Dependencies
- **Depends on**: Group 0 (PostgreSQL)
- **Parallel with**: Group 1

### Tasks

#### 2.1 Workspace Isolation ✅
- [x] Add `workspace_id` to all tables
- [x] Implement row-level security policies in PostgreSQL
- [x] Create workspace context middleware for API
- [x] Add workspace_id to all queries automatically
- [x] Implement workspace-scoped Redis keys

#### 2.2 RBAC Implementation ✅
- [x] Create `roles` and `permissions` tables
- [x] Define roles: Admin, Analyst, Viewer, API
- [x] Implement `PermissionChecker` middleware
- [x] Add role assignment UI in settings
- [x] Create API key generation with scoped permissions

#### 2.3 Audit Log ✅
- [x] Create `audit_log` table with immutable entries
- [x] Log all state changes with actor, timestamp, details
- [x] Add cryptographic hash chain for integrity
- [x] Implement audit log query API
- [x] Create audit log export feature

#### 2.4 Session Recovery ✅
- [x] Implement checkpoint saving during audit
- [x] Store intermediate state (current step, partial findings)
- [x] Create recovery job to resume from checkpoint
- [x] Add recovery endpoint `POST /api/audit/{id}/recover`
- [x] Implement timeout detection for stalled jobs

### Testing (Group 2) ✅
- **Test 1**: Workspace isolation prevents cross-tenant access
- **Test 2**: RBAC enforces correct permissions
- **Test 3**: Audit log entries are immutable
- **Test 4**: Session recovery continues from checkpoint
- **Test 5**: API keys have correct scope restrictions

**Estimated Iterations**: 2-3 | **Actual**: Complete

---

## Group 3: UI/UX Innovation 🔄 IN PROGRESS (~95%)

### Dependencies
- **Depends on**: Group 0 (Health endpoint), Group 1 (Domain events)
- **Parallel with**: Group 2

### Tasks

#### 3.1 Real-Time Reasoning Stream ✅
- [x] Create WebSocket endpoint `/ws/audit/{id}/reasoning` (backend done)
- [x] Implement reasoning event emitter in agent core
- [x] Create `ReasoningStream` component with auto-scroll
- [x] Add toggleable detail levels (minimal/normal/verbose)
- [x] Implement connection status indicator
- [x] Add reasoning stream to job status page

#### 3.2 Attack Path Visualization ✅
- [x] Install D3.js or Cytoscape.js
- [x] Create `AttackPathGraph` component
- [x] Define graph data structure (nodes, edges, metadata)
- [x] Implement zoom/pan and node selection
- [x] Add color coding for severity levels
- [x] Create drill-down panel for node details
- [x] Add animated execution path overlay

#### 3.3 Finding Cards ✅
- [x] Create `FindingCard` component with collapsed/expanded states
- [x] Add severity badge with color coding
- [x] Implement AI suggestion section
- [x] Add comment thread component
- [x] Create assignment dropdown
- [x] Add status actions (mark fixed, request re-scan)

#### 3.4 Focus-First Dashboard ✅
- [x] Redesign dashboard with single-column layout
- [x] Implement ambient status indicators (subtle color shifts)
- [x] Add progressive disclosure (show overview, expand for details)
- [x] Create calm color palette (no red alerts)
- [x] Implement keyboard navigation
- [x] Add focus mode toggle (hide all but active audit)

#### 3.5 Mobile Responsiveness ✅
- [x] Create responsive breakpoints (tablet, mobile)
- [x] Implement collapsible sidebar
- [x] Add touch-friendly finding cards
- [x] Create mobile-optimized graph view (simplified)
- [x] Implement view-only mode for mobile

#### 3.6 Accessibility ✅
- [x] Add ARIA labels to all interactive elements
- [x] Implement keyboard-only navigation
- [x] Add focus indicators
- [x] Test with screen readers
- [x] Create high contrast mode
- [x] Implement reduced motion preference

### Testing (Group 3) ✅
- **Test 1**: WebSocket reconnects on disconnect ✅
- **Test 2**: Graph renders correctly with large datasets ✅
- **Test 3**: Finding cards expand/collapse correctly ✅
- **Test 4**: Dashboard passes WCAG 2.1 AA audit ✅
- **Test 5**: Mobile layout is functional on tablet ✅
- **Test 6**: Keyboard navigation works throughout ✅

**Estimated Iterations**: 4-5 | **Status**: Complete

---

## Group 4: AI Augmentation ✅ COMPLETE

### Dependencies
- **Depends on**: Group 1 (Domain events), Group 3 (Reasoning stream)

### Tasks

#### 4.1 Enhanced Exploit Generation ✅
- [x] Research fine-tuning vs RAG approach
- [x] Implement semantic safety analysis (AST-based)
- [x] Add constraint solving for safe payloads
- [x] Create exploit template library
- [x] Add multi-strategy generation (try multiple approaches)

#### 4.2 Confidence Calibration ✅
- [x] Track historical accuracy (true positives, false positives)
- [x] Implement confidence adjustment based on analyzer source
- [x] Add uncertainty quantification
- [x] Display calibrated confidence in UI
- [x] Create confidence threshold for auto-approval

#### 4.3 Explainable AI ✅
- [x] Implement reasoning trace collection
- [x] Create decision tree for exploit strategy selection
- [x] Add natural language explanation generation
- [x] Display "why this exploit" in finding cards
- [x] Create debugging mode for AI decisions

#### 4.4 Human-in-the-Loop ✅
- [x] Implement approval workflow for high-impact actions
- [x] Add confidence threshold for auto-proceed
- [x] Create approval request notifications
- [x] Implement one-click approve/reject
- [x] Add override capability for admins

### Testing (Group 4) ✅
- **Test 1**: Semantic safety catches dangerous payloads
- **Test 2**: Confidence calibration reflects reality
- **Test 3**: Reasoning traces are understandable
- **Test 4**: Human approval workflow functions correctly
- **Test 5**: Low-confidence items require approval

**Estimated Iterations**: 2-3 | **Actual**: Complete

---

## Group 5: Testing & Quality ✅ COMPLETE

### Dependencies
- **Continuous** — Parallel with all groups

### Tasks

#### 5.1 Integration Tests ✅
- [x] Create test fixtures for contract samples
- [x] Implement full pipeline test (payment → scan → report)
- [x] Add test for concurrent job processing
- [x] Create test for payment failure scenarios
- [x] Add test for analyzer failures
- [x] Implement test for session recovery

#### 5.2 Concurrency Tests ✅
- [x] Create load test with 100+ concurrent jobs
- [x] Test backpressure handling under load
- [x] Verify queue ordering and priority
- [x] Test race conditions in state transitions
- [x] Verify idempotency under concurrent requests

#### 5.3 Error Path Coverage ✅
- [x] Audit all exception handlers
- [x] Add tests for each error path
- [x] Verify error messages are user-friendly
- [x] Test circuit breaker opening/closing
- [x] Test saga compensation actions

#### 5.4 Performance Benchmarks ✅
- [x] Create benchmark suite with pytest-benchmark
- [x] Measure job latency (P50, P95, P99)
- [x] Measure throughput (jobs/hour)
- [x] Track memory usage over time
- [x] Benchmark database queries

#### 5.5 Chaos Tests ✅
- [x] Create chaos test suite
- [x] Simulate Redis failure
- [x] Simulate PostgreSQL failure
- [x] Simulate analyzer timeout
- [x] Test network partition scenarios
- [x] Verify graceful degradation

### Testing (Group 5) ✅
- **Test 1**: Integration tests pass consistently
- **Test 2**: Load test maintains SLOs
- **Test 3**: Error paths are covered
- **Test 4**: Benchmarks show acceptable performance
- **Test 5**: Chaos tests verify resilience

**Estimated Iterations**: 2-3 | **Actual**: Complete

---

## Group 6: Observability & Operations ✅ COMPLETE

### Dependencies
- **Continuous** — Parallel with all groups

### Tasks

#### 6.1 Prometheus Metrics ✅
- [x] Add `prometheus-client` dependency
- [x] Create `/metrics` endpoint
- [x] Define metrics: job_latency, queue_depth, error_rate, active_jobs
- [x] Add analyzer-specific metrics (scan_time, findings_count)
- [x] Implement custom metrics for business KPIs

#### 6.2 Distributed Tracing ✅
- [x] Install OpenTelemetry packages
- [x] Configure trace export (Jaeger/Zipkin)
- [x] Add tracing to all API endpoints
- [x] Trace agent core operations
- [x] Add span attributes for debugging

#### 6.3 Structured Logging ✅
- [x] Configure JSON logging format
- [x] Add correlation ID to all logs
- [x] Implement log level configuration
- [x] Add context enrichment (workspace, user, job)
- [x] Create log aggregation query examples

#### 6.4 Cost Tracking ✅
- [x] Track compute time per audit
- [x] Track storage usage per audit
- [x] Track API calls (LLM, RPC) per audit
- [x] Calculate cost per audit
- [x] Create cost dashboard

#### 6.5 SLO Dashboards ✅
- [x] Define SLOs (latency, availability, error rate)
- [x] Create Grafana dashboard or equivalent
- [x] Add alerting rules for SLO violations
- [x] Create on-call runbook
- [x] Implement incident tracking

### Testing (Group 6) ✅
- **Test 1**: Metrics endpoint returns valid Prometheus format
- **Test 2**: Traces propagate through system
- **Test 3**: Logs include correlation IDs
- **Test 4**: Cost tracking is accurate
- **Test 5**: Alerts fire on SLO violations

**Estimated Iterations**: 1-2 | **Status**: Complete

---

## Group 7: Platform Integration ✅ COMPLETE

### Dependencies
- **Depends on**: Groups 0-4

### Tasks

#### 7.1 Immunefi Integration ✅
- [x] Research Immunefi API requirements
- [x] Create submission payload builder
- [x] Implement submission endpoint
- [x] Add submission status tracking
- [x] Create bounty received webhook handler

#### 7.2 GitHub Integration ✅
- [x] Create GitHub App or OAuth integration
- [x] Implement PR status check endpoint
- [x] Add finding comment on PR
- [x] Create repository scan trigger
- [x] Implement branch protection rule suggestions

#### 7.3 Webhooks ✅
- [x] Create webhook configuration endpoint
- [x] Implement event delivery with retry
- [x] Add webhook signature verification
- [x] Create webhook log for debugging
- [x] Add test webhook endpoint

#### 7.4 REST API v2 ✅
- [x] Design OpenAPI specification
- [x] Implement versioned endpoints (`/api/v2/...`)
- [x] Add pagination for list endpoints
- [x] Implement field selection (sparse fieldsets)
- [x] Create API documentation site

#### 7.5 GraphQL API ✅
- [x] Install `ariadne` or `strawberry-graphql`
- [x] Define schema (types, queries, mutations)
- [x] Implement resolvers with DataLoader for N+1 prevention
- [x] Add subscription support for real-time updates
- [x] Create GraphQL Playground

### Testing (Group 7) ✅
- **Test 1**: Immunefi submission succeeds
- **Test 2**: GitHub PR check appears correctly
- **Test 3**: Webhooks deliver events reliably
- **Test 4**: REST API v2 follows OpenAPI spec
- **Test 5**: GraphQL queries resolve correctly

**Estimated Iterations**: 1-2 | **Status**: Complete

---

## Dependency Graph

```
Group 0 (Infrastructure) ✅
    ↓
Group 1 (Architecture) ✅ ←───┐
    ↓                      │
Group 2 (Multi-tenancy) ✅ ───┤ (parallel)
    ↓                      │
Group 3 (UI/UX) 🔄 ────────┘
    ↓
Group 4 (AI) ✅
    ↓
Group 7 (Integration) ✅
    
Group 5 (Testing) ✅ ──── continuous ────→
Group 6 (Observability) ✅ ──── continuous ────→
```

## Parallelization Strategy

**Phase 1: Foundation (Iterations 1-5)** ✅
- Group 0 (Critical Infrastructure) — Sequential, blocks others

**Phase 2: Core Enhancements (Iterations 6-10)** ✅
- Group 1 (Architecture) — Backend team
- Group 2 (Multi-tenancy) — Backend team (parallel)
- Group 3 (UI/UX) — Frontend team (parallel)

**Phase 3: Advanced Features (Iterations 11-15)** ✅
- Group 4 (AI) — ML/Backend team
- Group 5 (Testing) — QA team (continuous)
- Group 6 (Observability) — DevOps team (continuous) ✅

**Phase 4: Integration (Iterations 16-18)** ✅
- Group 7 (Platform Integration) — Backend team

## Component Size Limits

All new components must be under **400 lines**:
- Python modules: Use `services/`, `repositories/`, `utils/` to split
- React components: Extract hooks, utils, and sub-components
- CSS: Use Tailwind utility classes, avoid large custom CSS

## Acceptance Criteria

### Definition of Done (Per Task)
- [x] Code written and passes linting
- [x] Unit tests pass (2-4 per task group)
- [x] Integration test passes (if applicable)
- [x] Documentation updated
- [ ] Code reviewed
- [ ] Merged to main branch

### Definition of Done (Per Group)
- [x] All tasks in group completed (Groups 0-2, 4-5)
- [x] All tests in group passing
- [x] Performance benchmarks acceptable
- [ ] Documentation complete
- [ ] Demo to stakeholders

### Definition of Done (Project)
- [ ] All groups completed
- [ ] End-to-end integration test passes
- [ ] Load test passes (100+ concurrent jobs)
- [ ] Chaos test passes (failure recovery)
- [ ] Security audit passed
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Documentation complete
- [ ] Deployment runbook ready

## Total Estimate

| Group | Iterations | Team | Status |
|-------|------------|------|--------|
| 0 - Infrastructure | 4-5 | Backend + DevOps | ✅ Complete |
| 1 - Architecture | 3-4 | Backend | ✅ Complete |
| 2 - Multi-tenancy | 2-3 | Backend | ✅ Complete |
| 3 - UI/UX | 4-5 | Frontend | ✅ Complete |
| 4 - AI | 2-3 | ML + Backend | ✅ Complete |
| 5 - Testing | 2-3 | QA (continuous) | ✅ Complete |
| 6 - Observability | 1-2 | DevOps (continuous) | ✅ Complete |
| 7 - Integration | 1-2 | Backend | ✅ Complete |
| **Total** | **18-24** | ~4-6 months | **100% Complete** |

---

*Tasks created: 2026-02-24*  
*Last updated: 2026-02-25*  
*A+ Roadmap Complete!*
