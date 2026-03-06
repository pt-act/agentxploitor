"""
AuditMemoryRecord — Persistent audit fact storage via SimpleMem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Every completed audit stores its findings here.
Every new audit of the same target loads history from here.
Delta analysis between versions is computed here.

Built on SimpleMem (academic-grade memory architecture).
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

# SimpleMem import — graceful fallback if not available
try:
    sys.path.insert(0, str(Path(__file__).parents[4] / "hexstrike.aiV2-main" / "SimpleMem-main"))
    from memory.unified_memory import UnifiedMemory  # type: ignore
    SIMPLEMEM_AVAILABLE = True
except ImportError:
    SIMPLEMEM_AVAILABLE = False
    UnifiedMemory = None


# ─── Data Models ────────────────────────────────────────────────────────────

@dataclass
class Finding:
    """A single vulnerability finding from an audit."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    severity: Literal["critical", "high", "medium", "low", "info"] = "info"
    category: str = ""                  # e.g. "reentrancy", "access_control"
    title: str = ""
    description: str = ""
    location: str = ""                  # file:line or URL path
    cve: str | None = None             # CVE reference if applicable
    cwe: str | None = None             # CWE reference if applicable
    attack_chain: list[str] = field(default_factory=list)
    confidence: float = 0.0            # 0.0 – 1.0
    fix_recommendation: str = ""
    visual_proof_id: str | None = None # ID of associated screenshot diff


@dataclass
class AuditMemoryRecord:
    """
    Complete record of a single audit — stored in SimpleMem after completion.

    This is the atomic unit of the intelligence layer.
    Every record stored here makes every future audit smarter.
    """
    # Identity
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str = ""                 # Stable ID: hash of (type + value + chain)
    target_type: Literal[
        "contract_evm", "contract_solana", "github_repo", "miniapp_url"
    ] = "contract_evm"
    target_value: str = ""             # Address, URL, or repo path
    chain: str | None = None           # "base", "ethereum", "solana", etc.

    # Provenance
    requested_by_fid: int = 0          # Farcaster FID of requester
    audit_mode: Literal["self_audit", "research", "contract"] = "contract"
    audit_type: Literal[
        "contract_basic", "contract_deep", "miniapp", "full_stack"
    ] = "contract_basic"
    independence_declaration: str = (
        "This audit was independently requested. "
        "AgentxploiTor has no affiliation with the audited project."
    )

    # Timing
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None

    # Source state (for delta analysis)
    bytecode_hash: str | None = None   # Hash of contract bytecode at audit time
    source_hash: str | None = None     # Hash of source code if available
    source_available: bool = False

    # Analysis provenance
    tools_used: list[str] = field(default_factory=list)      # e.g. ["slither", "mythril"]
    agents_used: list[str] = field(default_factory=list)     # HexStrike agent names
    skill_ids_applied: list[str] = field(default_factory=list)  # Code-Voyager skill IDs
    hexstrike_request_id: str | None = None

    # Findings
    findings: list[Finding] = field(default_factory=list)
    overall_severity: Literal[
        "critical", "high", "medium", "low", "clean"
    ] = "clean"
    overall_confidence: float = 0.0

    # Learning output
    transcript_summary: str = ""       # What the agent learned this session
    new_skill_ids: list[str] = field(default_factory=list)  # Skills created from this audit

    @classmethod
    def make_target_id(cls, target_type: str, target_value: str, chain: str | None) -> str:
        """Generate a stable, deterministic target ID."""
        raw = f"{target_type}:{target_value}:{chain or 'none'}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def compute_overall_severity(self) -> None:
        """Derive overall severity from finding set."""
        severity_order = ["critical", "high", "medium", "low", "info"]
        for level in severity_order:
            if any(f.severity == level for f in self.findings):
                self.overall_severity = level
                return
        self.overall_severity = "clean"

    def to_simplemem_dialogue(self) -> str:
        """
        Convert record to SimpleMem dialogue format.
        Used when storing via SimpleMem.add_dialogue().
        """
        finding_summary = "\n".join([
            f"  [{f.severity.upper()}] {f.title} @ {f.location} (confidence: {f.confidence:.0%})"
            for f in self.findings
        ]) or "  No findings — target is clean."

        return (
            f"Audit completed for target {self.target_value} ({self.target_type}, "
            f"chain: {self.chain or 'n/a'}).\n"
            f"Audit ID: {self.audit_id}\n"
            f"Overall severity: {self.overall_severity}\n"
            f"Findings ({len(self.findings)}):\n{finding_summary}\n"
            f"Tools: {', '.join(self.tools_used)}\n"
            f"Skills applied: {', '.join(self.skill_ids_applied) or 'none'}\n"
            f"Source hash: {self.source_hash or 'unavailable'}\n"
            f"Bytecode hash: {self.bytecode_hash or 'unavailable'}\n"
            f"Requested by FID: {self.requested_by_fid}\n"
            f"Completed: {self.completed_at}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict for JSON storage."""
        d = asdict(self)
        d["findings"] = [asdict(f) for f in self.findings]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuditMemoryRecord":
        """Deserialise from dict."""
        findings = [Finding(**f) for f in d.pop("findings", [])]
        record = cls(**d)
        record.findings = findings
        return record


# ─── Storage Interface ───────────────────────────────────────────────────────

class AuditMemoryStore:
    """
    Interface over SimpleMem for audit record persistence.

    Provides:
    - store(record): persist completed audit to SimpleMem
    - get_history(target_id): all past audits for a target
    - find_similar(target_type, target_value): semantic search
    - get_delta(target_id, hash_a, hash_b): what changed between versions
    - get_stats(): system-wide learning statistics
    """

    def __init__(self, storage_dir: str | None = None):
        self._storage_dir = Path(
            storage_dir or
            Path.home() / ".agentxploitor" / "audit_memory"
        )
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._storage_dir / "index.json"
        self._index = self._load_index()

        # SimpleMem instance for semantic search
        self._simplemem: Any = None
        if SIMPLEMEM_AVAILABLE:
            try:
                self._simplemem = UnifiedMemory(
                    project_name="agentxploitor_audits",
                    storage_dir=str(self._storage_dir / "simplemem")
                )
            except Exception:
                self._simplemem = None

    # ── Public API ───────────────────────────────────────────────────────────

    def store(self, record: AuditMemoryRecord) -> None:
        """Persist a completed audit record."""
        record.compute_overall_severity()

        # Write JSON record to disk
        record_path = self._storage_dir / f"{record.audit_id}.json"
        record_path.write_text(json.dumps(record.to_dict(), indent=2))

        # Update index
        target_id = record.target_id or AuditMemoryRecord.make_target_id(
            record.target_type, record.target_value, record.chain
        )
        if target_id not in self._index:
            self._index[target_id] = []
        self._index[target_id].append({
            "audit_id": record.audit_id,
            "completed_at": record.completed_at,
            "overall_severity": record.overall_severity,
            "finding_count": len(record.findings),
            "bytecode_hash": record.bytecode_hash,
            "source_hash": record.source_hash,
        })
        self._save_index()

        # Store in SimpleMem for semantic search
        if self._simplemem:
            try:
                self._simplemem.store(
                    record.to_simplemem_dialogue(),
                    memory_type="fact",
                    metadata={"target_id": target_id, "audit_id": record.audit_id}
                )
            except Exception:
                pass  # SimpleMem failure never blocks storage

    def get_history(self, target_id: str) -> list[AuditMemoryRecord]:
        """Retrieve all past audits for a target, chronological order."""
        entries = self._index.get(target_id, [])
        records = []
        for entry in entries:
            path = self._storage_dir / f"{entry['audit_id']}.json"
            if path.exists():
                try:
                    records.append(
                        AuditMemoryRecord.from_dict(json.loads(path.read_text()))
                    )
                except Exception:
                    continue
        return sorted(records, key=lambda r: r.completed_at or "")

    def find_similar(
        self,
        target_type: str,
        target_value: str,
        limit: int = 5
    ) -> list[AuditMemoryRecord]:
        """
        Semantic search for similar past audits.
        Uses SimpleMem if available, falls back to type-based matching.
        """
        if self._simplemem:
            try:
                results = self._simplemem.recall(
                    f"{target_type} {target_value}",
                    limit=limit
                )
                audit_ids = [r.get("metadata", {}).get("audit_id") for r in results]
                records = []
                for aid in audit_ids:
                    if aid:
                        path = self._storage_dir / f"{aid}.json"
                        if path.exists():
                            records.append(
                                AuditMemoryRecord.from_dict(json.loads(path.read_text()))
                            )
                return records
            except Exception:
                pass

        # Fallback: type-based matching from index
        matches = []
        for tid, entries in self._index.items():
            if entries:
                for e in entries[-1:]:  # latest audit per target
                    path = self._storage_dir / f"{e['audit_id']}.json"
                    if path.exists():
                        try:
                            r = AuditMemoryRecord.from_dict(json.loads(path.read_text()))
                            if r.target_type == target_type:
                                matches.append(r)
                        except Exception:
                            continue
        return matches[:limit]

    def get_delta(
        self,
        target_id: str,
        hash_a: str,
        hash_b: str
    ) -> dict[str, Any]:
        """
        Compare findings between two audit versions of the same target.
        Returns: new findings, resolved findings, persisting findings.
        """
        history = self.get_history(target_id)

        record_a = next(
            (r for r in history if r.bytecode_hash == hash_a or r.source_hash == hash_a),
            None
        )
        record_b = next(
            (r for r in history if r.bytecode_hash == hash_b or r.source_hash == hash_b),
            None
        )

        if not record_a or not record_b:
            return {"error": "One or both versions not found in history"}

        findings_a = {f.title: f for f in record_a.findings}
        findings_b = {f.title: f for f in record_b.findings}

        return {
            "target_id": target_id,
            "version_a": {"audit_id": record_a.audit_id, "completed_at": record_a.completed_at},
            "version_b": {"audit_id": record_b.audit_id, "completed_at": record_b.completed_at},
            "new_findings": [
                asdict(f) for k, f in findings_b.items() if k not in findings_a
            ],
            "resolved_findings": [
                asdict(f) for k, f in findings_a.items() if k not in findings_b
            ],
            "persisting_findings": [
                asdict(f) for k, f in findings_b.items() if k in findings_a
            ],
        }

    def get_stats(self) -> dict[str, Any]:
        """System-wide learning statistics for transparency display."""
        total_audits = sum(len(v) for v in self._index.values())
        total_targets = len(self._index)
        all_tools: set[str] = set()
        all_skills: set[str] = set()
        severity_counts: dict[str, int] = {}

        for entries in self._index.values():
            for entry in entries:
                path = self._storage_dir / f"{entry['audit_id']}.json"
                if path.exists():
                    try:
                        r = AuditMemoryRecord.from_dict(json.loads(path.read_text()))
                        all_tools.update(r.tools_used)
                        all_skills.update(r.skill_ids_applied)
                        sev = r.overall_severity
                        severity_counts[sev] = severity_counts.get(sev, 0) + 1
                    except Exception:
                        continue

        return {
            "total_audits": total_audits,
            "unique_targets": total_targets,
            "tools_seen": sorted(all_tools),
            "patterns_learned": len(all_skills),
            "severity_distribution": severity_counts,
            "simplemem_available": SIMPLEMEM_AVAILABLE,
        }

    # ── Private ──────────────────────────────────────────────────────────────

    def _load_index(self) -> dict[str, list[dict]]:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text())
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index, indent=2))
