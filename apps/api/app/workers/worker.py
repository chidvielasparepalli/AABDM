"""Worker: claims tasks, executes handlers, records results, emits events.

Retry policy: a handler failure requeues the task up to max_attempts (with
backoff via the requeue path); exhaustion dead-letters the task and emits a
failed event. Deadline bounds a single execution so a hung handler can't
block the worker forever.
"""

import threading
import time
from dataclasses import dataclass

from .events import EventBus, task_result_event
from .models import Task, TaskHandler, TaskResult, TaskStatus
from .queue import TaskQueue


@dataclass
class WorkerStats:
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    dead_lettered: int = 0


class Worker:
    def __init__(
        self,
        queue: TaskQueue,
        bus: EventBus,
        handlers: dict[str, TaskHandler],
        worker_id: str | None = None,
        deadline_s: float = 60.0,
    ):
        self.queue = queue
        self.bus = bus
        self.handlers = handlers
        self.worker_id = worker_id or f"worker-{threading.get_ident()}"
        self.deadline_s = deadline_s
        self.stats = WorkerStats()
        self._running = False

    def _run_one(self, task: Task) -> TaskResult:
        handler = self.handlers.get(task.kind.value)
        started = time.monotonic()
        task.attempts += 1  # this execution
        try:
            if handler is None:
                raise ValueError(f"no handler for task kind '{task.kind}'")
            data = handler(task)
            if time.monotonic() - started > self.deadline_s:
                raise TimeoutError(f"handler exceeded {self.deadline_s}s deadline")
            self.stats.succeeded += 1
            self.stats.processed += 1
            return TaskResult(task.id, TaskStatus.SUCCESS, handler.__name__, attempts=task.attempts, data=data)
        except Exception as exc:  # noqa: BLE001 — a failing handler must not kill the worker
            self.stats.processed += 1
            if task.attempts >= task.max_attempts:
                self.stats.dead_lettered += 1
                return TaskResult(
                    task.id, TaskStatus.DEAD_LETTERED, handler.__name__ if handler else "unknown",
                    error=str(exc), attempts=task.attempts,
                )
            self.stats.failed += 1
            return TaskResult(
                task.id, TaskStatus.FAILED, handler.__name__ if handler else "unknown",
                error=str(exc), attempts=task.attempts,
            )

    def process_once(self, timeout_s: float = 0.5) -> Task | None:
        """Claim and execute one task. Returns the task or None if queue empty."""
        task = self.queue.dequeue(self.worker_id, timeout_s)
        if task is None:
            return None
        result = self._run_one(task)
        if result.status == TaskStatus.FAILED:
            self.queue.requeue(task)
        self.bus.publish(task_result_event(result))
        return task

    def run_forever(self, poll_s: float = 0.2) -> None:
        """Blocking loop. Runs until stop() is called."""
        self._running = True
        while self._running:
            self.process_once(poll_s)

    def stop(self) -> None:
        self._running = False

    def drain(self, poll_s: float = 0.0) -> int:
        """Process until the queue is empty. Returns tasks processed."""
        count = 0
        while self.process_once(poll_s) is not None:
            count += 1
        return count
