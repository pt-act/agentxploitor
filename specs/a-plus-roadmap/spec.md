# AgentxploiTor A+ Roadmap - Specification

## Goal

Transform AgentxploiTor from production-viable (B+) to enterprise-grade (A+) by implementing distributed system primitives, proper storage abstraction, innovative UI/UX with real-time AI reasoning visualization, and multi-tenant architecture while maintaining consciousness-driven design principles.

## User Stories

1. **Enterprise Security Team Lead** — Collaborate on audits with team workspace, RBAC, and unified analytics dashboard.

2. **Protocol Developer** — Watch real-time analysis progress, see AI reasoning stream, interact with preliminary findings before final report.

3. **Security Researcher** — Leverage AI-augmented exploit suggestions, attack path visualization, and safe PoC generation with human-in-the-loop.

4. **Platform Operator** — Scale with distributed workers, automatic failover, real-time observability, and cost optimization.

## Requirements

### Critical Infrastructure
- Redis distributed queue with atomic operations
- Circuit breaker for all external calls (analyzers, LLM, RPC)
- Outbox pattern for reliable state transitions
- PostgreSQL with schema migrations
- Health check endpoints with dependency status

### Architectural Improvements
- Event sourcing for audit trail (immutable event log)
- CQRS for read/write separation
- Domain events (JobCreated, PaymentVerified, ScanCompleted, ExploitGenerated)
- Saga orchestration for distributed transactions
- Aggregate boundaries with consistency enforcement

### Multi-Tenancy & Security
- Workspace isolation (database-level tenant separation)
- RBAC with roles: Admin, Analyst, Viewer, API
- API key management with scoped permissions
- Immutable audit log with cryptographic integrity
- Session recovery for interrupted audits

### UI/UX Innovation
- **Real-time reasoning stream** — Agent thinking visualization with toggleable detail levels
- **Attack path graph** — Interactive D3.js visualization showing contract relationships and exploit flow
- **Collaborative annotations** — Comments, assignments, and status on each finding
- **Focus-first dashboard** — Ambient status, no interruptions, progressive disclosure
- **Finding cards** — Compact by default, expand for full context with AI fix suggestions
- **Mobile-responsive** — Full functionality on tablet, view-only on mobile
- **Accessibility** — WCAG 2.1 AA compliance

### AI Augmentation
- Fine-tuned exploit generation model (or RAG with constraints)
- Semantic safety analysis (beyond keyword matching)
- Confidence calibration from historical accuracy
- Explainable AI with reasoning traces
- Human approval required for high-impact actions

### Testing & Quality
- Integration tests for full pipeline (10+ scenarios)
- Concurrency stress tests (100+ concurrent jobs)
- Error path coverage >95% branches
- Performance benchmarks (latency, throughput, cost)
- Chaos tests (network partitions, node failures)

### Observability
- Prometheus metrics (job latency, queue depth, error rates)
- OpenTelemetry distributed tracing
- Structured JSON logging with correlation IDs
- Cost tracking per audit (compute, storage, API)
- SLO dashboards with alerting

### Platform Integration
- Immunefi automated bounty submission
- GitHub PR status checks
- Webhooks for audit events
- REST API v2 with OpenAPI spec
- GraphQL for flexible queries

## Visual Design

### Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│  Workspace Selector │ Team │ Activity │ Settings    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────┐  ┌───────────────────────┐ │
│  │   Active Audits     │  │   AI Reasoning Stream  │ │
│  │   (ambient cards)   │  │   (scrolling log)      │ │
│  │                     │  │                        │ │
│  │   [●●●○○] 3/5      │  │   ⟳ Analyzing...       │ │
│  │                     │  │   ✓ Found: Reentrancy  │ │
│  │   Card 1  Card 2   │  │   ⟳ Generating exploit │ │
│  │   Card 3  Card 4   │  │   ...                  │ │
│  └─────────────────────┘  └───────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │   Attack Path Visualization (expandable)        │ │
│  │   [Contract A] → [Function B] → [Vulnerability] │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Finding Card Design
```
┌─────────────────────────────────────────────────────┐
│ CRITICAL  Reentrancy in withdraw()         [>] [×] │
├─────────────────────────────────────────────────────┤
│ CVSS 9.5  Confidence 92%  Analyzer: Slither        │
│                                                       │
│ External call before state update enables...        │
│                                                       │
│ ┌─ AI Suggestion ────────────────────────────────┐ │
│ │ Add ReentrancyGuard or use check-effects-interactions │
│ │ pattern. Estimated fix complexity: LOW           │ │
│ └─────────────────────────────────────────────────┘ │
│                                                       │
│ [💬 3 comments]  [👤 Assign]  [✓ Mark Fixed]        │
└─────────────────────────────────────────────────────┘
```

## Existing Code to Leverage

| Component | Current State | Enhancement |
|-----------|--------------|-------------|
| `AnalyzerAdapter` | Clean abstraction | Add caching, parallel execution |
| `PerceptionProvider` | DI pattern | Add connection pooling |
| `JobSession` state machine | Valid transitions | Wrap with event sourcing |
| `Exploit.validate_safety()` | Keyword check | Add semantic analysis |
| Payment verification | BNKR on Base | Keep, add multi-token support |
| API routes | Functional | Add rate limiting, auth middleware |

## Out of Scope

- Full multi-tenant SaaS billing (usage-based pricing)
- Automated CI/CD integration (beyond GitHub PR checks)
- Real-time collaborative editing (like Google Docs)
- Mobile native apps (responsive web only)
- ML model training infrastructure (use external APIs initially)
- Active-active multi-region deployment (start with single-region)
- Blockchain smart contract upgrades monitoring
- Automated exploit execution on mainnet (safety constraint)

## Dependencies

### Infrastructure Dependencies
```
Redis Cluster (queue) → PostgreSQL (state) → Workers (compute)
                                ↓
                    S3-compatible storage (artifacts)
```

### Development Dependencies
```
Group 0 (Infrastructure) → Group 1 (Architecture) → Group 3 (Multi-tenancy)
                                                   ↘
                                                     Group 4 (UI/UX)
                                                   ↗
                         Group 2 (Testing) ← Group 5 (AI)
                         
Group 6 (Observability) — parallel with all groups
Group 7 (Integration) — depends on Groups 0-4
```

## Acceptance Criteria

### Must Have (MVP)
- [ ] Distributed queue with Redis
- [ ] PostgreSQL with migrations
- [ ] Circuit breaker for external calls
- [ ] Workspace and RBAC
- [ ] Real-time reasoning stream
- [ ] Finding card with AI suggestions
- [ ] Health check endpoint
- [ ] Integration tests for pipeline

### Should Have (Enhanced)
- [ ] Attack path visualization
- [ ] Collaborative annotations
- [ ] Event sourcing audit trail
- [ ] Distributed tracing
- [ ] Cost tracking

### Nice to Have (Future)
- [ ] Immunefi integration
- [ ] GraphQL API
- [ ] Chaos tests
- [ ] Fine-tuned LLM

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Redis SPOF | Redis Cluster or Sentinel from day 1 |
| Migration complexity | Dual-write during migration, feature flags |
| LLM cost | Aggressive caching, rate limiting, smaller model |
| UI overwhelm | User testing, progressive disclosure, tutorials |
| Distributed debugging | Tracing from start, structured logging |

## Estimated Iterations

| Group | Iterations | Notes |
|-------|------------|-------|
| Critical Infrastructure | 4-5 | Foundation, limited parallelization |
| Architectural Improvements | 3-4 | After infrastructure |
| Multi-Tenancy | 2-3 | Independent of UI |
| UI/UX Innovation | 4-5 | Parallel with backend work |
| AI Augmentation | 2-3 | After backend stable |
| Testing | 2-3 | Continuous throughout |
| Observability | 1-2 | Continuous throughout |
| Integration | 1-2 | Late stage |
| **Total** | **18-24** | ~4-6 months |

---

*Consciousness Gate 1: PASSED*  
*Gate 1 Questions:*
- ✅ Enhances human capability (AI augments, doesn't replace)
- ✅ Fosters contemplation (focus-first design, glass-box transparency)
- ✅ System is transparent (real-time reasoning, explainable AI)

*Ready for task breakdown*
