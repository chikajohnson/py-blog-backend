from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Setting:
    id: UUID = field(default_factory=uuid4)
    key: str = ""
    value: dict = field(default_factory=dict)
    updated_by: UUID | None = None
    updated_at: str | None = None

@dataclass
class ActivityLogEntry:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    action: str = ""
    entity_type: str | None = None
    entity_id: UUID | None = None
    metadata: dict = field(default_factory=dict)
    ip_address: str | None = None
    created_at: str | None = None
