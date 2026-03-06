"""
ProjectProfile — Per-subscriber project memory via Code-Voyager Brain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For monitoring subscribers: maintains accumulated knowledge about
each project across audit cycles.

On new audit: SessionStart injects this context.
On completion: SessionEnd updates it from transcript.
Code-Voyager Skill Factory mines transcript → writes new SKILL files.

This is what transforms a monitoring service into a dedicated
AI analyst that knows each project better with every audit.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Code-Voyager import — graceful fallback
try:
    sys.path.insert(0, str(Path(__file__).parents[4] / "hexstrike.aiV2-main" / "code-voyager" / "src"))
    from brain import VoyagerBrain          # type: ignore
    from skills import SkillFactory         # type: ignore
    CODE_VOYAGER_AVAILABLE = True
except ImportError:
    CODE_VOYAGER_AVAILABLE = False
    VoyagerBrain = None
    SkillFactory = None


# ─── Data Models ────────────────────────────────────────────────────────────

@dataclass
class ProjectProfile:
    """
    Accumulated knowledge about a specific monitored target.

    Built up over multiple audit cycles via Code-Voyager Brain.
    Injected at SessionStart of every new audit of this target.
    Updated at SessionEnd from the audit transcript.
    """
    target_id: str = ""
    target_value: str = ""
    target_type: str = ""

    # Accumulated knowledge (plain text — injected into agent context)
    brain_summary: str = ""            # Code-Voyager Brain narrative
    known_patterns: list[str] = field(default_factory=list)   # patterns specific to this target
    custom_skill_ids: list[str] = field(default_factory=list) # skill files created for this target
    audit_count: int = 0
    last_audited: str | None = None
    last_overall_severity: str = "clean"
    last_bytecode_hash: str | None = None
    last_source_hash: str | None = None

    # Watching state
    monitoring_enabled: bool = False
    subscriber_fid: int | None = None

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_session_context(self) -> str:
        """
        Format profile as context string injected at SessionStart.
        This is what the agent reads before beginning a new audit.
        """
        if self.audit_count == 0:
            return f"First audit of target {self.target_value}. No prior history."

        patterns_text = "\n".join(
            f"  - {p}" for p in self.known_patterns
        ) or "  None recorded yet."

        return (
            f"PRIOR AUDIT CONTEXT FOR: {self.target_value}\n"
            f"{'━' * 60}\n"
            f"Audit count: {self.audit_count}\n"
            f"Last audited: {self.last_audited}\n"
            f"Last severity: {self.last_overall_severity}\n"
            f"Last bytecode hash: {self.last_bytecode_hash or 'unknown'}\n\n"
            f"Accumulated knowledge:\n{self.brain_summary}\n\n"
            f"Known patterns for this target:\n{patterns_text}\n\n"
            f"Custom skills built for this target: "
            f"{', '.join(self.custom_skill_ids) or 'none yet'}\n"
            f"{'━' * 60}\n"
            f"FOCUS: What has changed since the last audit? "
            f"Apply known patterns first. Flag any new code paths."
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ProjectProfile":
        return cls(**d)


# ─── Storage Interface ───────────────────────────────────────────────────────

class ProjectProfileStore:
    """
    Manages per-subscriber project profiles via Code-Voyager Brain.

    SessionStart: load profile → inject as agent context
    SessionEnd: update profile from audit transcript
    Skill Factory: mine transcript → create project-specific SKILL files
    """

    def __init__(self, storage_dir: str | None = None):
        self._storage_dir = Path(
            storage_dir or
            Path.home() / ".agentxploitor" / "project_profiles"
        )
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        # Code-Voyager Brain instance
        self._brain: Any = None
        self._skill_factory: Any = None
        if CODE_VOYAGER_AVAILABLE:
            try:
                self._brain = VoyagerBrain(
                    storage_dir=str(self._storage_dir / "voyager_brain")
                )
                self._skill_factory = SkillFactory(
                    storage_dir=str(self._storage_dir / "skills")
                )
            except Exception:
                self._brain = None
                self._skill_factory = None

    # ── Public API ───────────────────────────────────────────────────────────

    def get_profile(self, target_id: str) -> ProjectProfile:
        """
        Load project profile for SessionStart context injection.
        Returns empty profile if this is the first audit.
        """
        path = self._storage_dir / f"{target_id}.json"
        if path.exists():
            try:
                profile = ProjectProfile.from_dict(json.loads(path.read_text()))
                # Enrich with Code-Voyager Brain if available
                if self._brain:
                    try:
                        brain_context = self._brain.load(target_id)
                        if brain_context:
                            profile.brain_summary = brain_context
                    except Exception:
                        pass
                return profile
            except Exception:
                pass
        return ProjectProfile(target_id=target_id)

    def update_profile(
        self,
        target_id: str,
        transcript: str,
        audit_record: Any = None  # AuditMemoryRecord
    ) -> ProjectProfile:
        """
        Update project profile at SessionEnd from audit transcript.
        Also fires Code-Voyager Skill Factory to mine new skills.
        """
        profile = self.get_profile(target_id)

        # Update from audit record if provided
        if audit_record:
            profile.target_value = audit_record.target_value
            profile.target_type = audit_record.target_type
            profile.audit_count += 1
            profile.last_audited = audit_record.completed_at
            profile.last_overall_severity = audit_record.overall_severity
            profile.last_bytecode_hash = audit_record.bytecode_hash
            profile.last_source_hash = audit_record.source_hash
            profile.updated_at = datetime.now(timezone.utc).isoformat()

            # Record new skills created during this audit
            if audit_record.new_skill_ids:
                profile.custom_skill_ids.extend(audit_record.new_skill_ids)
                profile.custom_skill_ids = list(set(profile.custom_skill_ids))

        # Update Code-Voyager Brain from transcript
        if self._brain and transcript:
            try:
                updated_summary = self._brain.update(
                    session_id=target_id,
                    transcript=transcript,
                    context=profile.brain_summary
                )
                if updated_summary:
                    profile.brain_summary = updated_summary
            except Exception:
                # Fallback: append transcript summary to brain
                if audit_record and audit_record.transcript_summary:
                    profile.brain_summary = (
                        f"{profile.brain_summary}\n\n"
                        f"[{profile.last_audited}]\n"
                        f"{audit_record.transcript_summary}"
                    ).strip()

        # Fire Skill Factory — mine transcript for reusable techniques
        new_skill_ids = []
        if self._skill_factory and transcript:
            try:
                proposed_skills = self._skill_factory.mine(
                    transcript=transcript,
                    context=f"Target: {profile.target_value} ({profile.target_type})",
                    project_id=target_id
                )
                for skill in (proposed_skills or []):
                    skill_id = self._skill_factory.save(skill, project_id=target_id)
                    if skill_id:
                        new_skill_ids.append(skill_id)
                        profile.custom_skill_ids.append(skill_id)
            except Exception:
                pass

        # Persist updated profile
        path = self._storage_dir / f"{target_id}.json"
        path.write_text(json.dumps(profile.to_dict(), indent=2))

        return profile

    def get_custom_skills(self, target_id: str) -> list[str]:
        """Retrieve skill IDs built specifically for this project."""
        profile = self.get_profile(target_id)
        return profile.custom_skill_ids

    def enable_monitoring(self, target_id: str, subscriber_fid: int) -> None:
        """Mark target as subscribed for continuous monitoring."""
        profile = self.get_profile(target_id)
        profile.monitoring_enabled = True
        profile.subscriber_fid = subscriber_fid
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._storage_dir / f"{target_id}.json"
        path.write_text(json.dumps(profile.to_dict(), indent=2))

    def list_monitored(self) -> list[ProjectProfile]:
        """Return all profiles with monitoring enabled."""
        profiles = []
        for path in self._storage_dir.glob("*.json"):
            try:
                p = ProjectProfile.from_dict(json.loads(path.read_text()))
                if p.monitoring_enabled:
                    profiles.append(p)
            except Exception:
                continue
        return profiles
