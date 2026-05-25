from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EDITOR = "editor"
    AUTHOR = "author"
    SUBSCRIBER = "subscriber"

    @property
    def level(self) -> int:
        return {"super_admin": 5, "admin": 4, "editor": 3, "author": 2, "subscriber": 1}.get(self.value, 0)


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    avatar_url: str | None = None
    bio: str = ""
    github_handle: str | None = None
    twitter_handle: str | None = None
    role: Role = Role.AUTHOR
    is_active: bool = True
    email_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def can_publish(self) -> bool:
        return self.role.level >= Role.EDITOR.level

    def can_manage_user(self, target: "User") -> bool:
        if self.role == Role.SUPER_ADMIN:
            return True
        if self.role == Role.ADMIN:
            return target.role != Role.SUPER_ADMIN
        return False
