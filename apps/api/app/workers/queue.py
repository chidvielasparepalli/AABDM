"""Task queue: protocol + in-memory implementation (mock).

The protocol is the contract a real broker (Redis/arq) implements in M6.
MemoryQueue is FIFO with per-worker claim (dequeue moves a task to in-flight
so a crash mid-execution can retry it — the durability seam).
"""

import threading
import time
from typing import Protocol

from .models import Task


class TaskQueue(Protocol):
    def enqueue(self, task: Task) -> None:
        """Add a task to the queue."""
        ...

    def dequeue(self, worker_id: str, timeout_s: float = 0.5) -> Task | None:
        """Claim the next task for a worker. Returns None when empty/blocked."""
        ...

    def requeue(self, task: Task) -> None:
        """Return a failed task to the queue for retry."""
        ...


class MemoryQueue:
    """Thread-safe in-memory FIFO. Mock — no durability across restarts."""

    def __init__(self) -> None:
        self._ready: list[Task] = []
        self._inflight: dict[str, Task] = {}  # task_id → claimed task
        self._lock = threading.Lock()

    def enqueue(self, task: Task) -> None:
        with self._lock:
            self._ready.append(task)

    def dequeue(self, worker_id: str, timeout_s: float = 0.5) -> Task | None:
        deadline = time.monotonic() + timeout_s
        while True:
            with self._lock:
                if self._ready:
                    task = self._ready.pop(0)
                    self._inflight[task.id] = task
                    return task
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.01)

    def requeue(self, task: Task) -> None:
        with self._lock:
            self._inflight.pop(task.id, None)
            self._ready.append(task)

    def size(self) -> int:
        with self._lock:
            return len(self._ready)

    def inflight_count(self) -> int:
        with self._lock:
            return len(self._inflight)
