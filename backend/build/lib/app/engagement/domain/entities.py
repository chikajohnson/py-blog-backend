from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Subscriber:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    is_active: bool = True
    subscribed_at: str | None = None
    unsubscribed_at: str | None = None
    source: str = "website"

@dataclass
class ArticleView:
    id: UUID = field(default_factory=uuid4)
    article_id: UUID | None = None
    visitor_fingerprint: str = ""
    referrer: str = ""
    read_duration_sec: int = 0
    viewed_at: str | None = None
