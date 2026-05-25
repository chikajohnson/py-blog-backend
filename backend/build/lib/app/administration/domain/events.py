from app.shared.events.event_bus import DomainEvent

def settings_updated(updated_by: str, keys_changed: list[str]) -> DomainEvent:
    return DomainEvent(event_type="SettingsUpdated", payload={"updated_by": updated_by, "keys_changed": keys_changed}, source="administration")
