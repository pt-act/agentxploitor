# AgentxploiTor A+ Roadmap - Requirements

## Feature Intent

Transform AgentxploiTor from a production-viable single-tenant platform (Grade B+) into an enterprise-grade, distributed security analysis platform (Grade A+) by addressing all findings from academic evaluation while introducing innovative UI/UX capabilities that leverage modern AI and visualization techniques.

## Consciousness Alignment

**Does this enhance human capability?**
✅ Yes — Empowers security researchers with AI-assisted analysis, visual proof generation, and collaborative auditing tools that amplify their effectiveness without replacing human judgment.

**Does it foster contemplation or create distraction?**
✅ Contemplative — Focus-first dashboard design, ambient status indicators, and glass-box transparency ensure users understand what the system is doing and why, fostering trust and learning.

**Is the system transparent (glass-box)?**
✅ Yes — Real-time reasoning visualization, explainable AI decisions, and full audit trails provide complete transparency into agent behavior.

## Problem Statement

The academic evaluation identified critical gaps preventing enterprise adoption:
1. **Distributed System Primitives** — No circuit breaker, saga orchestration, or outbox pattern
2. **Storage Abstraction** — Global variables and in-memory storage limit scalability
3. **Integration Testing** — Missing end-to-end pipeline coverage
4. **UI/UX Innovation** — Basic interface lacks modern collaborative and visualization features
5. **Multi-Tenancy** — No workspace isolation or RBAC

## User Stories

### Story 1: Enterprise Security Team Lead
> "As a security team lead, I want to onboard my entire team with role-based access control, assign audits to specific analysts, and track our collective progress on a unified dashboard so we can collaborate efficiently on security assessments."

**Acceptance Criteria:**
- Workspace creation with team invites
- Role assignment (Admin, Analyst, Viewer)
- Audit assignment and handoff workflows
- Team activity feed and analytics

### Story 2: Protocol Developer (Auditee)
> "As a protocol developer who commissioned an audit, I want real-time visibility into the analysis progress, see exactly what the AI is reasoning about, and interact with preliminary findings before the final report so I can prepare fixes proactively."

**Acceptance Criteria:**
- Live audit progress with reasoning stream
- Interactive finding cards with fix suggestions
- Comment thread on each finding
- Early warning alerts for critical issues

### Story 3: Security Researcher (Analyst)
> "As a security researcher, I want AI to augment my analysis by suggesting exploit strategies, visualizing attack paths, and auto-generating proof-of-concept code with safety guarantees so I can focus on high-value creative work."

**Acceptance Criteria:**
- AI-powered exploit suggestions
- Attack path visualization graph
- Safe PoC code generation with sandbox execution
- One-click report generation

### Story 4: Platform Operator
> "As a platform operator, I want distributed job processing with automatic failover, real-time observability, and cost optimization so I can scale the service reliably and economically."

**Acceptance Criteria:**
- Multi-node worker cluster with load balancing
- Health monitoring and alerting
- Cost tracking per audit
- Auto-scaling based on queue depth

## Core Requirements

### Group 0: Critical Infrastructure (Foundation)
- **REQ-001**: Redis-based distributed job queue with atomic operations
- **REQ-002**: Circuit breaker pattern for all external service calls
- **REQ-003**: Outbox pattern for reliable state changes
- **REQ-004**: PostgreSQL database with proper schema migrations
- **REQ-005**: Health check endpoints with dependency status

### Group 1: Architectural Improvements
- **REQ-006**: Event sourcing for audit trail (replaces mutable state)
- **REQ-007**: CQRS separation for reads/writes
- **REQ-008**: Domain events (JobCreated, PaymentVerified, ScanCompleted)
- **REQ-009**: Aggregate boundaries with consistency enforcement
- **REQ-010**: Saga orchestration for distributed transactions

### Group 2: Multi-Tenancy & Security
- **REQ-011**: Workspace isolation (logical/physical separation)
- **REQ-012**: Role-based access control (RBAC)
- **REQ-013**: API key management for integrations
- **REQ-014**: Audit log with immutable entries
- **REQ-015**: Session recovery for interrupted audits

### Group 3: UI/UX Innovation
- **REQ-016**: Real-time reasoning stream (agent thinking visualization)
- **REQ-017**: Attack path graph visualization (D3.js/Cytoscape)
- **REQ-018**: Collaborative finding annotations
- **REQ-019**: Focus-first dashboard (ambient status, no alerts)
- **REQ-020**: Progressive disclosure for complexity management
- **REQ-021**: Mobile-responsive design
- **REQ-022**: Dark/light theme with accessibility compliance

### Group 4: AI Augmentation
- **REQ-023**: Specialized LLM for exploit generation (fine-tuned)
- **REQ-024**: Constraint solving for safe payload generation
- **REQ-025**: Confidence calibration based on historical accuracy
- **REQ-026**: Explainable AI decisions (reasoning traces)
- **REQ-027**: Human-in-the-loop for critical decisions

### Group 5: Testing & Quality
- **REQ-028**: Integration tests for full pipeline (10+ scenarios)
- **REQ-029**: Concurrency stress tests for backpressure handling
- **REQ-030**: Error path coverage (>95% branches)
- **REQ-031**: Performance benchmarks (latency, throughput)
- **REQ-032**: Chaos engineering tests (failure injection)

### Group 6: Observability & Operations
- **REQ-033**: Prometheus metrics endpoint
- **REQ-034**: Distributed tracing (OpenTelemetry)
- **REQ-035**: Structured logging with context
- **REQ-036**: Cost tracking per audit (compute, storage, API calls)
- **REQ-037**: Alerting rules for SLO violations

### Group 7: Platform Integration
- **REQ-038**: Immunefi bounty submission automation
- **REQ-039**: GitHub PR integration (status checks)
- **REQ-040**: Webhook notifications for audit events
- **REQ-041**: REST API for external integrations
- **REQ-042**: GraphQL API for flexible queries

## Constraints

### Technical Constraints
- Must maintain backward compatibility with existing BNKR payment flow
- Python agent core must remain independently deployable
- Frontend must work without JavaScript (progressive enhancement)
- All external calls must have timeout and retry logic

### Business Constraints
- No breaking changes to existing audit workflow
- Migration path from in-memory to PostgreSQL must be smooth
- Cost per audit should not increase by more than 20%

### Security Constraints
- No secrets in logs (JWTs, API keys, wallet addresses)
- All user input must be validated and sanitized
- RBAC must enforce workspace isolation at database level
- Audit logs must be immutable and append-only

## Visual Design Inspiration

### Dashboard Concept
- **Focus-first design**: Single column layout, minimal chrome
- **Ambient indicators**: Subtle color shifts for status, no flashing alerts
- **Progressive disclosure**: Show overview by default, expand for details
- **Glass-box transparency**: Real-time reasoning stream visible

### Attack Path Visualization
- **Interactive graph**: Nodes are contracts/functions, edges are data flows
- **Risk highlighting**: Red/orange/yellow for severity levels
- **Animation**: Show exploit execution path step-by-step
- **Drill-down**: Click node to see code, findings, and fix suggestions

### Finding Cards
- **Compact by default**: Title, severity, one-line summary
- **Expand for details**: Full description, exploit scenario, fix guidance
- **Actions**: Comment, assign, mark as fixed, request re-scan
- **AI suggestions**: Auto-generated fix with confidence score

## Existing Code to Leverage

### Reusable Patterns (Keep)
- `AnalyzerAdapter` hierarchy — clean abstraction, add caching
- `PerceptionProvider` protocol — DI pattern, add pooling
- `JobSession` state machine — add event sourcing
- `VALID_TRANSITIONS` — add saga orchestration
- Safety validation in `Exploit.validate_safety()` — add semantic analysis

### Refactor Candidates
- Global state in `storage.ts` → Migrate to PostgreSQL
- In-memory queue in `worker.py` → Migrate to Redis
- Bare exception handling → Add structured error types
- Synchronous analyzers → Add async/parallel execution

### Deprecate
- `MockPerceptionProvider` for production (keep for testing)
- `MemoryJobStore` for production (keep for development)

## Dependencies

### External Services
- Redis 7.x for distributed queue
- PostgreSQL 15.x for persistent storage
- OpenTelemetry Collector for distributed tracing
- Prometheus for metrics scraping

### Libraries
- `redis-py` with asyncio support
- `asyncpg` for PostgreSQL
- `tenacity` for retry logic (or implement circuit breaker)
- `opentelemetry-*` packages for tracing
- D3.js or Cytoscape.js for graph visualization
- React Query for data fetching (replace polling)
- Framer Motion for animations

### Infrastructure
- Docker containers for workers
- Kubernetes for orchestration (or equivalent)
- S3-compatible storage for artifacts
- CDN for frontend assets

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Redis single point of failure | Medium | High | Use Redis Cluster or Sentinel |
| PostgreSQL migration complexity | Medium | Medium | Incremental migration with dual-write |
| LLM cost explosion | High | Medium | Caching, rate limiting, fine-tuned smaller model |
| UI complexity overwhelms users | Medium | High | User testing, progressive disclosure, tutorials |
| Distributed system debugging difficulty | High | High | Distributed tracing, structured logging, runbooks |

## Success Metrics

### Technical Metrics
- Pipeline latency P95 < 30 seconds for scan initiation
- Throughput > 100 audits/hour per worker node
- Availability > 99.9% (measured monthly)
- Test coverage > 85% (branch coverage)

### Business Metrics
- User satisfaction (NPS) > 50
- Time to first finding < 5 minutes
- Audit completion rate > 95%
- Repeat usage > 60% within 30 days

### Quality Metrics
- False positive rate < 15%
- False negative rate < 5% (measured by re-audits)
- Exploit proof success rate > 80%

## Timeline Estimate

**Total: 18-24 iterations** (estimated 4-6 months with parallel work)

| Phase | Iterations | Parallelization |
|-------|------------|-----------------|
| Critical Infrastructure | 4-5 | Limited (foundation) |
| Architectural Improvements | 3-4 | Medium (after infrastructure) |
| Multi-Tenancy & Security | 2-3 | High (independent of UI) |
| UI/UX Innovation | 4-5 | High (independent of backend) |
| AI Augmentation | 2-3 | Medium (after backend) |
| Testing & Quality | 2-3 | Continuous |
| Observability & Operations | 1-2 | Continuous |
| Platform Integration | 1-2 | Late stage |

## Open Questions

1. **Redis Cluster vs Redis Sentinel** — Which HA strategy for Redis?
2. **Fine-tuned LLM vs RAG** — Which approach for exploit generation?
3. **Graph database** — Should we use Neo4j for attack path visualization?
4. **Real-time transport** — WebSocket vs Server-Sent Events for reasoning stream?
5. **Multi-region deployment** — Active-active or active-passive for global availability?

## References

- Academic Evaluation Report (2026-02-24)
- AgentxploiTor Hardening Spec (original)
- Orion-OS Architecture Guide
- "Building Microservices" by Sam Newman (patterns reference)
- "Designing Data-Intensive Applications" by Martin Kleppmann (distributed systems)

---

*Requirements gathered: 2026-02-24*  
*Consciousness Gate 1: PASSED*  
*Ready for specification phase*
