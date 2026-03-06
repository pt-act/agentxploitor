"""
Redis Job Queue

Distributed job queue implementation using Redis.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from models import JobSession, JobStatus
from exceptions import AgentError, JobStateError
from infrastructure.redis_pool import RedisPool, get_redis_pool

logger = logging.getLogger(__name__)


class QueuePriority(int, Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class RedisJobQueue:
    """
    Distributed job queue using Redis.
    
    Features:
    - Atomic enqueue/dequeue operations
    - Priority-based ordering
    - Job TTL and cleanup
    - Pub/Sub for job events
    - Idempotent operations
    """
    
    KEY_PREFIX = "agentxploitor:jobs"
    QUEUE_KEY = f"{KEY_PREFIX}:queue"
    JOBS_KEY = f"{KEY_PREFIX}:data"
    PROCESSING_KEY = f"{KEY_PREFIX}:processing"
    EVENTS_CHANNEL = f"{KEY_PREFIX}:events"
    
    def __init__(
        self,
        pool: Optional[RedisPool] = None,
        job_ttl: int = 86400 * 7,  # 7 days
        processing_timeout: int = 3600,  # 1 hour
    ):
        self._pool = pool
        self._job_ttl = job_ttl
        self._processing_timeout = processing_timeout
        self._local_cache: Dict[str, JobSession] = {}
    
    @property
    def pool(self) -> RedisPool:
        if self._pool is None:
            self._pool = get_redis_pool()
        return self._pool
    
    async def enqueue(
        self,
        job: JobSession,
        priority: QueuePriority = QueuePriority.NORMAL
    ) -> None:
        """
        Add job to queue with priority.
        
        Uses Redis transaction for atomicity.
        """
        client = self.pool.get_client()
        
        job_key = f"{self.JOBS_KEY}:{job.id}"
        
        job_data = json.dumps(job.to_dict())
        
        async with client.pipeline() as pipe:
            exists = await client.exists(job_key)
            if exists:
                logger.warning(f"Job {job.id} already exists, updating")
            
            score = self._calculate_score(priority)
            
            await (
                pipe.set(job_key, job_data, ex=self._job_ttl)
                .zadd(self.QUEUE_KEY, {job.id: score})
                .execute()
            )
        
        self._local_cache[job.id] = job
        
        await self._publish_event('job_enqueued', {'job_id': job.id, 'priority': priority.value})
        
        logger.info(f"Enqueued job {job.id} with priority {priority.name}")
    
    async def dequeue(
        self,
        timeout: float = 5.0,
        worker_id: Optional[str] = None
    ) -> Optional[JobSession]:
        """
        Get next job from queue atomically.
        
        Moves job from queue to processing set.
        """
        client = self.pool.get_client()
        
        try:
            result = await client.zpopmin(self.QUEUE_KEY, count=1)
            
            if not result:
                return None
            
            job_id = result[0][0]
            
            job_key = f"{self.JOBS_KEY}:{job_id}"
            job_data = await client.get(job_key)
            
            if not job_data:
                logger.warning(f"Job {job_id} data not found, skipping")
                return None
            
            data = json.loads(job_data)
            job = self._reconstruct_job(data)
            
            processing_key = f"{self.PROCESSING_KEY}:{job_id}"
            processing_data = json.dumps({
                'worker_id': worker_id,
                'started_at': datetime.utcnow().isoformat(),
            })
            await client.set(processing_key, processing_data, ex=self._processing_timeout)
            
            self._local_cache[job.id] = job
            
            await self._publish_event('job_dequeued', {
                'job_id': job.id,
                'worker_id': worker_id,
            })
            
            logger.info(f"Dequeued job {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
    
    async def get(self, job_id: str) -> Optional[JobSession]:
        """Get job by ID."""
        if job_id in self._local_cache:
            return self._local_cache[job_id]
        
        client = self.pool.get_client()
        job_key = f"{self.JOBS_KEY}:{job_id}"
        
        job_data = await client.get(job_key)
        if not job_data:
            return None
        
        data = json.loads(job_data)
        job = self._reconstruct_job(data)
        self._local_cache[job.id] = job
        
        return job
    
    async def update(self, job: JobSession) -> None:
        """Update job in Redis."""
        client = self.pool.get_client()
        job_key = f"{self.JOBS_KEY}:{job.id}"
        
        job_data = json.dumps(job.to_dict())
        await client.set(job_key, job_data, ex=self._job_ttl)
        
        self._local_cache[job.id] = job
        
        await self._publish_event('job_updated', {
            'job_id': job.id,
            'status': job.status.value,
        })
    
    async def complete(self, job_id: str) -> None:
        """Mark job as complete and remove from processing."""
        client = self.pool.get_client()
        
        processing_key = f"{self.PROCESSING_KEY}:{job_id}"
        await client.delete(processing_key)
        
        job = await self.get(job_id)
        if job:
            await self._publish_event('job_completed', {'job_id': job_id})
        
        logger.info(f"Job {job_id} completed")
    
    async def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed and optionally requeue."""
        client = self.pool.get_client()
        
        processing_key = f"{self.PROCESSING_KEY}:{job_id}"
        await client.delete(processing_key)
        
        job = await self.get(job_id)
        if job:
            job.error = error
            job.transition_to(JobStatus.FAILED, error)
            await self.update(job)
        
        await self._publish_event('job_failed', {
            'job_id': job_id,
            'error': error,
        })
        
        logger.error(f"Job {job_id} failed: {error}")
    
    async def requeue_stale(self, max_age: int = 3600) -> int:
        """
        Requeue jobs that have been processing too long.
        
        Returns count of requeued jobs.
        """
        client = self.pool.get_client()
        
        pattern = f"{self.PROCESSING_KEY}:*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        requeued = 0
        for key in keys:
            ttl = await client.ttl(key)
            if ttl <= 0:
                job_id = key.split(':')[-1]
                
                job = await self.get(job_id)
                if job:
                    await self.enqueue(job, priority=QueuePriority.HIGH)
                    await client.delete(key)
                    requeued += 1
                    logger.warning(f"Requeued stale job {job_id}")
        
        return requeued
    
    async def size(self) -> int:
        """Get queue size."""
        client = self.pool.get_client()
        return await client.zcard(self.QUEUE_KEY)
    
    async def processing_count(self) -> int:
        """Get count of jobs being processed."""
        client = self.pool.get_client()
        pattern = f"{self.PROCESSING_KEY}:*"
        count = 0
        async for _ in client.scan_iter(match=pattern):
            count += 1
        return count
    
    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[JobSession]:
        """List jobs, optionally filtered by status."""
        client = self.pool.get_client()
        
        pattern = f"{self.JOBS_KEY}:*"
        jobs = []
        
        async for key in client.scan_iter(match=pattern, count=limit):
            job_data = await client.get(key)
            if job_data:
                data = json.loads(job_data)
                job = self._reconstruct_job(data)
                
                if status is None or job.status == status:
                    jobs.append(job)
                    
                    if len(jobs) >= limit:
                        break
        
        return jobs
    
    async def clear_completed(self, older_than: int = 86400) -> int:
        """Clear completed jobs older than threshold."""
        client = self.pool.get_client()
        
        jobs = await self.list_jobs(status=JobStatus.COMPLETED)
        cleared = 0
        
        cutoff = datetime.utcnow().timestamp() - older_than
        
        for job in jobs:
            job_time = datetime.fromisoformat(job.updated_at).timestamp()
            if job_time < cutoff:
                job_key = f"{self.JOBS_KEY}:{job.id}"
                await client.delete(job_key)
                self._local_cache.pop(job.id, None)
                cleared += 1
        
        return cleared
    
    def _calculate_score(self, priority: QueuePriority) -> float:
        """Calculate queue score (lower = higher priority)."""
        return -priority.value + datetime.utcnow().timestamp() * 0.0001
    
    def _reconstruct_job(self, data: Dict[str, Any]) -> JobSession:
        """Reconstruct JobSession from dict."""
        return JobSession(
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
            error=data.get('error'),
        )
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish event to Redis channel."""
        try:
            client = self.pool.get_client()
            event = json.dumps({
                'type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
            })
            await client.publish(self.EVENTS_CHANNEL, event)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")


def create_redis_queue(pool: Optional[RedisPool] = None) -> RedisJobQueue:
    """Factory function for Redis job queue."""
    return RedisJobQueue(pool=pool)
