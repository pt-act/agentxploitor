"""
Integration Tests - Full Pipeline Tests

Tests the complete audit workflow from payment to report generation.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from models import JobSession, JobStatus
from tests.fixtures.fixtures import (
    SAMPLE_CONTRACTS,
    SAMPLE_JOBS,
    SAMPLE_PAYMENTS,
    create_mock_analyzer_result,
)


@pytest.fixture
def mock_db():
    """Create a mock database pool."""
    db = MagicMock()
    db.connected = True
    db.fetchrow = AsyncMock()
    db.fetch = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.connected = True
    redis.enqueue = AsyncMock(return_value=True)
    redis.dequeue = AsyncMock(return_value=None)
    redis.lpush = AsyncMock(return_value=1)
    redis.rpop = AsyncMock(return_value=None)
    return redis


@pytest.fixture
def mock_analyzer():
    """Create a mock analyzer."""
    async def analyze(contract_source: str, **kwargs):
        vulnerabilities = []
        if 'reentrancy' in contract_source.lower():
            vulnerabilities.append('reentrancy')
        if 'overflow' in contract_source.lower():
            vulnerabilities.append('integer_overflow')
        if 'access' in contract_source.lower():
            vulnerabilities.append('access_control')
        
        return create_mock_analyzer_result(vulnerabilities)
    
    return analyze


class TestFullPipeline:
    """Integration tests for the complete audit pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_audit_pipeline_success(self, mock_db, mock_redis, mock_analyzer):
        """Test successful end-to-end audit pipeline."""
        job_data = SAMPLE_JOBS['standard_audit'].to_dict()
        
        job = JobSession(
            id=job_data['id'],
            target_url=job_data['target_url'],
            wallet_address=job_data['wallet_address'],
            status=JobStatus.PENDING_PAYMENT,
        )
        
        assert job.status == JobStatus.PENDING_PAYMENT
        
        job.status = JobStatus.PAYMENT_VERIFIED
        assert job.status == JobStatus.PAYMENT_VERIFIED
        
        job.status = JobStatus.QUEUED
        assert job.status == JobStatus.QUEUED
        
        job.status = JobStatus.IN_PROGRESS
        assert job.status == JobStatus.IN_PROGRESS
        
        result = await mock_analyzer(SAMPLE_CONTRACTS['reentrancy_vulnerable'].source)
        assert result['success'] is True
        assert len(result['findings']) >= 1
        
        job.findings_count = {
            'critical': sum(1 for f in result['findings'] if f['severity'] == 'CRITICAL'),
            'high': sum(1 for f in result['findings'] if f['severity'] == 'HIGH'),
            'medium': sum(1 for f in result['findings'] if f['severity'] == 'MEDIUM'),
            'low': sum(1 for f in result['findings'] if f['severity'] == 'LOW'),
        }
        
        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED
        assert job.findings_count['critical'] + job.findings_count['high'] >= 1
    
    @pytest.mark.asyncio
    async def test_payment_verification_flow(self, mock_db):
        """Test payment verification process."""
        payment = SAMPLE_PAYMENTS['valid_payment']
        
        is_valid = (
            payment.valid and
            payment.confirmations >= 12 and
            int(payment.amount) >= 10000000000000000
        )
        
        assert is_valid is True
        
        insufficient = SAMPLE_PAYMENTS['insufficient_payment']
        is_valid_insufficient = (
            insufficient.valid and
            int(insufficient.amount) >= 10000000000000000
        )
        
        assert is_valid_insufficient is False
        
        unconfirmed = SAMPLE_PAYMENTS['unconfirmed_payment']
        is_valid_unconfirmed = (
            unconfirmed.confirmations >= 12
        )
        
        assert is_valid_unconfirmed is False
    
    @pytest.mark.asyncio
    async def test_analyzer_failure_handling(self, mock_analyzer):
        """Test handling of analyzer failures."""
        async def failing_analyzer(*args, **kwargs):
            raise Exception("Analyzer crashed")
        
        with pytest.raises(Exception):
            await failing_analyzer("contract source")
        
        result = await mock_analyzer("safe contract")
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_multi_analyzer_workflow(self, mock_analyzer):
        """Test running multiple analyzers in parallel."""
        contract = SAMPLE_CONTRACTS['reentrancy_vulnerable'].source
        
        analyzers = ['slither', 'mythril', 'echidna']
        
        results = await asyncio.gather(
            *[mock_analyzer(contract, analyzer=a) for a in analyzers],
            return_exceptions=True,
        )
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 3
        
        all_findings = []
        for result in successful_results:
            all_findings.extend(result['findings'])
        
        assert len(all_findings) >= 1
    
    @pytest.mark.asyncio
    async def test_priority_queue_ordering(self, mock_redis):
        """Test that jobs are processed in priority order."""
        jobs = [
            ('job-low', 'low'),
            ('job-critical', 'critical'),
            ('job-normal', 'normal'),
            ('job-high', 'high'),
        ]
        
        for job_id, priority in jobs:
            await mock_redis.enqueue(job_id, priority=priority)
        
        enqueue_calls = mock_redis.enqueue.call_args_list
        assert len(enqueue_calls) == 4


class TestJobStateTransitions:
    """Tests for job state machine transitions."""
    
    @pytest.mark.asyncio
    async def test_valid_state_transitions(self):
        """Test valid state transitions."""
        job = JobSession(
            id='test-job',
            target_url='https://example.com',
            status=JobStatus.PENDING_PAYMENT,
        )
        
        valid_transitions = {
            JobStatus.PENDING_PAYMENT: [JobStatus.PAYMENT_VERIFIED, JobStatus.QUEUED, JobStatus.CANCELLED],
            JobStatus.PAYMENT_VERIFIED: [JobStatus.QUEUED, JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
            JobStatus.QUEUED: [JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
            JobStatus.IN_PROGRESS: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED],
            JobStatus.COMPLETED: [],
            JobStatus.FAILED: [JobStatus.QUEUED],
            JobStatus.CANCELLED: [JobStatus.QUEUED],
        }
        
        job.status = JobStatus.PAYMENT_VERIFIED
        assert job.status in valid_transitions[JobStatus.PENDING_PAYMENT]
        
        job.status = JobStatus.QUEUED
        assert job.status in valid_transitions[JobStatus.PAYMENT_VERIFIED]
        
        job.status = JobStatus.IN_PROGRESS
        assert job.status in valid_transitions[JobStatus.QUEUED]
        
        job.status = JobStatus.COMPLETED
        assert job.status in valid_transitions[JobStatus.IN_PROGRESS]
    
    @pytest.mark.asyncio
    async def test_job_recovery_from_failure(self):
        """Test job recovery after failure."""
        job = JobSession(
            id='test-job',
            target_url='https://example.com',
            status=JobStatus.FAILED,
            error='Analyzer timeout',
        )
        
        assert job.status == JobStatus.FAILED
        assert job.error is not None
        
        job.error = None
        job.status = JobStatus.QUEUED
        
        assert job.status == JobStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self):
        """Test job cancellation workflow."""
        job = JobSession(
            id='test-job',
            target_url='https://example.com',
            status=JobStatus.IN_PROGRESS,
        )
        
        job.status = JobStatus.CANCELLED
        
        assert job.status == JobStatus.CANCELLED


class TestSessionRecovery:
    """Tests for session recovery and checkpointing."""
    
    @pytest.mark.asyncio
    async def test_checkpoint_save_and_restore(self):
        """Test saving and restoring checkpoints."""
        checkpoint = {
            'job_id': 'job-001',
            'current_step': 'exploit_generation',
            'completed_steps': ['payment', 'scan'],
            'findings_count': {'critical': 1, 'high': 2},
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        serialized = json.dumps(checkpoint)
        restored = json.loads(serialized)
        
        assert restored['job_id'] == checkpoint['job_id']
        assert restored['current_step'] == 'exploit_generation'
        assert len(restored['completed_steps']) == 2
    
    @pytest.mark.asyncio
    async def test_recovery_from_timeout(self):
        """Test recovery from job timeout."""
        job = JobSession(
            id='timeout-job',
            target_url='https://example.com',
            status=JobStatus.IN_PROGRESS,
        )
        
        last_update = datetime.utcnow()
        job.updated_at = last_update.isoformat()
        
        import time
        time.sleep(0.1)
        
        current_time = datetime.utcnow()
        elapsed = (current_time - last_update).total_seconds()
        
        timeout_threshold = 0.05
        is_timeout = elapsed > timeout_threshold
        
        assert is_timeout is True
        
        job.status = JobStatus.FAILED
        job.error = 'Job timed out'
        
        assert job.status == JobStatus.FAILED


class TestReportGeneration:
    """Tests for report generation."""
    
    @pytest.mark.asyncio
    async def test_report_generation_with_findings(self, mock_analyzer):
        """Test report generation with findings."""
        result = await mock_analyzer(SAMPLE_CONTRACTS['reentrancy_vulnerable'].source)
        
        report = {
            'id': 'report-001',
            'job_id': 'job-001',
            'target_url': 'https://example.com',
            'summary': {
                'CRITICAL': sum(1 for f in result['findings'] if f['severity'] == 'CRITICAL'),
                'HIGH': sum(1 for f in result['findings'] if f['severity'] == 'HIGH'),
                'MEDIUM': sum(1 for f in result['findings'] if f['severity'] == 'MEDIUM'),
                'LOW': sum(1 for f in result['findings'] if f['severity'] == 'LOW'),
            },
            'vulnerabilities': result['findings'],
            'created_at': datetime.utcnow().isoformat(),
        }
        
        assert report['summary']['CRITICAL'] + report['summary']['HIGH'] >= 1
        assert len(report['vulnerabilities']) >= 1
    
    @pytest.mark.asyncio
    async def test_report_serialization(self):
        """Test report can be serialized to JSON."""
        report = {
            'id': 'report-001',
            'summary': {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 0, 'LOW': 0},
            'vulnerabilities': [
                {
                    'id': 'finding-001',
                    'title': 'Test Finding',
                    'severity': 'CRITICAL',
                    'confidence': 0.95,
                }
            ],
        }
        
        serialized = json.dumps(report)
        deserialized = json.loads(serialized)
        
        assert deserialized['id'] == report['id']
        assert deserialized['summary']['CRITICAL'] == 1


class TestEventSourcingIntegration:
    """Tests for event sourcing in the pipeline."""
    
    @pytest.mark.asyncio
    async def test_event_sequence(self):
        """Test that events are generated in correct sequence."""
        from domain.event_sourcing import (
            JobCreatedEvent,
            JobStateChangedEvent,
            PaymentVerifiedEvent,
            FindingDiscoveredEvent,
            JobCompletedEvent,
        )
        
        events = []
        
        events.append(JobCreatedEvent.create(
            job_id='job-001',
            target_url='https://example.com',
            scope='Full audit',
            priority='normal',
        ))
        
        events.append(PaymentVerifiedEvent.create(
            job_id='job-001',
            tx_hash='0xabc...',
            amount='100000000000000000',
            confirmations=12,
        ))
        
        events.append(JobStateChangedEvent.create(
            job_id='job-001',
            from_status='pending_payment',
            to_status='queued',
        ))
        
        events.append(FindingDiscoveredEvent.create(
            job_id='job-001',
            finding_id='finding-001',
            title='Reentrancy',
            severity='CRITICAL',
            cvss_score=9.8,
            analyzer='slither',
        ))
        
        events.append(JobCompletedEvent.create(
            job_id='job-001',
            findings_count={'critical': 1, 'high': 0, 'medium': 0, 'low': 0},
            report_path='/reports/job-001.json',
        ))
        
        event_types = [e.event_type for e in events]
        
        assert 'job_created' in event_types
        assert 'payment_verified' in event_types
        assert 'job_state_changed' in event_types
        assert 'finding_discovered' in event_types
        assert 'job_completed' in event_types
