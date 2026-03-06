"""
GraphQL API Schema and Implementation

Provides a flexible GraphQL API for querying and mutating
Agentxploitor data with real-time subscriptions.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


GRAPHQL_SCHEMA = '''
"""Agentxploitor GraphQL API Schema"""

scalar DateTime
scalar JSON
scalar UUID

type Query {
    """Workspace queries"""
    workspace(id: ID!): Workspace
    workspaces(limit: Int, offset: Int, orderBy: String): WorkspaceConnection!
    
    """Job queries"""
    job(id: ID!): Job
    jobs(workspaceId: ID, status: JobStatus, priority: Priority, limit: Int, offset: Int): JobConnection!
    jobByTarget(targetUrl: String!): Job
    
    """Finding queries"""
    finding(id: ID!): Finding
    findings(jobId: ID!, severity: Severity, status: FindingStatus, limit: Int, offset: Int): FindingConnection!
    findingCounts(jobId: ID!): FindingCounts!
    
    """Report queries"""
    report(jobId: ID!): Report
    
    """Metrics queries"""
    metrics(workspaceId: ID!, startDate: DateTime, endDate: DateTime): Metrics!
    costs(workspaceId: ID!, startDate: DateTime, endDate: DateTime): CostSummary!
    
    """User queries"""
    me: User
    users(workspaceId: ID!): [User!]!
}

type Mutation {
    """Job mutations"""
    createJob(input: CreateJobInput!): Job!
    cancelJob(id: ID!): Job!
    recoverJob(id: ID!): Job!
    
    """Finding mutations"""
    updateFinding(id: ID!, input: UpdateFindingInput!): Finding!
    addComment(findingId: ID!, content: String!): Comment!
    
    """Webhook mutations"""
    createWebhook(input: CreateWebhookInput!): Webhook!
    updateWebhook(id: ID!, input: UpdateWebhookInput!): Webhook!
    deleteWebhook(id: ID!): Boolean!
    testWebhook(id: ID!): WebhookDelivery!
    
    """User mutations"""
    updateUser(id: ID!, input: UpdateUserInput!): User!
}

type Subscription {
    """Real-time job updates"""
    jobUpdated(id: ID!): JobEvent!
    jobCompleted(id: ID!): Job!
    
    """Real-time finding updates"""
    findingDiscovered(jobId: ID!): Finding!
    
    """Real-time reasoning stream"""
    reasoningStream(auditId: ID!): ReasoningEvent!
}

"""Workspace type"""
type Workspace {
    id: ID!
    name: String!
    slug: String!
    createdAt: DateTime!
    settings: JSON
    users: [User!]!
    jobs: [Job!]!
    jobCount: Int!
}

type WorkspaceConnection {
    edges: [WorkspaceEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type WorkspaceEdge {
    node: Workspace!
    cursor: String!
}

"""Job types"""
type Job {
    id: ID!
    targetUrl: String!
    contractAddress: String
    scope: String
    status: JobStatus!
    priority: Priority!
    workspace: Workspace!
    createdBy: User
    createdAt: DateTime!
    updatedAt: DateTime!
    startedAt: DateTime
    completedAt: DateTime
    findings: [Finding!]!
    findingsCount: Int!
    report: Report
    error: String
}

enum JobStatus {
    PENDING_PAYMENT
    PAYMENT_VERIFIED
    QUEUED
    IN_PROGRESS
    COMPLETED
    FAILED
    CANCELLED
}

enum Priority {
    LOW
    NORMAL
    HIGH
    CRITICAL
}

type JobConnection {
    edges: [JobEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type JobEdge {
    node: Job!
    cursor: String!
}

type JobEvent {
    job: Job!
    eventType: String!
    timestamp: DateTime!
}

"""Finding types"""
type Finding {
    id: ID!
    job: Job!
    title: String!
    description: String!
    severity: Severity!
    cvssScore: Float
    confidence: Float
    location: String
    exploitScenario: String
    expectedOutcome: String
    analyzer: String
    status: FindingStatus!
    assignedTo: User
    comments: [Comment!]!
    createdAt: DateTime!
    updatedAt: DateTime!
}

enum Severity {
    CRITICAL
    HIGH
    MEDIUM
    LOW
    INFO
}

enum FindingStatus {
    OPEN
    ACKNOWLEDGED
    FIXED
    WONT_FIX
    FALSE_POSITIVE
}

type FindingConnection {
    edges: [FindingEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type FindingEdge {
    node: Finding!
    cursor: String!
}

type FindingCounts {
    total: Int!
    critical: Int!
    high: Int!
    medium: Int!
    low: Int!
    info: Int!
}

"""Comment type"""
type Comment {
    id: ID!
    finding: Finding!
    author: User!
    content: String!
    createdAt: DateTime!
    updatedAt: DateTime
}

"""Report type"""
type Report {
    id: ID!
    job: Job!
    format: ReportFormat!
    url: String
    content: JSON
    generatedAt: DateTime!
}

enum ReportFormat {
    JSON
    PDF
    HTML
    MARKDOWN
}

"""User type"""
type User {
    id: ID!
    displayName: String!
    email: String
    role: UserRole!
    workspace: Workspace!
    createdAt: DateTime!
    lastActiveAt: DateTime
}

enum UserRole {
    ADMIN
    ANALYST
    VIEWER
    API
}

"""Webhook types"""
type Webhook {
    id: ID!
    url: String!
    events: [String!]!
    active: Boolean!
    createdAt: DateTime!
    lastTriggeredAt: DateTime
    deliveryStats: WebhookStats
}

type WebhookStats {
    totalDeliveries: Int!
    successfulDeliveries: Int!
    failedDeliveries: Int!
    successRate: Float!
}

type WebhookDelivery {
    id: ID!
    webhook: Webhook!
    event: String!
    status: DeliveryStatus!
    attempts: Int!
    responseCode: Int
    error: String
    createdAt: DateTime!
    completedAt: DateTime
}

enum DeliveryStatus {
    PENDING
    SENDING
    SUCCESS
    FAILED
    EXPIRED
}

"""Metrics types"""
type Metrics {
    jobs: JobMetrics!
    findings: FindingMetrics!
    performance: PerformanceMetrics!
    period: MetricsPeriod!
}

type JobMetrics {
    total: Int!
    completed: Int!
    failed: Int!
    avgDuration: Float!
}

type FindingMetrics {
    total: Int!
    bySeverity: FindingCounts!
    avgPerJob: Float!
}

type PerformanceMetrics {
    avgLatency: Float!
    p50Latency: Float!
    p95Latency: Float!
    p99Latency: Float!
    throughput: Float!
}

type MetricsPeriod {
    startDate: DateTime!
    endDate: DateTime!
}

"""Cost types"""
type CostSummary {
    total: Float!
    compute: Float!
    storage: Float!
    apiCalls: Float!
    llmTokens: Float!
    byJob: [JobCost!]!
    period: MetricsPeriod!
}

type JobCost {
    jobId: ID!
    job: Job
    amount: Float!
}

"""Reasoning stream types"""
type ReasoningEvent {
    id: ID!
    auditId: ID!
    type: ReasoningEventType!
    content: String!
    timestamp: DateTime!
    metadata: JSON
}

enum ReasoningEventType {
    THOUGHT
    ACTION
    OBSERVATION
    DECISION
    ERROR
}

"""Pagination"""
type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}

"""Input types"""
input CreateJobInput {
    targetUrl: String!
    contractAddress: String
    scope: String
    priority: Priority
    workspaceId: ID!
}

input UpdateFindingInput {
    status: FindingStatus
    assignedTo: ID
}

input CreateWebhookInput {
    url: String!
    events: [String!]!
    secret: String
    active: Boolean
}

input UpdateWebhookInput {
    url: String
    events: [String!]
    secret: String
    active: Boolean
}

input UpdateUserInput {
    displayName: String
    email: String
}

"""Directives"""
directive @auth(requires: UserRole = ADMIN) on FIELD_DEFINITION
directive @skip(if: Boolean!) on FIELD_DEFINITION
directive @include(if: Boolean!) on FIELD_DEFINITION
'''


class GraphQLContext:
    """Context for GraphQL resolvers."""

    def __init__(self, user=None, workspace=None):
        self.user = user
        self.workspace = workspace


RESOLVERS = {
    "Query": {
        "workspace": lambda self, info, id: None,
        "workspaces": lambda self, info, **kwargs: {"edges": [], "pageInfo": {}},
        "job": lambda self, info, id: None,
        "jobs": lambda self, info, **kwargs: {"edges": [], "pageInfo": {}},
        "jobByTarget": lambda self, info, targetUrl: None,
        "finding": lambda self, info, id: None,
        "findings": lambda self, info, **kwargs: {"edges": [], "pageInfo": {}},
        "findingCounts": lambda self, info, jobId: {},
        "report": lambda self, info, jobId: None,
        "metrics": lambda self, info, **kwargs: {},
        "costs": lambda self, info, **kwargs: {},
        "me": lambda self, info: None,
        "users": lambda self, info, workspaceId: [],
    },
    "Mutation": {
        "createJob": lambda self, info, input: {},
        "cancelJob": lambda self, info, id: {},
        "recoverJob": lambda self, info, id: {},
        "updateFinding": lambda self, info, id, input: {},
        "addComment": lambda self, info, findingId, content: {},
        "createWebhook": lambda self, info, input: {},
        "updateWebhook": lambda self, info, id, input: {},
        "deleteWebhook": lambda self, info, id: False,
        "testWebhook": lambda self, info, id: {},
        "updateUser": lambda self, info, id, input: {},
    },
    "Subscription": {
        "jobUpdated": lambda self, info, id: None,
        "jobCompleted": lambda self, info, id: None,
        "findingDiscovered": lambda self, info, jobId: None,
        "reasoningStream": lambda self, info, auditId: None,
    },
}


def create_graphql_router():
    """Create GraphQL router configuration."""
    return {
        "schema": GRAPHQL_SCHEMA,
        "resolvers": RESOLVERS,
        "context": GraphQLContext,
    }
