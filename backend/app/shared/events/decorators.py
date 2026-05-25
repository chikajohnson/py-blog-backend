from app.shared.events.event_bus import event_bus, EventHandler


def subscribe_to(event_type: str):
    def decorator(func: EventHandler) -> EventHandler:
        event_bus.subscribe(event_type, func)
        return func
    return decorator
