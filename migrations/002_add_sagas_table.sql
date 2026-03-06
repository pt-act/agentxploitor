-- Migration: 002_add_sagas_table
-- Description: Add table for saga state persistence
-- Created: 2026-02-24

-- Sagas table for saga orchestration
CREATE TABLE IF NOT EXISTS sagas (
    id VARCHAR(100) PRIMARY KEY,
    saga_type VARCHAR(100) NOT NULL,
    correlation_id VARCHAR(100),
    state VARCHAR(50) NOT NULL DEFAULT 'pending',
    context JSONB DEFAULT '{}',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT valid_saga_state CHECK (
        state IN ('pending', 'running', 'completed', 'compensating', 'failed', 'compensated')
    )
);

CREATE INDEX idx_sagas_type ON sagas(saga_type);
CREATE INDEX idx_sagas_correlation ON sagas(correlation_id);
CREATE INDEX idx_sagas_state ON sagas(state);
CREATE INDEX idx_sagas_created ON sagas(created_at DESC);

INSERT INTO schema_migrations (version) VALUES ('002_add_sagas_table');
