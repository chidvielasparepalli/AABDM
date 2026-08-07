"""Event bus — in-memory, M3 durability later.

Protocol: producers call `bus.publish(event)`; subscribers register async
callbacks on a topic. Handlers run isolated — one exception doesn't
block other handlers on the same event. Ordering is per-topic FIFO.

M3: swap for a real broker (Redis Streams/Kafka) behind the same interface.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable

from .schema import Event, EventType, topic_for

logger = logging.getLogger(__name__)

EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        # topic -> list of handlers
        self._subscribers: dict[str, list[Callable[[Event], Awaitable[None]]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Register a handler for an exact event type (e.g. 'research.completed')."""
        self._subscribers[event_type].append(handler)

    def subscribe_topic(self, topic: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Register a handler for ALL events under a topic (e.g. 'call.*')."""
        self._subscribers[topic].append(handler)

    async def publish(self, event: Event) -> None:
        """Emit an event — run all exact-type handlers + topic handlers.

        Handlers run concurrently (asyncio.gather). One handler's exception
        is logged but doesn't cancel the others — isolation is the contract.
        """
        exact_handlers = self._subscribers.get(event.type, [])
        topic = topic_for(event.type)
        topic_handlers = self._subscribers.get(topic, [])
        all_handlers = exact_handlers + topic_handlers

        if not all_handlers:
            logger.debug("No subscribers for %s (org_id=%s, corr=%s)",
                         event.type, event.org_id, event.correlation_id[:8])
            return

        logger.info("Publishing %s (corr=%s, org=%s)",
                    event.type, event.correlation_id[:8], event.org_id)

        async def _run(h: Callable[[Event], Awaitable[None]]) -> None:
            try:
                await h(event)
            except Exception:  # noqa: BLE001 — isolate handler failures
                logger.exception("Handler failed for %s: %s", event.type, h)

        await asyncio.gather(*(_run(h) for h in all_handlers))

    def subscribers_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))


# Singleton bus — the single source of truth for the process.
bus = EventBus()