from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.shared.database import Base

class SettingModel(Base):
    __tablename__ = "settings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, nullable=False, default={})
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at = Column(String)

class ActivityLogModel(Base):
    __tablename__ = "activity_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    meta_data = Column("metadata", JSONB, default={})
    ip_address = Column(String(45))
    created_at = Column(String)
