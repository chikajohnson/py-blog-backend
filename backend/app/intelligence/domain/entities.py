from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Conversation:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    title: str = "New Chat"
    model: str = "gpt-4"
    created_at: str | None = None
    updated_at: str | None = None

@dataclass
class Message:
    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID | None = None
    role: str = "user"
    content: str = ""
    tokens_used: int = 0
    created_at: str | None = None
