from typing import Any, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = ""


EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(event))
            except Exception:
                logger.exception("Event handler %s failed for %s", handler.__name__, event.event_type)


event_bus = EventBus()
