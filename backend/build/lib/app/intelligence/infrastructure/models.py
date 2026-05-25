from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.shared.database import Base

class AIConversationModel(Base):
    __tablename__ = "ai_conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="New Chat")
    model = Column(String(50), default="gpt-4")
    created_at = Column(String)
    updated_at = Column(String)
    messages = relationship("AIMessageModel", back_populates="conversation", cascade="all, delete-orphan")

class AIMessageModel(Base):
    __tablename__ = "ai_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(String)
    conversation = relationship("AIConversationModel", back_populates="messages")
