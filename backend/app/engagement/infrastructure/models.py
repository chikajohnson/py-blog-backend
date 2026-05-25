from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.shared.database import Base

class NewsletterSubscriberModel(Base):
    __tablename__ = "newsletter_subscribers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(String)
    unsubscribed_at = Column(String)
    source = Column(String(50), default="website")

class ArticleViewModel(Base):
    __tablename__ = "article_views"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    visitor_fingerprint = Column(String(64), nullable=False)
    referrer = Column(String(500), default="")
    read_duration_sec = Column(Integer, default=0)
    viewed_at = Column(String)
