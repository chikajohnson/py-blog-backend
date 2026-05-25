from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import re


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass
class Article:
    id: UUID = field(default_factory=uuid4)
    slug: str = ""
    title: str = ""
    excerpt: str = ""
    content: str = ""
    cover_image_url: str | None = None
    author_id: UUID | None = None
    category_id: UUID | None = None
    status: ArticleStatus = ArticleStatus.DRAFT
    is_featured: bool = False
    reading_time_min: int = 0
    views_count: int = 0
    meta_title: str | None = None
    meta_description: str | None = None
    published_at: datetime | None = None
    tag_ids: list[UUID] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.status == ArticleStatus.PUBLISHED

    @staticmethod
    def generate_slug(title: str) -> str:
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    @staticmethod
    def calculate_reading_time(content: str) -> int:
        return max(1, round(len(content.split()) / 200))


@dataclass
class Category:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str = ""
    icon: str = ""
    color: str = "#000000"
    sort_order: int = 0
    article_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def generate_slug(name: str) -> str:
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        return re.sub(r'-+', '-', slug).strip('-')


@dataclass
class Tag:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    color: str = "#000000"
    article_count: int = 0
    created_at: datetime | None = None

    @staticmethod
    def generate_slug(name: str) -> str:
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        return re.sub(r'-+', '-', slug).strip('-')
