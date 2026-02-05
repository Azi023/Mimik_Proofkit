"""Background worker for processing audit jobs.

This module provides a simple worker implementation for processing
audit jobs. For production use, consider using a proper job queue
like Celery, ARQ, or Redis Queue.
"""

import asyncio
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import queue
import threading

from proofkit.utils.logger import logger


@dataclass
class Job:
    """Represents a background job."""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    created_at: datetime
    status: str = "pending"
    result: Optional[any] = None
    error: Optional[str] = None


class SimpleJobQueue:
    """
    Simple in-memory job queue.

    This is suitable for development and single-instance deployments.
    For production with multiple workers, use Redis-based queue.
    """

    def __init__(self, max_workers: int = 2):
        self.queue: queue.Queue = queue.Queue()
        self.jobs: dict[str, Job] = {}
        self.max_workers = max_workers
        self._workers: list[threading.Thread] = []
        self._running = False

    def enqueue(
        self,
        job_id: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Job:
        """
        Add a job to the queue.

        Args:
            job_id: Unique job identifier
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Job object
        """
        job = Job(
            id=job_id,
            func=func,
            args=args,
            kwargs=kwargs,
            created_at=datetime.utcnow(),
        )
        self.jobs[job_id] = job
        self.queue.put(job)
        logger.debug(f"Job {job_id} enqueued")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def start_workers(self):
        """Start worker threads."""
        if self._running:
            return

        self._running = True
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"job-worker-{i}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

        logger.info(f"Started {self.max_workers} job workers")

    def stop_workers(self):
        """Stop worker threads."""
        self._running = False
        # Add sentinel values to wake up workers
        for _ in self._workers:
            self.queue.put(None)

    def _worker_loop(self):
        """Worker loop that processes jobs from queue."""
        while self._running:
            try:
                job = self.queue.get(timeout=1)
                if job is None:
                    continue

                self._process_job(job)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def _process_job(self, job: Job):
        """Process a single job."""
        logger.info(f"Processing job {job.id}")
        job.status = "processing"

        try:
            result = job.func(*job.args, **job.kwargs)
            job.result = result
            job.status = "complete"
            logger.info(f"Job {job.id} complete")

        except Exception as e:
            job.error = str(e)
            job.status = "failed"
            logger.error(f"Job {job.id} failed: {e}")


# Global job queue instance
_job_queue: Optional[SimpleJobQueue] = None


def get_job_queue() -> SimpleJobQueue:
    """Get or create the global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = SimpleJobQueue()
        _job_queue.start_workers()
    return _job_queue


def shutdown_job_queue():
    """Shutdown the global job queue."""
    global _job_queue
    if _job_queue:
        _job_queue.stop_workers()
        _job_queue = None
