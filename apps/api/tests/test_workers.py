"""Worker layer tests — in-memory queue + bus, no external deps."""

from app.workers.events import MemoryBus
from app.workers.models import Task, TaskPayload
from app.workers.queue import MemoryQueue
from app.workers.worker import Worker


def _worker(queue, bus, handlers, **kw):
    return Worker(queue, bus, handlers, **kw)


def test_happy_path_task_success():
    queue = MemoryQueue()
    bus = MemoryBus()
    seen = {}

    def handler(task):
        seen["ran"] = True
        return {"ok": True}

    worker = _worker(queue, bus, {"research": handler})
    queue.enqueue(Task(kind=TaskPayload.RESEARCH, payload={"url": "https://x.com"}))
    worker.drain()

    assert seen["ran"]
    assert worker.stats.succeeded == 1
    assert worker.stats.processed == 1
    assert len(bus.by_type("worker.task_success")) == 1
    assert bus.events[0].payload["handler"] == "handler"


def test_retry_then_success():
    queue = MemoryQueue()
    bus = MemoryBus()
    attempts = {"n": 0}

    def flaky(task):
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise RuntimeError("transient")
        return {"done": True}

    worker = _worker(queue, bus, {"research": flaky})
    queue.enqueue(Task(kind=TaskPayload.RESEARCH))
    worker.drain()

    assert attempts["n"] == 2
    assert worker.stats.succeeded == 1
    assert worker.stats.failed == 1  # first attempt failed, then requeued
    assert len(bus.by_type("worker.task_success")) == 1
    assert len(bus.by_type("worker.task_failed")) == 1
    # retried task's final result reports the final attempt count
    final = bus.by_type("worker.task_success")[0]
    assert final.payload["attempts"] == 2


def test_dead_letter_after_max_attempts():
    queue = MemoryQueue()
    bus = MemoryBus()

    def always_fail(task):
        raise ValueError("permanent")

    worker = _worker(queue, bus, {"research": always_fail})
    queue.enqueue(Task(kind=TaskPayload.RESEARCH, max_attempts=2))
    worker.drain()

    assert worker.stats.dead_lettered == 1
    assert worker.stats.processed == 2  # attempt 1 fails+requeues, attempt 2 dead-letters
    failed_events = bus.by_type("worker.task_failed")
    assert len(failed_events) == 2  # first attempt + final dead-letter
    assert failed_events[-1].payload["dead_lettered"] is True


def test_unknown_handler_dead_letters():
    queue = MemoryQueue()
    bus = MemoryBus()
    worker = _worker(queue, bus, {})  # no handlers
    queue.enqueue(Task(kind=TaskPayload.RESEARCH))
    worker.drain()

    assert worker.stats.dead_lettered == 1
    failed = bus.by_type("worker.task_failed")[0]
    assert "no handler" in failed.payload["error"]


def test_empty_queue_process_once_returns_none():
    worker = _worker(MemoryQueue(), MemoryBus(), {})
    assert worker.process_once(0.0) is None


def test_queue_order_fifo():
    queue = MemoryQueue()
    order = []
    bus = MemoryBus()

    def handler(task):
        order.append(task.id)
        return {}

    worker = _worker(queue, bus, {"research": handler})
    a, b = Task(kind=TaskPayload.RESEARCH), Task(kind=TaskPayload.RESEARCH)
    queue.enqueue(a)
    queue.enqueue(b)
    worker.drain()

    assert order == [a.id, b.id]


def test_memory_queue_requeue_and_size():
    queue = MemoryQueue()
    t = Task(kind=TaskPayload.RESEARCH)
    queue.enqueue(t)
    claimed = queue.dequeue("w1", 0.0)
    assert claimed.id == t.id
    assert queue.inflight_count() == 1
    queue.requeue(t)
    assert queue.inflight_count() == 0
    assert queue.size() == 1
