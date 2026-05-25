from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Media:
    id: UUID = field(default_factory=uuid4)
    filename: str = ""
    original_name: str = ""
    mime_type: str = ""
    file_size: int = 0
    width: int | None = None
    height: int | None = None
    url: str = ""
    alt_text: str = ""
    uploaded_by: UUID | None = None
    created_at: str | None = None
