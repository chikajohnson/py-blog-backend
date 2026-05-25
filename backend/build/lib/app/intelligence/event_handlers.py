from app.shared.events.decorators import subscribe_to
from app.shared.events.event_bus import DomainEvent

@subscribe_to("AIMessageSent")
async def on_ai_message_sent(event: DomainEvent) -> None: pass
