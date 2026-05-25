from app.shared.events.event_bus import DomainEvent

def article_created(article_id: str, author_id: str, title: str, status: str) -> DomainEvent:
    return DomainEvent(event_type="ArticleCreated", payload={"article_id": article_id, "author_id": author_id, "title": title, "status": status}, source="content")

def article_updated(article_id: str, author_id: str, changed_fields: list[str]) -> DomainEvent:
    return DomainEvent(event_type="ArticleUpdated", payload={"article_id": article_id, "author_id": author_id, "changed_fields": changed_fields}, source="content")

def article_published(article_id: str, author_id: str, title: str, published_at: str) -> DomainEvent:
    return DomainEvent(event_type="ArticlePublished", payload={"article_id": article_id, "author_id": author_id, "title": title, "published_at": published_at}, source="content")

def article_deleted(article_id: str, deleted_by: str) -> DomainEvent:
    return DomainEvent(event_type="ArticleDeleted", payload={"article_id": article_id, "deleted_by": deleted_by}, source="content")

def article_viewed(article_id: str, fingerprint: str, referrer: str = "") -> DomainEvent:
    return DomainEvent(event_type="ArticleViewed", payload={"article_id": article_id, "fingerprint": fingerprint, "referrer": referrer}, source="content")

def category_created(category_id: str, name: str) -> DomainEvent:
    return DomainEvent(event_type="CategoryCreated", payload={"category_id": category_id, "name": name}, source="content")

def category_updated(category_id: str, changed_fields: list[str]) -> DomainEvent:
    return DomainEvent(event_type="CategoryUpdated", payload={"category_id": category_id, "changed_fields": changed_fields}, source="content")

def category_deleted(category_id: str) -> DomainEvent:
    return DomainEvent(event_type="CategoryDeleted", payload={"category_id": category_id}, source="content")

def tag_created(tag_id: str, name: str) -> DomainEvent:
    return DomainEvent(event_type="TagCreated", payload={"tag_id": tag_id, "name": name}, source="content")

def tag_deleted(tag_id: str) -> DomainEvent:
    return DomainEvent(event_type="TagDeleted", payload={"tag_id": tag_id}, source="content")
