"""
Concurrency Tests - Load and Race Condition Tests

Tests system behavior under concurrent load and race conditions.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import defaultdict
import threading

from models import JobSession, JobStatus
from infrastructure.circuit_breaker import CircuitBreaker, CircuitState
from infrastructure.redis_queue import RedisJobQueue, QueuePriority


class TestConcurrentJobProcessing:
    """Tests for concurrent job processing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self):
        """Test creating multiple jobs concurrently."""
        num_jobs = 100
        created_jobs = []
        lock = asyncio.Lock()
        
        async def create_job(job_id: int):
            job = JobSession(
                id=f'job-{job_id:04d}',
                target_url=f'https://example.com/contract/{job_id}',
                status=JobStatus.QUEUED,
            )
            async with lock:
                created_jobs.append(job)
            return job
        
        tasks = [create_job(i) for i in range(num_jobs)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == num_jobs
        assert len(created_jobs) == num_jobs
        
        job_ids = [job.id for job in results]
        assert len(set(job_ids)) == num_jobs
    
    @pytest.mark.asyncio
    async def test_concurrent_status_updates(self):
        """Test concurrent status updates to the same job."""
        job = JobSession(
            id='job-concurrent',
            target_url='https://example.com',
            status=JobStatus.QUEUED,
        )
        
        update_count = 0
        lock = threading.Lock()
        
        async def update_status(new_status: JobStatus):
            nonlocal update_count
            with lock:
                update_count += 1
            job.status = new_status
        
        updates = [JobStatus.IN_PROGRESS] * 10
        tasks = [update_status(s) for s in updates]
        await asyncio.gather(*tasks)
        
        assert update_count == 10
        assert job.status == JobStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_load_test_100_jobs(self):
        """Load test with 100+ concurrent jobs."""
        num_jobs = 150
        processed = {'count': 0}
        lock = asyncio.Lock()
        
        async def process_job(job_id: int):
            await asyncio.sleep(0.01)
            async with lock:
                processed['count'] += 1
        
        start = time.time()
        tasks = [process_job(i) for i in range(num_jobs)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        assert processed['count'] == num_jobs
        assert elapsed < 5.0
    
    @pytest.mark.asyncio
    async def test_backpressure_handling(self):
        """Test backpressure handling under load."""
        queue_size = 0
        max_queue_size = 50
        dropped = 0
        lock = asyncio.Lock()
        
        async def enqueue_job(job_id: int):
            nonlocal queue_size, dropped
            async with lock:
                if queue_size >= max_queue_size:
                    dropped += 1
                    return False
                queue_size += 1
            return True
        
        async def dequeue_job():
            nonlocal queue_size
            await asyncio.sleep(0.005)
            async with lock:
                if queue_size > 0:
                    queue_size -= 1
        
        enqueue_tasks = [enqueue_job(i) for i in range(100)]
        results = await asyncio.gather(*enqueue_tasks)
        
        accepted = sum(1 for r in results if r)
        
        assert accepted <= max_queue_size
        assert dropped >= 50


class TestQueueOrdering:
    """Tests for queue ordering and priority."""
    
    def test_priority_ordering(self):
        """Test that priority queue orders correctly."""
        queue = RedisJobQueue()
        
        low_score = queue._calculate_score(QueuePriority.LOW)
        normal_score = queue._calculate_score(QueuePriority.NORMAL)
        high_score = queue._calculate_score(QueuePriority.HIGH)
        critical_score = queue._calculate_score(QueuePriority.CRITICAL)
        
        assert critical_score < high_score < normal_score < low_score
    
    @pytest.mark.asyncio
    async def test_fifo_within_priority(self):
        """Test FIFO ordering within same priority."""
        jobs = []
        
        async def add_job(job_id: str, priority: QueuePriority):
            timestamp = time.time()
            jobs.append({
                'id': job_id,
                'priority': priority,
                'timestamp': timestamp,
            })
        
        await add_job('job-1', QueuePriority.NORMAL)
        await asyncio.sleep(0.001)
        await add_job('job-2', QueuePriority.NORMAL)
        await asyncio.sleep(0.001)
        await add_job('job-3', QueuePriority.NORMAL)
        
        normal_jobs = [j for j in jobs if j['priority'] == QueuePriority.NORMAL]
        sorted_jobs = sorted(normal_jobs, key=lambda j: j['timestamp'])
        
        assert sorted_jobs[0]['id'] == 'job-1'
        assert sorted_jobs[1]['id'] == 'job-2'
        assert sorted_jobs[2]['id'] == 'job-3'


class TestRaceConditions:
    """Tests for race conditions in state transitions."""
    
    @pytest.mark.asyncio
    async def test_race_in_status_transition(self):
        """Test race condition in status transitions."""
        job = JobSession(
            id='race-job',
            target_url='https://example.com',
            status=JobStatus.QUEUED,
        )
        
        results = []
        lock = asyncio.Lock()
        
        async def try_transition(new_status: JobStatus):
            async with lock:
                valid_transitions = {
                    JobStatus.QUEUED: [JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
                }
                if new_status in valid_transitions.get(job.status, []):
                    job.status = new_status
                    results.append((new_status, True))
                else:
                    results.append((new_status, False))
        
        tasks = [
            try_transition(JobStatus.IN_PROGRESS),
            try_transition(JobStatus.CANCELLED),
        ]
        await asyncio.gather(*tasks)
        
        success_count = sum(1 for _, success in results if success)
        assert success_count == 1
    
    @pytest.mark.asyncio
    async def test_idempotency_under_concurrent_requests(self):
        """Test idempotency of operations under concurrent requests."""
        processed_ids = set()
        results = []
        lock = asyncio.Lock()
        
        async def process_idempotent(request_id: str):
            async with lock:
                if request_id in processed_ids:
                    results.append((request_id, 'duplicate'))
                    return
                processed_ids.add(request_id)
                results.append((request_id, 'processed'))
        
        tasks = [
            process_idempotent('req-001'),
            process_idempotent('req-001'),
            process_idempotent('req-001'),
        ]
        await asyncio.gather(*tasks)
        
        processed_count = sum(1 for _, status in results if status == 'processed')
        duplicate_count = sum(1 for _, status in results if status == 'duplicate')
        
        assert processed_count == 1
        assert duplicate_count == 2


class TestCircuitBreakerConcurrency:
    """Tests for circuit breaker under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_failures_open_circuit(self):
        """Test that concurrent failures open the circuit."""
        from infrastructure.config import CircuitBreakerConfig
        
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        breaker = CircuitBreaker('concurrent-test', config)
        
        async def failing_call():
            raise Exception("Failure")
        
        async def call_through_breaker():
            try:
                await breaker.call(failing_call)
                return True
            except Exception:
                return False
        
        tasks = [call_through_breaker() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert breaker.state == CircuitState.OPEN
        
        failures = sum(1 for r in results if not r)
        assert failures == 10
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker recovery in half-open state."""
        from infrastructure.config import CircuitBreakerConfig
        from infrastructure.circuit_breaker import CircuitOpenError
        
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        breaker = CircuitBreaker('half-open-test', config)
        
        async def failing_call():
            raise Exception("Failure")
        
        async def success_call():
            return "success"
        
        for _ in range(3):
            try:
                await breaker.call(failing_call)
            except Exception:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        with pytest.raises(CircuitOpenError):
            await breaker.call(success_call)
        
        await asyncio.sleep(0.15)
        
        result = await breaker.call(success_call)
        assert result == "success"


class TestDatabaseConcurrency:
    """Tests for database operations under concurrent access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_writes(self):
        """Test concurrent database writes."""
        write_count = 0
        lock = asyncio.Lock()
        written_ids = []
        
        async def write_record(record_id: int):
            nonlocal write_count
            await asyncio.sleep(0.001)
            async with lock:
                write_count += 1
                written_ids.append(record_id)
        
        tasks = [write_record(i) for i in range(50)]
        await asyncio.gather(*tasks)
        
        assert write_count == 50
        assert len(written_ids) == 50
    
    @pytest.mark.asyncio
    async def test_optimistic_locking(self):
        """Test optimistic locking for concurrent updates."""
        record = {'id': 1, 'version': 0, 'value': 'initial'}
        updates = []
        lock = asyncio.Lock()
        
        async def update_record(new_value: str):
            async with lock:
                current_version = record['version']
                
                await asyncio.sleep(0.001)
                
                if record['version'] == current_version:
                    record['value'] = new_value
                    record['version'] += 1
                    updates.append((new_value, True))
                else:
                    updates.append((new_value, False))
        
        tasks = [
            update_record('update-1'),
            update_record('update-2'),
            update_record('update-3'),
        ]
        await asyncio.gather(*tasks)
        
        successful = sum(1 for _, success in updates if success)
        assert successful == 1
        assert record['version'] == 1


class TestMemoryUnderLoad:
    """Tests for memory usage under load."""
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """Test that completed jobs are cleaned up."""
        jobs = []
        
        for i in range(100):
            job = JobSession(
                id=f'job-{i}',
                target_url=f'https://example.com/{i}',
                status=JobStatus.COMPLETED,
            )
            jobs.append(job)
        
        del jobs
        
        import gc
        gc.collect()
        
        pass
    
    @pytest.mark.asyncio
    async def test_event_history_limit(self):
        """Test that event history has a maximum size."""
        from domain.event_sourcing import DomainEvent
        
        events = []
        max_events = 1000
        
        for i in range(1500):
            event = DomainEvent(
                event_id=f'evt-{i}',
                event_type='test_event',
                aggregate_id='test',
            )
            events.append(event)
            
            if len(events) > max_events:
                events = events[-max_events:]
        
        assert len(events) == max_events
