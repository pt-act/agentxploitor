"""
Group 0 Tests — SimpleMem + Code-Voyager Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tests: 4 targeted tests covering critical integration points.
Fast feedback. No external dependencies required (all mocked).

Run: pytest src/tests/test_memory.py -v
"""

from __future__ import annotations

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from memory.audit_memory import AuditMemoryRecord, AuditMemoryStore, Finding
from memory.project_profile import ProjectProfile, ProjectProfileStore
from memory.session_hooks import AuditSessionManager, SessionContext


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_store(tmp_path):
    """AuditMemoryStore backed by temp directory — no SimpleMem dependency."""
    return AuditMemoryStore(storage_dir=str(tmp_path / "audit_memory"))


@pytest.fixture
def tmp_profile_store(tmp_path):
    """ProjectProfileStore backed by temp directory — no Code-Voyager dependency."""
    return ProjectProfileStore(storage_dir=str(tmp_path / "project_profiles"))


@pytest.fixture
def sample_record():
    """A realistic completed audit record."""
    record = AuditMemoryRecord(
        target_type="contract_evm",
        target_value="0xabcdef1234567890abcdef1234567890abcdef12",
        chain="base",
        requested_by_fid=12345,
        audit_type="contract_deep",
        tools_used=["slither", "mythril"],
        agents_used=["CVEIntelligenceManager", "VulnerabilityCorrelator"],
        skill_ids_applied=["skill_reentrancy_001"],
        findings=[
            Finding(
                severity="critical",
                category="reentrancy",
                title="Reentrancy in withdraw()",
                description="Classic reentrancy vulnerability in withdraw function.",
                location="contracts/Vault.sol:142",
                confidence=0.96,
                fix_recommendation="Add ReentrancyGuard modifier.",
            ),
            Finding(
                severity="medium",
                category="access_control",
                title="Missing access control on setFee()",
                location="contracts/Vault.sol:89",
                confidence=0.82,
                fix_recommendation="Add onlyOwner modifier.",
            ),
        ],
        bytecode_hash="abc123hash",
        source_hash="src456hash",
        source_available=True,
        transcript_summary="Found reentrancy and access control issues.",
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    record.target_id = AuditMemoryRecord.make_target_id(
        record.target_type, record.target_value, record.chain
    )
    return record


# ── T0.1: AuditMemoryRecord stored correctly after completed audit ────────────

def test_audit_memory_record_stored_and_retrieved(tmp_store, sample_record):
    """
    T0.1: AuditMemoryRecord stored correctly after completed audit.
    Verifies: store() persists to disk, get_history() retrieves correctly.
    """
    # Store the record
    tmp_store.store(sample_record)

    # Retrieve history for this target
    history = tmp_store.get_history(sample_record.target_id)

    assert len(history) == 1
    retrieved = history[0]

    assert retrieved.audit_id == sample_record.audit_id
    assert retrieved.target_value == sample_record.target_value
    assert retrieved.target_type == "contract_evm"
    assert retrieved.chain == "base"
    assert retrieved.overall_severity == "critical"  # derived from findings
    assert len(retrieved.findings) == 2
    assert retrieved.findings[0].severity == "critical"
    assert retrieved.findings[0].title == "Reentrancy in withdraw()"
    assert retrieved.requested_by_fid == 12345
    assert "independently requested" in retrieved.independence_declaration


# ── T0.2: Audit history retrieved correctly for known target ─────────────────

def test_audit_history_multiple_audits(tmp_store, sample_record):
    """
    T0.2: Audit history retrieved correctly — multiple audits, chronological order.
    Verifies: second audit appended, history ordered correctly.
    """
    # Store first audit
    tmp_store.store(sample_record)

    # Store second audit (same target, different version)
    second_record = AuditMemoryRecord(
        target_id=sample_record.target_id,
        target_type="contract_evm",
        target_value=sample_record.target_value,
        chain="base",
        requested_by_fid=12345,
        audit_type="contract_deep",
        findings=[],  # all fixed
        overall_severity="clean",
        bytecode_hash="newbytecode789",
        source_hash="newsrc789hash",
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    tmp_store.store(second_record)

    history = tmp_store.get_history(sample_record.target_id)

    assert len(history) == 2
    # First audit has findings, second is clean
    assert history[0].overall_severity == "critical"
    assert history[1].overall_severity == "clean"

    # Delta analysis
    delta = tmp_store.get_delta(
        sample_record.target_id,
        "abc123hash",   # hash_a (first audit)
        "newbytecode789"  # hash_b (second audit)
    )
    assert "new_findings" in delta
    assert "resolved_findings" in delta
    assert "persisting_findings" in delta
    # All findings from first audit resolved (empty second audit)
    assert len(delta["resolved_findings"]) == 2
    assert len(delta["new_findings"]) == 0


# ── T0.3: SessionStart correctly injects historical context ──────────────────

@pytest.mark.asyncio
async def test_session_start_injects_historical_context(tmp_store, tmp_profile_store, sample_record):
    """
    T0.3: SessionStart correctly injects historical context for returning target.
    Verifies: prior audit history appears in session context string.
    """
    # Pre-store an audit record so there's history
    tmp_store.store(sample_record)

    manager = AuditSessionManager(
        memory_store=tmp_store,
        profile_store=tmp_profile_store,
    )

    ctx = await manager.session_start(
        target_type="contract_evm",
        target_value=sample_record.target_value,
        chain="base",
        requested_by_fid=12345,
    )

    assert isinstance(ctx, SessionContext)
    assert ctx.prior_audit_count == 1
    assert ctx.target_id == sample_record.target_id
    assert "AGENTXPLOITOR SESSION CONTEXT" in ctx.full_context
    # Prior history must be in the injected context
    assert "Prior audits: 1" in ctx.full_context or "critical" in ctx.full_context
    # Session must be tracked
    assert ctx.session_id in manager._active_sessions


# ── T0.4: SessionEnd fires after audit and updates correctly ─────────────────

@pytest.mark.asyncio
async def test_session_end_stores_and_updates(tmp_store, tmp_profile_store, sample_record):
    """
    T0.4: SessionEnd fires after audit, stores record, updates profile.
    Verifies: record persisted, profile audit_count incremented.
    """
    manager = AuditSessionManager(
        memory_store=tmp_store,
        profile_store=tmp_profile_store,
    )

    # Start session
    ctx = await manager.session_start(
        target_type="contract_evm",
        target_value=sample_record.target_value,
        chain="base",
        requested_by_fid=12345,
    )

    # End session with the sample record
    sample_record.target_id = ctx.target_id
    await manager.session_end(
        session_id=ctx.session_id,
        audit_record=sample_record,
        transcript="Found reentrancy in withdraw(). Applied reentrancy skill. Confirmed exploit.",
    )

    # Record must be stored
    history = tmp_store.get_history(ctx.target_id)
    assert len(history) == 1
    assert history[0].audit_id == sample_record.audit_id

    # Session must be cleaned up
    assert ctx.session_id not in manager._active_sessions

    # Profile must be updated
    profile = tmp_profile_store.get_profile(ctx.target_id)
    assert profile.audit_count == 1
    assert profile.last_overall_severity == "critical"

    # Stats must reflect the audit
    stats = manager.get_stats()
    assert stats["total_audits"] >= 1
    assert stats["active_sessions"] == 0
