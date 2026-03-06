"""
AgentxploiTor Job Worker

Background worker for processing audit jobs from queue.
"""

import asyncio
import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Callable

from models import JobSession, JobStatus, AuditReport
from exceptions import AgentError, JobStateError


class JobQueue:
    """In-memory job queue with optional file persistence."""
    
    def __init__(self, persist_dir: Optional[Path] = None):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._jobs: Dict[str, JobSession] = {}
        self.persist_dir = persist_dir or Path(os.environ.get(
            'AGENTXPLOITOR_QUEUE_DIR',
            '/tmp/agentxploitor/queue'
        ))
        self.persist_dir.mkdir(parents=True, exist_ok=True)
    
    async def enqueue(self, job: JobSession) -> None:
        """Add job to queue."""
        self._jobs[job.id] = job
        await self._queue.put(job.id)
        await self._persist_job(job)
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[JobSession]:
        """Get next job from queue."""
        try:
            job_id = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            return self._jobs.get(job_id)
        except asyncio.TimeoutError:
            return None
    
    def get(self, job_id: str) -> Optional[JobSession]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def update(self, job: JobSession) -> None:
        """Update job in memory."""
        self._jobs[job.id] = job
    
    async def _persist_job(self, job: JobSession) -> None:
        """Persist job to file."""
        job_file = self.persist_dir / f"{job.id}.json"
        with open(job_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)
    
    def load_persisted(self) -> int:
        """Load persisted jobs back into memory. Returns count loaded."""
        count = 0
        for job_file in self.persist_dir.glob("job-*.json"):
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)
                job = JobSession(
                    id=data['id'],
                    target_url=data['target_url'],
                    status=JobStatus(data['status']),
                    created_at=data['created_at'],
                    updated_at=data['updated_at'],
                    state_history=data.get('state_history', []),
                    payment_tx_hash=data.get('payment_tx_hash'),
                    payment_amount=data.get('payment_amount'),
                    wallet_address=data.get('wallet_address'),
                    findings_count=data.get('findings_count'),
                    report_path=data.get('report_path'),
                    error=data.get('error')
                )
                self._jobs[job.id] = job
                if job.status in [JobStatus.QUEUED, JobStatus.PAYMENT_VERIFIED]:
                    self._queue.put_nowait(job.id)
                count += 1
            except Exception as e:
                print(f"⚠️  Failed to load job {job_file}: {e}")
        return count


class JobWorker:
    """Background worker for processing audit jobs."""
    
    def __init__(
        self,
        queue: JobQueue,
        agent_factory: Callable[[], Any],
        max_concurrent: int = 1,
        retry_attempts: int = 3,
        retry_delay: float = 60.0
    ):
        self.queue = queue
        self.agent_factory = agent_factory
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self._running = False
        self._tasks: set = set()
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        print(f"🔄 Job worker started (max concurrent: {self.max_concurrent})")
        
        loaded = self.queue.load_persisted()
        if loaded > 0:
            print(f"📂 Loaded {loaded} persisted jobs")
        
        while self._running:
            try:
                job = await self.queue.dequeue(timeout=5.0)
                if job:
                    task = asyncio.create_task(self._process_job(job))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Worker error: {e}")
                await asyncio.sleep(1)
    
    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        print("🛑 Job worker stopping...")
    
    async def _process_job(self, job: JobSession) -> None:
        """Process a single job with retry logic."""
        async with self._semaphore:
            print(f"📋 Processing job {job.id}")
            
            try:
                job.transition_to(JobStatus.IN_PROGRESS, "Worker picked up job")
                await self.queue._persist_job(job)
                
                agent = self.agent_factory()
                
                report = await agent.run_audit(
                    target_url=job.target_url,
                    job_id=job.id
                )
                
                job.findings_count = report.summary
                job.report_path = str(agent.output_dir / f"report-{job.id}.json")
                job.transition_to(JobStatus.COMPLETED, "Audit completed successfully")
                
                print(f"✅ Job {job.id} completed")
                
            except AgentError as e:
                job.error = e.message
                job.transition_to(JobStatus.FAILED, e.message)
                print(f"❌ Job {job.id} failed: {e.message}")
                
                if e.recoverable and self.retry_attempts > 0:
                    print(f"🔄 Will retry job {job.id} in {self.retry_delay}s")
                    await asyncio.sleep(self.retry_delay)
                    job.transition_to(JobStatus.QUEUED, f"Retry scheduled (error was recoverable)")
                    
            except JobStateError as e:
                job.error = e.message
                print(f"⚠️  Job {job.id} state error: {e.message}")
                
            except Exception as e:
                job.error = str(e)
                job.transition_to(JobStatus.FAILED, str(e))
                print(f"❌ Job {job.id} unexpected error: {e}")
            
            finally:
                self.queue.update(job)
                await self.queue._persist_job(job)


class IdempotencyKeyManager:
    """Manage idempotency keys for deduplication."""
    
    def __init__(self, ttl_seconds: int = 86400):
        self._keys: Dict[str, float] = {}
        self._ttl = ttl_seconds
    
    def check(self, key: str) -> bool:
        """Check if key exists (returns True if duplicate)."""
        now = datetime.utcnow().timestamp()
        
        expired = [k for k, t in self._keys.items() if now - t > self._ttl]
        for k in expired:
            del self._keys[k]
        
        if key in self._keys:
            return True
        
        self._keys[key] = now
        return False
    
    def generate_key(self, target_url: str, wallet_address: str) -> str:
        """Generate idempotency key from inputs."""
        import hashlib
        data = f"{target_url}:{wallet_address}:{datetime.utcnow().strftime('%Y%m%d')}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class BackpressureHandler:
    """Handle backpressure for pipeline stages."""
    
    def __init__(
        self,
        max_queue_size: int = 100,
        throttle_delay: float = 0.1,
        max_concurrent: int = 10
    ):
        self.max_queue_size = max_queue_size
        self.throttle_delay = throttle_delay
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._current_load = 0
    
    async def acquire(self) -> bool:
        """Try to acquire a slot. Returns False if overloaded."""
        if self._current_load >= self.max_queue_size:
            await asyncio.sleep(self.throttle_delay)
            return False
        
        await self._semaphore.acquire()
        self._current_load += 1
        return True
    
    def release(self) -> None:
        """Release a slot."""
        self._semaphore.release()
        self._current_load = max(0, self._current_load - 1)
    
    @property
    def load(self) -> float:
        """Current load as percentage."""
        return self._current_load / self.max_queue_size


def create_worker() -> JobWorker:
    """Factory function to create a configured worker."""
    
    def agent_factory():
        from agentxploitor import AgentxploiTorAgent
        return AgentxploiTorAgent(browser_perception=True)
    
    queue = JobQueue()
    
    return JobWorker(
        queue=queue,
        agent_factory=agent_factory,
        max_concurrent=int(os.environ.get('WORKER_MAX_CONCURRENT', '1')),
        retry_attempts=int(os.environ.get('WORKER_RETRY_ATTEMPTS', '3')),
        retry_delay=float(os.environ.get('WORKER_RETRY_DELAY', '60.0'))
    )


async def run_worker():
    """CLI entry point for worker."""
    import sys
    
    worker = create_worker()
    
    def handle_signal(sig, frame):
        worker.stop()
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()
    
    print("👋 Worker shut down complete")


if __name__ == '__main__':
    asyncio.run(run_worker())
