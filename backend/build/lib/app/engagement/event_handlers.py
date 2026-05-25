from app.shared.events.decorators import subscribe_to
from app.shared.events.event_bus import DomainEvent

@subscribe_to("NewsletterSubscribed")
async def on_newsletter_subscribed(event: DomainEvent) -> None: pass

@subscribe_to("NewsletterUnsubscribed")
async def on_newsletter_unsubscribed(event: DomainEvent) -> None: pass
