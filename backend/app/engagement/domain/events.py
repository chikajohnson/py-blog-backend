from app.shared.events.event_bus import DomainEvent

def newsletter_subscribed(subscriber_id: str, email: str, source: str = "website") -> DomainEvent:
    return DomainEvent(event_type="NewsletterSubscribed", payload={"subscriber_id": subscriber_id, "email": email, "source": source}, source="engagement")

def newsletter_unsubscribed(subscriber_id: str, email: str) -> DomainEvent:
    return DomainEvent(event_type="NewsletterUnsubscribed", payload={"subscriber_id": subscriber_id, "email": email}, source="engagement")
