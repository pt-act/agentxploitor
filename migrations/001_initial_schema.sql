-- Migration: 001_initial_schema
-- Description: Initial schema for AgentxploiTor enterprise features
-- Created: 2026-02-24

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for hashing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

--------------------------------------------------------------------------------
-- WORKSPACES
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_by UUID,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_workspaces_slug ON workspaces(slug);
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at DESC);

--------------------------------------------------------------------------------
-- USERS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    external_id VARCHAR(255),  -- Farcaster FID or other auth ID
    email VARCHAR(255),
    display_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    settings JSONB DEFAULT '{}',
    api_key_hash VARCHAR(255),
    api_key_scopes JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'analyst', 'viewer', 'api'))
);

CREATE INDEX idx_users_workspace ON users(workspace_id);
CREATE INDEX idx_users_external_id ON users(external_id);
CREATE INDEX idx_users_api_key ON users(api_key_hash) WHERE api_key_hash IS NOT NULL;

--------------------------------------------------------------------------------
-- JOBS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(100) PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    target_url TEXT NOT NULL,
    contract_address VARCHAR(100),
    scope TEXT,
    priority VARCHAR(20) DEFAULT 'normal',
    
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    version INTEGER DEFAULT 1,
    
    wallet_address VARCHAR(100),
    payment_tx_hash VARCHAR(100),
    payment_amount VARCHAR(100),
    payment_verified BOOLEAN DEFAULT FALSE,
    
    findings_count JSONB DEFAULT '{}',
    report_path TEXT,
    error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT valid_status CHECK (
        status IN ('pending_payment', 'payment_verified', 'queued', 
                   'in_progress', 'completed', 'failed', 'cancelled')
    ),
    CONSTRAINT valid_priority CHECK (
        priority IN ('low', 'normal', 'high', 'critical')
    )
);

CREATE INDEX idx_jobs_workspace ON jobs(workspace_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_wallet ON jobs(wallet_address);

--------------------------------------------------------------------------------
-- JOB STATE HISTORY
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS job_state_history (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100) REFERENCES jobs(id) ON DELETE CASCADE,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    reason TEXT,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_history_status CHECK (
        to_status IN ('pending_payment', 'payment_verified', 'queued',
                      'in_progress', 'completed', 'failed', 'cancelled')
    )
);

CREATE INDEX idx_job_history_job ON job_state_history(job_id);
CREATE INDEX idx_job_history_created ON job_state_history(created_at DESC);

--------------------------------------------------------------------------------
-- EVENTS (Event Sourcing)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_version INTEGER DEFAULT 1,
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    causation_id VARCHAR(100),
    correlation_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_event_position UNIQUE (aggregate_type, aggregate_id, id)
);

CREATE INDEX idx_events_aggregate ON events(aggregate_type, aggregate_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_created ON events(created_at DESC);
CREATE INDEX idx_events_correlation ON events(correlation_id);

--------------------------------------------------------------------------------
-- OUTBOX
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS outbox (
    id BIGSERIAL PRIMARY KEY,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    destination VARCHAR(100) DEFAULT 'default',
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT max_retries CHECK (retry_count < 10)
);

CREATE INDEX idx_outbox_unpublished ON outbox(created_at) 
    WHERE published = FALSE;
CREATE INDEX idx_outbox_aggregate ON outbox(aggregate_type, aggregate_id);

--------------------------------------------------------------------------------
-- FINDINGS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS findings (
    id VARCHAR(100) PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL,
    cvss_score DECIMAL(3,1),
    location TEXT,
    exploit_scenario TEXT,
    expected_outcome TEXT,
    target_url TEXT,
    analyzer VARCHAR(100),
    confidence DECIMAL(3,2) DEFAULT 1.0,
    
    status VARCHAR(50) DEFAULT 'open',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_finding_severity CHECK (
        severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')
    ),
    CONSTRAINT valid_finding_status CHECK (
        status IN ('open', 'acknowledged', 'fixed', 'wont_fix', 'false_positive')
    )
);

CREATE INDEX idx_findings_job ON findings(job_id);
CREATE INDEX idx_findings_workspace ON findings(workspace_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_status ON findings(status);

--------------------------------------------------------------------------------
-- FINDING COMMENTS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS finding_comments (
    id BIGSERIAL PRIMARY KEY,
    finding_id VARCHAR(100) REFERENCES findings(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_comments_finding ON finding_comments(finding_id);
CREATE INDEX idx_comments_created ON finding_comments(created_at DESC);

--------------------------------------------------------------------------------
-- EXPLOITS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exploits (
    id BIGSERIAL PRIMARY KEY,
    finding_id VARCHAR(100) REFERENCES findings(id) ON DELETE CASCADE,
    technique VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    steps JSONB DEFAULT '[]',
    success_indicators JSONB DEFAULT '[]',
    safety_constraints JSONB DEFAULT '[]',
    
    execution_status VARCHAR(50) DEFAULT 'pending',
    execution_result JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_exploit_status CHECK (
        execution_status IN ('pending', 'running', 'success', 'failed', 'skipped')
    )
);

CREATE INDEX idx_exploits_finding ON exploits(finding_id);

--------------------------------------------------------------------------------
-- VERIFICATIONS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS verifications (
    id BIGSERIAL PRIMARY KEY,
    finding_id VARCHAR(100) REFERENCES findings(id) ON DELETE CASCADE,
    exploit_id BIGINT REFERENCES exploits(id) ON DELETE CASCADE,
    
    success BOOLEAN NOT NULL,
    visual_diff DECIMAL(5,2),
    proof_path TEXT,
    evidence JSONB DEFAULT '[]',
    reason TEXT,
    
    before_url TEXT,
    after_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_verifications_finding ON verifications(finding_id);

--------------------------------------------------------------------------------
-- ARTIFACTS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS artifacts (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100) REFERENCES jobs(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    size_bytes BIGINT,
    content_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    CONSTRAINT valid_artifact_type CHECK (
        type IN ('report', 'screenshot', 'diff', 'proof', 'log', 'other')
    )
);

CREATE INDEX idx_artifacts_job ON artifacts(job_id);
CREATE INDEX idx_artifacts_expires ON artifacts(expires_at) WHERE expires_at IS NOT NULL;

--------------------------------------------------------------------------------
-- AUDIT LOG
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    
    old_value JSONB,
    new_value JSONB,
    
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    prev_hash VARCHAR(64),
    hash VARCHAR(64) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_workspace ON audit_log(workspace_id);
CREATE INDEX idx_audit_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- Function to compute hash chain
CREATE OR REPLACE FUNCTION compute_audit_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.hash := encode(
        sha256(
            (COALESCE(NEW.prev_hash, '') || 
             NEW.action || 
             NEW.resource_type || 
             COALESCE(NEW.resource_id, '') ||
             COALESCE(NEW.old_value::text, '') ||
             COALESCE(NEW.new_value::text, '') ||
             NEW.created_at::text
            )::bytea
        ),
        'hex'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_hash_trigger
    BEFORE INSERT ON audit_log
    FOR EACH ROW
    EXECUTE FUNCTION compute_audit_hash();

--------------------------------------------------------------------------------
-- MIGRATIONS TRACKING
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO schema_migrations (version) VALUES ('001_initial_schema');
