from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.shared.database import Base

article_tags = Table(
    "article_tags", Base.metadata,
    Column("article_id", UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class ArticleModel(Base):
    __tablename__ = "articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    excerpt = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String(500))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    is_featured = Column(Boolean, default=False)
    reading_time_min = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    meta_title = Column(String(500))
    meta_description = Column(Text)
    published_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
    author = relationship("UserModel", back_populates="articles", foreign_keys=[author_id])
    category = relationship("CategoryModel", back_populates="articles")
    tags = relationship("TagModel", secondary=article_tags, back_populates="articles")


class CategoryModel(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, default="")
    icon = Column(String(50), default="")
    color = Column(String(7), default="#000000")
    sort_order = Column(Integer, default=0)
    created_at = Column(String)
    updated_at = Column(String)
    articles = relationship("ArticleModel", back_populates="category")


class TagModel(Base):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#000000")
    created_at = Column(String)
    articles = relationship("ArticleModel", secondary=article_tags, back_populates="tags")
