from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.shared.database import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    bio = Column(Text, default="")
    github_handle = Column(String(100))
    twitter_handle = Column(String(100))
    role = Column(String(20), nullable=False, default="author")
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
    articles = relationship("ArticleModel", back_populates="author", foreign_keys="ArticleModel.author_id")
    media = relationship("MediaModel", back_populates="uploader", foreign_keys="MediaModel.uploaded_by")


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(String, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(String)


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(String, nullable=False)
    used_at = Column(String)
    created_at = Column(String)
