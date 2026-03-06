"""
AuditSessionManager — SessionStart/SessionEnd hooks for HexStrike
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wires SimpleMem + Code-Voyager into HexStrike's audit lifecycle.

SessionStart: loads audit history + project profile → injects context
SessionEnd:   stores findings → updates profile → fires Skill Factory

This is the bridge between HexStrike's stateless execution
and the persistent intelligence layer.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .audit_memory import AuditMemoryRecord, AuditMemoryStore, Finding
from .project_profile import ProjectProfile, ProjectProfileStore


@dataclass
class SessionContext:
    """
    Context object passed to HexStrike at SessionStart.
    Contains all historical knowledge needed to begin the audit.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str = ""
    target_value: str = ""
    target_type: str = ""
    chain: str | None = None

    # Historical context (injected into HexStrike system prompt)
    prior_audit_count: int = 0
    prior_findings_summary: str = ""
    project_profile_context: str = ""
    similar_targets_context: str = ""
    custom_skill_ids: list[str] = field(default_factory=list)

    # Full context string for injection
    full_context: str = ""

    def is_first_audit(self) -> bool:
        return self.prior_audit_count == 0


class AuditSessionManager:
    """
    Manages the full lifecycle of an audit session.

    Usage:
        manager = AuditSessionManager()

        # At audit start — load context for HexStrike
        ctx = await manager.session_start(target_id, target_value, target_type, chain)
        # → inject ctx.full_context into HexStrike system prompt

        # During audit — update findings as they stream in
        manager.add_finding(session_id, finding)

        # At audit completion — store everything, update brain
        await manager.session_end(session_id, transcript, audit_record)
    """

    def __init__(
        self,
        memory_store: AuditMemoryStore | None = None,
        profile_store: ProjectProfileStore | None = None,
    ):
        self._memory = memory_store or AuditMemoryStore()
        self._profiles = profile_store or ProjectProfileStore()
        self._active_sessions: dict[str, SessionContext] = {}

    # ── SessionStart ─────────────────────────────────────────────────────────

    async def session_start(
        self,
        target_type: str,
        target_value: str,
        chain: str | None,
        requested_by_fid: int = 0,
    ) -> SessionContext:
        """
        Load all historical context before HexStrike begins analysis.

        Called by the queue worker before dispatching to HexStrike.
        The returned context is injected into HexStrike's system prompt.
        """
        target_id = AuditMemoryRecord.make_target_id(target_type, target_value, chain)

        # Load in parallel: audit history + project profile + similar targets
        history, profile, similar = await asyncio.gather(
            asyncio.to_thread(self._memory.get_history, target_id),
            asyncio.to_thread(self._profiles.get_profile, target_id),
            asyncio.to_thread(
                self._memory.find_similar, target_type, target_value, 3
            ),
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        history = history if isinstance(history, list) else []
        profile = profile if isinstance(profile, ProjectProfile) else ProjectProfile(target_id=target_id)
        similar = similar if isinstance(similar, list) else []

        # Build context strings
        prior_findings_summary = self._format_history(history)
        similar_context = self._format_similar(similar, target_id)
        project_context = profile.to_session_context()
        custom_skills = self._profiles.get_custom_skills(target_id)

        full_context = self._build_full_context(
            target_value=target_value,
            target_type=target_type,
            chain=chain,
            prior_audit_count=len(history),
            prior_findings=prior_findings_summary,
            project_context=project_context,
            similar_context=similar_context,
            custom_skills=custom_skills,
        )

        ctx = SessionContext(
            target_id=target_id,
            target_value=target_value,
            target_type=target_type,
            chain=chain,
            prior_audit_count=len(history),
            prior_findings_summary=prior_findings_summary,
            project_profile_context=project_context,
            similar_targets_context=similar_context,
            custom_skill_ids=custom_skills,
            full_context=full_context,
        )

        self._active_sessions[ctx.session_id] = ctx
        return ctx

    # ── SessionEnd ───────────────────────────────────────────────────────────

    async def session_end(
        self,
        session_id: str,
        audit_record: AuditMemoryRecord,
        transcript: str = "",
    ) -> None:
        """
        Store findings and update intelligence layer after audit completes.

        Called by the queue worker after HexStrike returns results.
        Fires Code-Voyager Skill Factory autonomously — no human intervention.
        """
        # Mark completion time
        audit_record.completed_at = datetime.now(timezone.utc).isoformat()
        audit_record.target_id = AuditMemoryRecord.make_target_id(
            audit_record.target_type,
            audit_record.target_value,
            audit_record.chain,
        )

        # Store in SimpleMem
        await asyncio.to_thread(self._memory.store, audit_record)

        # Update Code-Voyager Brain + fire Skill Factory
        updated_profile = await asyncio.to_thread(
            self._profiles.update_profile,
            audit_record.target_id,
            transcript,
            audit_record,
        )

        # Record skill IDs back to audit record
        if updated_profile.custom_skill_ids:
            audit_record.new_skill_ids = updated_profile.custom_skill_ids

        # Clean up active session
        self._active_sessions.pop(session_id, None)

    # ── Utility ──────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """System-wide intelligence statistics for transparency display."""
        stats = self._memory.get_stats()
        stats["active_sessions"] = len(self._active_sessions)
        stats["code_voyager_available"] = self._profiles._brain is not None
        stats["simplemem_available"] = self._memory._simplemem is not None
        return stats

    # ── Private ──────────────────────────────────────────────────────────────

    def _format_history(self, history: list[AuditMemoryRecord]) -> str:
        if not history:
            return "No prior audits for this target."
        lines = [f"Prior audits: {len(history)}"]
        for r in history[-3:]:  # last 3 audits
            lines.append(
                f"  [{r.completed_at[:10] if r.completed_at else 'unknown'}] "
                f"Severity: {r.overall_severity} | "
                f"Findings: {len(r.findings)} | "
                f"Source hash: {r.source_hash or 'unavailable'}"
            )
        return "\n".join(lines)

    def _format_similar(
        self, similar: list[AuditMemoryRecord], exclude_target_id: str
    ) -> str:
        filtered = [r for r in similar if r.target_id != exclude_target_id]
        if not filtered:
            return ""
        lines = ["Similar targets previously audited:"]
        for r in filtered[:3]:
            lines.append(
                f"  {r.target_value} ({r.target_type}) — "
                f"severity: {r.overall_severity}, "
                f"{len(r.findings)} findings"
            )
        return "\n".join(lines)

    def _build_full_context(
        self,
        target_value: str,
        target_type: str,
        chain: str | None,
        prior_audit_count: int,
        prior_findings: str,
        project_context: str,
        similar_context: str,
        custom_skills: list[str],
    ) -> str:
        sections = [
            f"═══ AGENTXPLOITOR SESSION CONTEXT ═══",
            f"Target: {target_value}",
            f"Type: {target_type} | Chain: {chain or 'n/a'}",
            f"",
            project_context,
        ]
        if prior_audit_count > 0:
            sections += ["", "AUDIT HISTORY:", prior_findings]
        if similar_context:
            sections += ["", similar_context]
        if custom_skills:
            sections += [
                "",
                f"Project-specific skills available: {', '.join(custom_skills)}",
                "Apply these skills before running generic analysis.",
            ]
        sections.append("═══ BEGIN ANALYSIS ═══")
        return "\n".join(sections)
