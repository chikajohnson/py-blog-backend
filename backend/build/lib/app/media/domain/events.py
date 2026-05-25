from app.shared.events.event_bus import DomainEvent

def media_uploaded(media_id: str, uploaded_by: str, filename: str, size: int) -> DomainEvent:
    return DomainEvent(event_type="MediaUploaded", payload={"media_id": media_id, "uploaded_by": uploaded_by, "filename": filename, "size": size}, source="media")

def media_deleted(media_id: str, deleted_by: str) -> DomainEvent:
    return DomainEvent(event_type="MediaDeleted", payload={"media_id": media_id, "deleted_by": deleted_by}, source="media")
