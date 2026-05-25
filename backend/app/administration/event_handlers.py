from app.shared.events.event_bus import DomainEvent, event_bus
from app.shared.database import async_session
from app.administration.infrastructure.repositories import SQLAlchemyActivityLogRepository

# Map event types to action strings for the activity log
EVENT_ACTION_MAP: dict[str, str] = {
    "UserRegistered": "user.register",
    "UserLoggedIn": "user.login",
    "UserPasswordReset": "user.password_reset",
    "UserRoleChanged": "user.role_changed",
    "MediaUploaded": "media.upload",
    "MediaDeleted": "media.delete",
    "NewsletterSubscribed": "newsletter.subscribe",
    "NewsletterUnsubscribed": "newsletter.unsubscribe",
    "AIMessageSent": "ai.message_sent",
    "SettingsUpdated": "settings.update",
}


async def _log_event(event: DomainEvent) -> None:
    action = EVENT_ACTION_MAP.get(event.event_type, event.event_type.lower())
    payload = event.payload
    async with async_session() as session:
        repo = SQLAlchemyActivityLogRepository(session)
        await repo.log(
            {
                "user_id": payload.get("user_id")
                or payload.get("uploaded_by")
                or payload.get("deleted_by")
                or payload.get("updated_by")
                or payload.get("subscriber_id"),
                "action": action,
                "entity_type": event.source,
                "entity_id": payload.get("user_id")
                or payload.get("media_id")
                or payload.get("subscriber_id")
                or payload.get("conversation_id"),
                "metadata": payload,
            }
        )
        await session.commit()


# Register a single handler for all known event types
for _event_type in EVENT_ACTION_MAP:
    event_bus.subscribe(_event_type, _log_event)
