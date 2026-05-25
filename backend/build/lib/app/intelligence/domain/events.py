from app.shared.events.event_bus import DomainEvent

def ai_message_sent(conversation_id: str, user_id: str, tokens_used: int) -> DomainEvent:
    return DomainEvent(event_type="AIMessageSent", payload={"conversation_id": conversation_id, "user_id": user_id, "tokens_used": tokens_used}, source="intelligence")
