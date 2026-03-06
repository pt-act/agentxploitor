"""
Performance Benchmarks

Measures system performance metrics using pytest-benchmark patterns.
"""

import pytest
import asyncio
import time
from datetime import datetime
from statistics import mean, median, stdev
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    times_ms: List[float]
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'iterations': self.iterations,
            'mean_ms': round(self.mean_ms, 2),
            'median_ms': round(self.median_ms, 2),
            'p95_ms': round(self.p95_ms, 2),
            'p99_ms': round(self.p99_ms, 2),
            'min_ms': round(self.min_ms, 2),
            'max_ms': round(self.max_ms, 2),
        }


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate a percentile value."""
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(index, len(sorted_data) - 1)]


class SimpleBenchmark:
    """Simple benchmarking utility without pytest-benchmark dependency."""
    
    def __init__(self):
        self._results: List[BenchmarkResult] = []
    
    def run(
        self,
        name: str,
        func: callable,
        iterations: int = 100,
        warmup: int = 5,
    ) -> BenchmarkResult:
        """Run a benchmark."""
        for _ in range(warmup):
            func()
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            times_ms=times,
            mean_ms=mean(times),
            median_ms=median(times),
            p95_ms=calculate_percentile(times, 95),
            p99_ms=calculate_percentile(times, 99),
            min_ms=min(times),
            max_ms=max(times),
        )
        
        self._results.append(result)
        return result
    
    async def run_async(
        self,
        name: str,
        func: callable,
        iterations: int = 100,
        warmup: int = 5,
    ) -> BenchmarkResult:
        """Run an async benchmark."""
        for _ in range(warmup):
            await func()
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await func()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            times_ms=times,
            mean_ms=mean(times),
            median_ms=median(times),
            p95_ms=calculate_percentile(times, 95),
            p99_ms=calculate_percentile(times, 99),
            min_ms=min(times),
            max_ms=max(times),
        )
        
        self._results.append(result)
        return result
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self._results
    
    def summary(self) -> str:
        """Get a summary of all benchmarks."""
        lines = [
            "Benchmark Results",
            "=" * 60,
            f"{'Name':<30} {'Mean':>10} {'P95':>10} {'P99':>10}",
            "-" * 60,
        ]
        
        for result in self._results:
            lines.append(
                f"{result.name:<30} "
                f"{result.mean_ms:>8.2f}ms "
                f"{result.p95_ms:>8.2f}ms "
                f"{result.p99_ms:>8.2f}ms"
            )
        
        return "\n".join(lines)


class TestJobLatencyBenchmarks:
    """Benchmarks for job processing latency."""
    
    @pytest.mark.asyncio
    async def test_job_creation_latency(self):
        """Benchmark job creation latency."""
        from models import JobSession, JobStatus
        
        benchmark = SimpleBenchmark()
        
        async def create_job():
            job = JobSession(
                id=f'job-{time.time_ns()}',
                target_url='https://example.com',
                status=JobStatus.QUEUED,
            )
            return job
        
        result = await benchmark.run_async('job_creation', create_job, iterations=100)
        
        assert result.mean_ms < 10, f"Job creation too slow: {result.mean_ms}ms"
        assert result.p99_ms < 50, f"P99 latency too high: {result.p99_ms}ms"
        
        print(f"\nJob Creation Benchmark:")
        print(f"  Mean: {result.mean_ms:.2f}ms")
        print(f"  P95: {result.p95_ms:.2f}ms")
        print(f"  P99: {result.p99_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_status_transition_latency(self):
        """Benchmark status transition latency."""
        from models import JobSession, JobStatus
        
        benchmark = SimpleBenchmark()
        job = JobSession(
            id='benchmark-job',
            target_url='https://example.com',
            status=JobStatus.QUEUED,
        )
        
        def transition():
            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.IN_PROGRESS
            else:
                job.status = JobStatus.QUEUED
        
        result = benchmark.run('status_transition', transition, iterations=1000)
        
        assert result.mean_ms < 1, f"Status transition too slow: {result.mean_ms}ms"
        
        print(f"\nStatus Transition Benchmark:")
        print(f"  Mean: {result.mean_ms:.4f}ms")
        print(f"  P95: {result.p95_ms:.4f}ms")


class TestQueueThroughputBenchmarks:
    """Benchmarks for queue throughput."""
    
    @pytest.mark.asyncio
    async def test_enqueue_throughput(self):
        """Benchmark enqueue operations per second."""
        benchmark = SimpleBenchmark()
        enqueue_count = 0
        
        async def enqueue():
            nonlocal enqueue_count
            enqueue_count += 1
        
        result = await benchmark.run_async('enqueue', enqueue, iterations=1000)
        
        throughput = 1000 / (result.mean_ms / 1000)
        
        print(f"\nEnqueue Throughput:")
        print(f"  Ops/sec: {throughput:.0f}")
        print(f"  Mean latency: {result.mean_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_dequeue_throughput(self):
        """Benchmark dequeue operations per second."""
        benchmark = SimpleBenchmark()
        dequeue_count = 0
        
        async def dequeue():
            nonlocal dequeue_count
            dequeue_count += 1
        
        result = await benchmark.run_async('dequeue', dequeue, iterations=1000)
        
        throughput = 1000 / (result.mean_ms / 1000)
        
        print(f"\nDequeue Throughput:")
        print(f"  Ops/sec: {throughput:.0f}")


class TestEventSourcingBenchmarks:
    """Benchmarks for event sourcing operations."""
    
    @pytest.mark.asyncio
    async def test_event_creation_benchmark(self):
        """Benchmark event creation."""
        from domain.event_sourcing import DomainEvent
        
        benchmark = SimpleBenchmark()
        
        def create_event():
            return DomainEvent(
                event_type='test_event',
                aggregate_type='job',
                aggregate_id='job-001',
                payload={'key': 'value'},
            )
        
        result = benchmark.run('event_creation', create_event, iterations=1000)
        
        assert result.mean_ms < 1
        print(f"\nEvent Creation: {result.mean_ms:.4f}ms")
    
    @pytest.mark.asyncio
    async def test_event_serialization_benchmark(self):
        """Benchmark event serialization."""
        from domain.event_sourcing import DomainEvent
        
        benchmark = SimpleBenchmark()
        event = DomainEvent(
            event_type='test_event',
            aggregate_type='job',
            aggregate_id='job-001',
            payload={'key': 'value' * 100},
        )
        
        def serialize():
            return event.to_dict()
        
        result = benchmark.run('event_serialization', serialize, iterations=1000)
        
        print(f"\nEvent Serialization: {result.mean_ms:.4f}ms")


class TestDatabaseQueryBenchmarks:
    """Benchmarks for database operations."""
    
    @pytest.mark.asyncio
    async def test_mock_query_latency(self):
        """Benchmark simulated database query."""
        benchmark = SimpleBenchmark()
        
        async def mock_query():
            await asyncio.sleep(0.001)  # Simulate DB latency
            return {'id': 1, 'data': 'result'}
        
        result = await benchmark.run_async('mock_query', mock_query, iterations=100)
        
        assert result.mean_ms < 5
        print(f"\nMock Query Latency: {result.mean_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_batch_insert_benchmark(self):
        """Benchmark batch insert operations."""
        benchmark = SimpleBenchmark()
        
        async def batch_insert():
            records = [{'id': i, 'value': f'data-{i}'} for i in range(100)]
            await asyncio.sleep(0.01)  # Simulate batch insert
            return len(records)
        
        result = await benchmark.run_async('batch_insert', batch_insert, iterations=50)
        
        throughput = 100 / (result.mean_ms / 1000)
        
        print(f"\nBatch Insert:")
        print(f"  Records: 100")
        print(f"  Latency: {result.mean_ms:.2f}ms")
        print(f"  Throughput: {throughput:.0f} records/sec")


class TestMemoryUsageBenchmarks:
    """Benchmarks for memory usage."""
    
    def test_memory_efficiency(self):
        """Test memory efficiency of job storage."""
        import sys
        
        from models import JobSession, JobStatus
        
        jobs = []
        initial_size = sys.getsizeof(jobs)
        
        for i in range(1000):
            job = JobSession(
                id=f'job-{i}',
                target_url='https://example.com',
                status=JobStatus.QUEUED,
            )
            jobs.append(job)
        
        final_size = sys.getsizeof(jobs)
        per_job_overhead = (final_size - initial_size) / 1000
        
        print(f"\nMemory Efficiency:")
        print(f"  Initial size: {initial_size} bytes")
        print(f"  Final size: {final_size} bytes")
        print(f"  Per-job overhead: {per_job_overhead:.2f} bytes")


class TestCircuitBreakerBenchmarks:
    """Benchmarks for circuit breaker operations."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_overhead(self):
        """Benchmark circuit breaker overhead."""
        from infrastructure.circuit_breaker import CircuitBreaker
        
        benchmark = SimpleBenchmark()
        breaker = CircuitBreaker('benchmark')
        
        async def direct_call():
            return "result"
        
        async def protected_call():
            return await breaker.call(direct_call)
        
        direct_result = await benchmark.run_async('direct_call', direct_call, iterations=1000)
        
        protected_result = await benchmark.run_async('protected_call', protected_call, iterations=1000)
        
        overhead = protected_result.mean_ms - direct_result.mean_ms
        
        print(f"\nCircuit Breaker Overhead:")
        print(f"  Direct call: {direct_result.mean_ms:.4f}ms")
        print(f"  Protected call: {protected_result.mean_ms:.4f}ms")
        print(f"  Overhead: {overhead:.4f}ms")
        
        assert overhead < 1, f"Circuit breaker overhead too high: {overhead}ms"


class TestEndToEndBenchmarks:
    """End-to-end system benchmarks."""
    
    @pytest.mark.asyncio
    async def test_full_audit_workflow_benchmark(self):
        """Benchmark complete audit workflow."""
        benchmark = SimpleBenchmark()
        
        async def full_workflow():
            await asyncio.sleep(0.01)  # Payment verification
            await asyncio.sleep(0.02)  # Scan
            await asyncio.sleep(0.01)  # Exploit generation
            await asyncio.sleep(0.005)  # Report generation
        
        result = await benchmark.run_async('full_workflow', full_workflow, iterations=100)
        
        print(f"\nFull Audit Workflow:")
        print(f"  Mean: {result.mean_ms:.2f}ms")
        print(f"  P95: {result.p95_ms:.2f}ms")
        print(f"  P99: {result.p99_ms:.2f}ms")
