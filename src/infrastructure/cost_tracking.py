"""
Cost Tracking

Tracks compute, storage, and API costs per audit for billing
and cost optimization.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict
import json


class CostType(str, Enum):
    """Types of costs."""
    COMPUTE = "compute"
    STORAGE = "storage"
    API_CALL = "api_call"
    LLM_TOKENS = "llm_tokens"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class CostEntry:
    """Individual cost entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audit_id: str = ""
    workspace_id: str = ""
    cost_type: CostType = CostType.COMPUTE
    description: str = ""
    amount: float = 0.0
    currency: str = "USD"
    quantity: float = 0.0
    unit: str = ""
    unit_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'audit_id': self.audit_id,
            'workspace_id': self.workspace_id,
            'cost_type': self.cost_type.value,
            'description': self.description,
            'amount': self.amount,
            'currency': self.currency,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_cost': self.unit_cost': self.metadata,
,
            'metadata            'timestamp': self.timestamp,
        }


@dataclass
class AuditCostSummary:
    """Cost summary for an audit."""
    audit_id: str
    workspace_id: str
    compute_cost: float = 0.0
    storage_cost: float = 0.0
    api_call_cost: float = 0.0
    llm_tokens_cost: float = 0.0
    external_service_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    entries: List[CostEntry] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    
    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'audit_id': self.audit_id,
            'workspace_id': self.workspace_id,
            'compute_cost': round(self.compute_cost, 4),
            'storage_cost': round(self.storage_cost, 4),
            'api_call_cost': round(self.api_call_cost, 4),
            'llm_tokens_cost': round(self.llm_tokens_cost, 4),
            'external_service_cost': round(self.external_service_cost, 4),
            'total_cost': round(self.total_cost, 4),
            'currency': self.currency,
            'duration_seconds': round(self.duration_seconds, 2),
            'entry_count': len(self.entries),
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }


class CostTracker:
    """
    Track costs per audit.
    
    Usage:
        tracker = CostTracker()
        
        with tracker.track_compute("audit-123", "workspace-1"):
            # Do compute work
            time.sleep(1)
        
        tracker.track_llm_tokens("audit-123", "gpt-4", 1000, 2000)
        
        summary = tracker.get_audit_cost("audit-123")
        print(f"Total cost: ${summary.total_cost}")
    """
    
    UNIT_COSTS = {
        'compute': {
            'cpu_second': 0.0001,
            'gpu_second': 0.001,
        },
        'storage': {
            'gb_month': 0.023,
            'gb_transfer': 0.09,
        },
        'api_call': {
            'rpc_call': 0.0001,
            'webhook': 0.0005,
        },
        'llm_tokens': {
            'gpt4_input': 0.03 / 1000,
            'gpt4_output': 0.06 / 1000,
            'gpt35_input': 0.001 / 1000,
            'gpt35_output': 0.002 / 1000,
            'claude_input': 0.003 / 1000,
            'claude_output': 0.015 / 1000,
        },
        'external_service': {
            'slither': 0.01,
            'mythril': 0.02,
            'etherscan': 0.001,
        },
    }
    
    def __init__(self):
        self._costs: Dict[str, List[CostEntry]] = defaultdict(list)
        self._active_compute: Dict[str, float] = {}
    
    def start_compute_tracking(self, audit_id: str, workspace_id: str) -> str:
        """Start tracking compute time for an audit."""
        tracking_id = f"{audit_id}:{time.time()}"
        self._active_compute[tracking_id] = time.time()
        return tracking_id
    
    def end_compute_tracking(
        self,
        tracking_id: str,
        audit_id: str,
        workspace_id: str,
        compute_type: str = 'cpu_second',
    ) -> Optional[CostEntry]:
        """End tracking compute time and record cost."""
        if tracking_id not in self._active_compute:
            return None
        
        start_time = self._active_compute.pop(tracking_id)
        duration = time.time() - start_time
        unit_cost = self.UNIT_COSTS['compute'].get(compute_type, 0.0001)
        
        entry = CostEntry(
            audit_id=audit_id,
            workspace_id=workspace_id,
            cost_type=CostType.COMPUTE,
            description=f"Compute time ({compute_type})",
            quantity=duration,
            unit=compute_type,
            unit_cost=unit_cost,
            amount=round(duration * unit_cost, 6),
            metadata={'duration_seconds': duration},
        )
        
        self._costs[audit_id].append(entry)
        return entry
    
    @contextmanager
    def track_compute(self, audit_id: str, workspace_id: str, compute_type: str = 'cpu_second'):
        """Context manager for tracking compute costs."""
        tracking_id = self.start_compute_tracking(audit_id, workspace_id)
        try:
            yield tracking_id
        finally:
            self.end_compute_tracking(tracking_id, audit_id, workspace_id, compute_type)
    
    def track_storage(
        self,
        audit_id: str,
        workspace_id: str,
        size_gb: float,
        duration_hours: float,
        storage_type: str = 'gb_month',
    ):
        """Track storage costs."""
        unit_cost = self.UNIT_COSTS['storage'].get(storage_type, 0.023)
        hours_fraction = duration_hours / 720
        cost = size_gb * unit_cost * hours_fraction
        
        entry = CostEntry(
            audit_id=audit_id,
            workspace_id=workspace_id,
            cost_type=CostType.STORAGE,
            description=f"Storage ({storage_type})",
            quantity=size_gb * hours_fraction,
            unit=storage_type,
            unit_cost=unit_cost,
            amount=round(cost, 6),
            metadata={'size_gb': size_gb, 'duration_hours': duration_hours},
        )
        
        self._costs[audit_id].append(entry)
        return entry
    
    def track_api_call(
        self,
        audit_id: str,
        workspace_id: str,
        service: str,
        count: int = 1,
    ):
        """Track API call costs."""
        unit_cost = self.UNIT_COSTS['api_call'].get(service, 0.0001)
        cost = count * unit_cost
        
        entry = CostEntry(
            audit_id=audit_id,
            workspace_id=workspace_id,
            cost_type=CostType.API_CALL,
            description=f"API calls to {service}",
            quantity=count,
            unit=service,
            unit_cost=unit_cost,
            amount=round(cost, 6),
            metadata={'service': service, 'count': count},
        )
        
        self._costs[audit_id].append(entry)
        return entry
    
    def track_llm_tokens(
        self,
        audit_id: str,
        workspace_id: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Track LLM token costs."""
        model_key = model.lower().replace('-', '').replace('.', '')
        
        input_cost = 0
        if input_tokens > 0:
            input_unit = self.UNIT_COSTS['llm_tokens'].get(f'{model_key}_input', 0.001)
            input_cost = input_tokens * input_unit
        
        output_cost = 0
        if output_tokens > 0:
            output_unit = self.UNIT_COSTS['llm_tokens'].get(f'{model_key}_output', 0.002)
            output_cost = output_tokens * output_unit
        
        total_cost = input_cost + output_cost
        
        if total_cost > 0:
            entry = CostEntry(
                audit_id=audit_id,
                workspace_id=workspace_id,
                cost_type=CostType.LLM_TOKENS,
                description=f"LLM tokens ({model})",
                quantity=input_tokens + output_tokens,
                unit='tokens',
                unit_cost=total_cost / (input_tokens + output_tokens) if (input_tokens + output_tokens) > 0 else 0,
                amount=round(total_cost, 6),
                metadata={
                    'model': model,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                },
            )
            
            self._costs[audit_id].append(entry)
            return entry
        
        return None
    
    def track_external_service(
        self,
        audit_id: str,
        workspace_id: str,
        service: str,
        count: int = 1,
    ):
        """Track external service costs."""
        unit_cost = self.UNIT_COSTS['external_service'].get(service, 0.01)
        cost = count * unit_cost
        
        entry = CostEntry(
            audit_id=audit_id,
            workspace_id=workspace_id,
            cost_type=CostType.EXTERNAL_SERVICE,
            description=f"External service ({service})",
            quantity=count,
            unit=service,
            unit_cost=unit_cost,
            amount=round(cost, 6),
            metadata={'service': service, 'count': count},
        )
        
        self._costs[audit_id].append(entry)
        return entry
    
    def get_audit_cost(self, audit_id: str) -> AuditCostSummary:
        """Get cost summary for an audit."""
        entries = self._costs.get(audit_id, [])
        
        if not entries:
            return AuditCostSummary(audit_id=audit_id, workspace_id="")
        
        workspace_id = entries[0].workspace_id
        started_at = entries[0].timestamp
        completed_at = entries[-1].timestamp
        
        summary = AuditCostSummary(
            audit_id=audit_id,
            workspace_id=workspace_id,
            started_at=started_at,
            completed_at=completed_at,
            entries=entries,
        )
        
        for entry in entries:
            summary.total_cost += entry.amount
            
            if entry.cost_type == CostType.COMPUTE:
                summary.compute_cost += entry.amount
            elif entry.cost_type == CostType.STORAGE:
                summary.storage_cost += entry.amount
            elif entry.cost_type == CostType.API_CALL:
                summary.api_call_cost += entry.amount
            elif entry.cost_type == CostType.LLM_TOKENS:
                summary.llm_tokens_cost += entry.amount
            elif entry.cost_type == CostType.EXTERNAL_SERVICE:
                summary.external_service_cost += entry.amount
        
        return summary
    
    def get_workspace_costs(
        self,
        workspace_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditCostSummary]:
        """Get cost summaries for all audits in a workspace."""
        summaries = []
        
        for audit_id, entries in self._costs.items():
            if not entries:
                continue
            
            if entries[0].workspace_id != workspace_id:
                continue
            
            if start_date or end_date:
                timestamps = [datetime.fromisoformat(e.timestamp) for e in entries]
                if start_date and all(t < start_date for t in timestamps):
                    continue
                if end_date and all(t > end_date for t in timestamps):
                    continue
            
            summaries.append(self.get_audit_cost(audit_id))
        
        return summaries
    
    def get_total_costs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """Get total costs across all audits."""
        totals = {
            'compute': 0.0,
            'storage': 0.0,
            'api_call': 0.0,
            'llm_tokens': 0.0,
            'external_service': 0.0,
            'total': 0.0,
        }
        
        for audit_id in self._costs:
            summary = self.get_audit_cost(audit_id)
            
            if start_date or end_date:
                timestamps = [datetime.fromisoformat(e.timestamp) for e in summary.entries]
                if start_date and all(t < start_date for t in timestamps):
                    continue
                if end_date and all(t > end_date for t in timestamps):
                    continue
            
            totals['compute'] += summary.compute_cost
            totals['storage'] += summary.storage_cost
            totals['api_call'] += summary.api_call_cost
            totals['llm_tokens'] += summary.llm_tokens_cost
            totals['external_service'] += summary.external_service_cost
            totals['total'] += summary.total_cost
        
        return totals
    
    def export_costs_json(self, audit_id: str) -> str:
        """Export costs as JSON."""
        summary = self.get_audit_cost(audit_id)
        return json.dumps(summary.to_dict(), indent=2)


from contextlib import contextmanager


_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def track_compute(audit_id: str, workspace_id: str, compute_type: str = 'cpu_second'):
    """Convenience function to track compute costs."""
    return get_cost_tracker().track_compute(audit_id, workspace_id, compute_type)


def track_llm_tokens(audit_id: str, workspace_id: str, model: str, input_tokens: int, output_tokens: int):
    """Convenience function to track LLM tokens."""
    return get_cost_tracker().track_llm_tokens(audit_id, workspace_id, model, input_tokens, output_tokens)
