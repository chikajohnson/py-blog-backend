from app.shared.events.decorators import subscribe_to
from app.shared.events.event_bus import DomainEvent

@subscribe_to("MediaUploaded")
async def on_media_uploaded(event: DomainEvent) -> None: pass

@subscribe_to("MediaDeleted")
async def on_media_deleted(event: DomainEvent) -> None: pass
